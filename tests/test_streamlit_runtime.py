"""Exercise the actual Streamlit factory with an obsolete imported backend."""
import ast
import hashlib
import json
import os
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class ObsoleteService:
    def __init__(self, *args):
        pass

    def handle(self, *args):
        return {"ok": True, "token": "old-token", "config": {}}


class StreamlitRuntimeTest(unittest.TestCase):
    def test_deployed_source_replaces_stale_imported_classes(self):
        tree = ast.parse((ROOT / "Electricity-circuit.py").read_text())
        factory = next(node for node in tree.body
                       if isinstance(node, ast.FunctionDef)
                       and node.name == "shared_course_service")
        factory.decorator_list = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/questions.json").write_text(json.dumps({"exams": []}))
            backend = root / "course_backend.py"
            current = (ROOT / "course_backend.py").read_bytes()
            backend.write_bytes(current)
            namespace = {"asset_root": root, "hashlib": hashlib, "types": types,
                         "CourseService": ObsoleteService, "ConfigStore": lambda **kwargs: None}
            exec(compile(ast.Module(body=[factory], type_ignores=[]), str(ROOT / "Electricity-circuit.py"), "exec"), namespace)
            create = namespace["shared_course_service"]
            with patch.dict(os.environ, {"DC_COURSE_CONFIG_PATH": str(root / "admin.json")}):
                service = create("", "", "test-admin", "bank", hashlib.sha256(current).hexdigest())
                session = {}
                reply = service.handle({"action": "admin_login", "password": "test-admin"}, session)
                self.assertTrue(reply["ok"])
                self.assertTrue(reply.get("capabilities", {}).get("qa_theory"),
                                "QA must use the deployed backend even if Python retains an older imported class")
                self.assertTrue(reply["capabilities"]["password_management"])
                self.assertFalse(service.handle({"action": "admin_login", "password": "wrong"}, {})["ok"])
                # A second deployment must load its own code without a process restart.
                changed = current.replace(b'"qa_theory": True', b'"qa_theory": False')
                self.assertNotEqual(changed, current)
                backend.write_bytes(changed)
                updated = create("", "", "test-admin", "bank", hashlib.sha256(changed).hexdigest())
                self.assertFalse(updated.handle({"action": "admin_login", "password": "test-admin"}, {})["capabilities"]["qa_theory"])
                self.assertTrue(service.handle({"action": "admin_login", "password": "test-admin"}, {})["capabilities"]["qa_theory"],
                                "An existing service keeps its own module globals during a deployment")


if __name__ == "__main__":
    unittest.main()
