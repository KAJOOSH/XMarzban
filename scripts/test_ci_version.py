"""Release gating tests; no registry writes or application startup."""
import unittest
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from scripts.ci_version import read_version, release_info

class VersionTests(unittest.TestCase):
    def test_unchanged(self):
        self.assertEqual(release_info('__version__ = "0.8.4"','__version__ = "0.8.4"')['changed'],'false')
    def test_changed(self):
        result=release_info('__version__ = "0.8.5"','__version__ = "0.8.4"')
        self.assertEqual(result,{'version':'0.8.5','previous_version':'0.8.4','changed':'true'})
    def test_initial(self):
        self.assertEqual(release_info('__version__ = "1.0.0"',None)['changed'],'true')
    def test_no_application_execution(self):
        self.assertEqual(read_version('raise RuntimeError("must not execute")\n__version__ = "1.2.3"'),'1.2.3')
    def test_invalid_version(self):
        for value in ('latest','v1.2.3','1.2','1.2.3/invalid','1.2.3+build'):
            with self.subTest(value=value), self.assertRaises(ValueError): read_version(f'__version__ = {value!r}')
    def test_prerelease(self):
        self.assertEqual(read_version('__version__ = "1.2.3-rc.1"'),'1.2.3-rc.1')

class GitEventTests(unittest.TestCase):
    def run_event(self, versions, event_name='push', zero_before=False):
        detector = Path(__file__).with_name('ci_version.py').resolve()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
            git('init', '-q')
            git('config', 'user.email', 'ci@example.invalid')
            git('config', 'user.name', 'CI fixture')
            (root/'app').mkdir()
            before = None
            for index, version in enumerate(versions):
                (root/'app/__init__.py').write_text(f'__version__ = {version!r}\n')
                (root/'change.txt').write_text(str(index))
                git('add', '.')
                git('commit', '-qm', 'fixture')
                if index == 0:
                    before = git('rev-parse', 'HEAD')
            event = root/'event.json'
            event.write_text(json.dumps({'before': '0'*40 if zero_before else before}))
            output = root/'output.txt'
            result = subprocess.run([sys.executable, str(detector)], cwd=root, env={
                **os.environ, 'GITHUB_EVENT_NAME': event_name,
                'GITHUB_EVENT_PATH': str(event), 'GITHUB_OUTPUT': str(output),
            }, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            return dict(line.split('=', 1) for line in output.read_text().splitlines())

    def test_multi_commit_push_compares_with_before_entire_push(self):
        self.assertEqual(self.run_event(['1.0.0','1.0.1','1.0.1'])['changed'], 'true')

    def test_manual_run_does_not_override_unchanged_version(self):
        self.assertEqual(self.run_event(['1.0.0','1.0.0'], 'workflow_dispatch')['changed'], 'false')

    def test_initial_push_zero_sha(self):
        self.assertEqual(self.run_event(['1.0.0'], zero_before=True)['changed'], 'true')

if __name__=='__main__': unittest.main(verbosity=2)
