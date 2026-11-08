import os
import subprocess
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(os.name!='nt' and Path('/bin/bash').exists(),'bash launcher requires a POSIX system')
class MacLauncherTests(unittest.TestCase):
    def run_launcher(self, supported):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); launcher=root/'Start WUPHF.command'
            source=Path('Start WUPHF.command').read_text()
            self.assertIn('export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"',source)
            source=source.replace('export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"','export PATH="$PATH"')
            launcher.write_text(source);launcher.chmod(0o755)
            (root/'codex').write_text('#!/bin/sh\nexit 0\n');(root/'codex').chmod(0o755)
            (root/'python3').write_text('#!/bin/sh\nif [ "$1" = "-c" ]; then exit '+('0' if supported else '1')+'; fi\necho WUPHF_STARTED\n');(root/'python3').chmod(0o755)
            return subprocess.run(['/bin/bash',str(launcher)],input='\n',text=True,capture_output=True,env={**os.environ,'PATH':str(root)+':/usr/bin:/bin'},timeout=5)

    def test_old_python_does_not_start_application(self):
        result=self.run_launcher(False)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('3.11',result.stdout)
        self.assertNotIn('WUPHF_STARTED',result.stdout)

    def test_supported_python_starts_application(self):
        result=self.run_launcher(True)
        self.assertEqual(result.returncode,0)
        self.assertIn('WUPHF_STARTED',result.stdout)
