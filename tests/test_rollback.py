"""Exercise the actual restore pathspec in an isolated Git repository."""
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class RollbackTest(unittest.TestCase):
    def test_restore_app_preserves_infrastructure_and_history(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            def git(*args):
                return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True).stdout.strip()
            def write(name,text):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
            git('init');git('config','user.name','test');git('config','user.email','test@example.invalid')
            write('app.py','stable');git('add','.');git('commit','-m','stable');stable=git('rev-parse','HEAD')
            write('app.py','new');write('learning_tools.js','new feature')
            write('.github/workflows/checks.yml','retained checks');write('data/shabbat_jerusalem.json','retained dates')
            write('scripts/update_shabbat_schedule.py','retained refresh');write('ROLLBACK_HE.md','retained instructions')
            git('add','.');git('commit','-m','new');head=git('rev-parse','HEAD')
            line=next(line.strip()[5:] for line in (ROOT/'.github/workflows/restore-stable.yml').read_text().splitlines() if line.strip().startswith('run: git restore'))
            args=shlex.split(line);args=[('--source='+stable) if value.startswith('--source=') else value for value in args]
            git(*args[1:])
            self.assertEqual((root/'app.py').read_text(),'stable')
            self.assertFalse((root/'learning_tools.js').exists())
            self.assertEqual((root/'.github/workflows/checks.yml').read_text(),'retained checks')
            self.assertEqual((root/'data/shabbat_jerusalem.json').read_text(),'retained dates')
            self.assertEqual(git('rev-parse','HEAD'),head,'Restore prepares a new commit instead of rewriting history')
