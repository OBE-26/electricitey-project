"""Check the actual JavaScript sent to Streamlit, including course extensions."""
import ast
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class FrontendSyntaxTest(unittest.TestCase):
    def test_combined_frontend_syntax_and_bootstrap(self):
        tree = ast.parse((ROOT / "Electricity-circuit.py").read_text())
        html = next(ast.literal_eval(n.value) for n in tree.body
                    if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", "") == "APP_HTML" for t in n.targets))
        self.assertEqual(html.count("/* COURSE_EXTENSION */"), 1)
        self.assertEqual(html.count("CourseApp.initialize();"), 1)
        extension = "\n".join((ROOT / name).read_text()
                              for name in ("course_practice.js", "courses.js"))
        html = html.replace("/* COURSE_EXTENSION */", extension)
        with tempfile.TemporaryDirectory() as directory:
            for i, script in enumerate(re.findall(r"<script>(.*?)</script>", html, re.S)):
                path = Path(directory) / f"script-{i}.js"
                path.write_text(script)
                result = subprocess.run(["node", "--check", str(path)],
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
