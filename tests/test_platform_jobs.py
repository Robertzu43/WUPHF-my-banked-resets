import tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from wuphf import platform_jobs

class PlatformJobsTests(unittest.TestCase):
    def test_linux_installs_a_user_timer_without_overwriting_existing_units(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch('wuphf.platform_jobs.sys.platform','linux'), patch('wuphf.platform_jobs.UNITS',root), patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
                platform_jobs.install()
                self.assertTrue((root/'wuphf-resets.timer').exists())
                self.assertTrue((root/'wuphf-resets.service').exists())
                self.assertIn('OnUnitActiveSec=10min',(root/'wuphf-resets.timer').read_text())
                self.assertTrue(any('enable' in call.args[0] for call in run.call_args_list))
                with self.assertRaises(RuntimeError):platform_jobs.install()
    def test_linux_failed_activation_cleans_up_created_units(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch('wuphf.platform_jobs.sys.platform','linux'),patch('wuphf.platform_jobs.UNITS',root),patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):platform_jobs.install()
            self.assertFalse(list(root.iterdir()))
    def test_windows_creates_a_ten_minute_interactive_task(self):
        with patch('wuphf.platform_jobs.sys.platform','win32'),patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=0)) as run:
            platform_jobs.install()
        args=run.call_args.args[0]
        self.assertIn('/create',[x.lower() for x in args])
        self.assertIn('/it',[x.lower() for x in args])
        self.assertIn('10',args)
        self.assertIn('start_background.py',args[args.index('/TR')+1])
    def test_windows_task_failure_is_not_silently_ignored(self):
        with patch('wuphf.platform_jobs.sys.platform','win32'),patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=1)):
            with self.assertRaises(RuntimeError):platform_jobs.install()
    def test_cli_delegates_windows_install_and_uninstall(self):
        from wuphf import cli
        with patch('wuphf.cli.sys.platform','win32'),patch('wuphf.cli.shutil.which',return_value='codex.cmd'),patch('wuphf.platform_jobs.install') as install,patch('wuphf.platform_jobs.uninstall') as uninstall:
            cli.install_agent()
            cli.main(['uninstall'])
        install.assert_called_once_with()
        uninstall.assert_called_once_with()
    def test_linux_uninstall_removes_only_its_own_units(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('wuphf-resets.service','wuphf-resets.timer','other.timer'):(root/name).write_text('x')
            with patch('wuphf.platform_jobs.sys.platform','linux'),patch('wuphf.platform_jobs.UNITS',root),patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=0)):
                platform_jobs.uninstall()
            self.assertEqual(sorted(p.name for p in root.iterdir()),['other.timer'])
    def test_failed_linux_uninstall_preserves_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'wuphf-resets.timer').write_text('x')
            with patch('wuphf.platform_jobs.sys.platform','linux'),patch('wuphf.platform_jobs.UNITS',root),patch('wuphf.platform_jobs.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):platform_jobs.uninstall()
            self.assertTrue((root/'wuphf-resets.timer').exists())
    def test_unit_argument_escapes_special_characters(self):
        self.assertEqual(platform_jobs._quote('a %b "c"'), '"a %%b \\"c\\""')
        with self.assertRaises(RuntimeError):platform_jobs._quote('a\nb')
