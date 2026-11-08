import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


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


@unittest.skipUnless(os.name!='nt', 'packaged shell launcher requires POSIX')
class PackagedLauncherTests(unittest.TestCase):
    def make_package(self, root, platform):
        from scripts import build_package
        package=root/'WUPHF folder $cash; apostrophe\' "quote" %percent'
        package.mkdir();(package/'_internal').mkdir()
        executable=package/'WUPHF'
        executable.write_text('#!/bin/sh\n[ "$PWD" = "$(dirname "$0")" ] || exit 41\nprintf "%s\\n" "$@"\n')
        executable.chmod(0o755)
        with patch('scripts.build_package.sys.platform',platform):build_package.copy_package_files(package)
        return package

    def test_packaged_launchers_follow_relocation_preserve_arguments_and_repeat(self):
        for platform,name in [('darwin','Start WUPHF.command'),('linux','Start WUPHF.sh')]:
            with self.subTest(platform=platform), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);package=self.make_package(root,platform)
                destination=root/'new location';destination.mkdir()
                package=package.rename(destination/package.name)
                launcher=package/name
                self.assertTrue(os.access(launcher,os.X_OK))
                for _ in range(2):
                    result=subprocess.run([str(launcher),'--check-assets','a b;$HOME'],cwd=root,text=True,capture_output=True,timeout=5)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertEqual(result.stdout,'--check-assets\na b;$HOME\n')

    def test_missing_bundle_members_fail_with_recovery_instructions(self):
        for missing in ['WUPHF','_internal']:
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as tmp:
                package=self.make_package(Path(tmp),'darwin')
                member=package/missing
                member.rmdir() if member.is_dir() else member.unlink()
                result=subprocess.run([str(package/'Start WUPHF.command')],text=True,capture_output=True,timeout=5)
                self.assertNotEqual(result.returncode,0)
                self.assertIn('whole WUPHF folder',result.stderr)
                self.assertIn('Extract',result.stderr)

    def test_nonexecutable_binary_reports_extract_and_permission_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            package=self.make_package(Path(tmp),'linux');(package/'WUPHF').chmod(0o644)
            result=subprocess.run([str(package/'Start WUPHF.sh')],text=True,capture_output=True,timeout=5)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('executable',result.stderr)
            self.assertIn('tar',result.stderr)
