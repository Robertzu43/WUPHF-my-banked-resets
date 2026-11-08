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

    def test_linux_monitoring_status_distinguishes_enabled_disabled_and_unknown(self):
        with patch('wuphf.platform_jobs.sys.platform','linux'),patch('wuphf.platform_jobs.subprocess.run') as run:
            run.side_effect=[SimpleNamespace(returncode=0,stdout='enabled\n'),SimpleNamespace(returncode=0,stdout='active\n')]
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'enabled')
            run.side_effect=[SimpleNamespace(returncode=1,stdout='disabled\n')]
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'disabled')
            run.side_effect=OSError('no systemd')
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'unknown')

    def test_mac_monitoring_status_only_asserts_absence_if_domain_accessible(self):
        with patch('wuphf.platform_jobs.sys.platform','darwin'),patch('wuphf.platform_jobs.os.getuid',return_value=123,create=True),patch('wuphf.platform_jobs.subprocess.run') as run:
            run.side_effect=[SimpleNamespace(returncode=1),SimpleNamespace(returncode=0)]
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'disabled')
            run.side_effect=[SimpleNamespace(returncode=1),SimpleNamespace(returncode=1)]
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'unknown')

    def test_windows_task_status_requires_valid_scheduler_xml(self):
        xml='<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"><Settings><Enabled>true</Enabled></Settings></Task>'
        with patch('wuphf.platform_jobs.sys.platform','win32'),patch('wuphf.platform_jobs.subprocess.run') as run:
            run.return_value=SimpleNamespace(returncode=0,stdout=xml)
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'enabled')
            run.return_value=SimpleNamespace(returncode=1,stdout='')
            self.assertEqual(getattr(platform_jobs,"monitoring_status",lambda:"not implemented")(),'unknown')

    def test_linux_frozen_scheduler_uses_installed_executable_not_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);exe=root/'Installed WUPHF'/'WUPHF';units=root/'units'
            with patch.object(platform_jobs.sys,'platform','linux'),patch.object(platform_jobs.sys,'frozen',True,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs.sys,'_MEIPASS',str(root/'temporary bundle'),create=True),patch.object(platform_jobs,'UNITS',units),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                platform_jobs.install()
            service=(units/'wuphf-resets.service').read_text()
            self.assertIn('WorkingDirectory='+platform_jobs._quote(exe.parent),service)
            self.assertIn('ExecStart='+platform_jobs._quote(exe)+' "--background"',service)
            self.assertNotIn('temporary bundle',service);self.assertNotIn('start_background.py',service)

    def test_windows_frozen_scheduler_quotes_installed_executable(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'Installed WUPHF'/'WUPHF.exe'
            with patch.object(platform_jobs.sys,'platform','win32'),patch.object(platform_jobs.sys,'frozen',True,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs.sys,'_MEIPASS',str(Path(d)/'temporary bundle'),create=True),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
                platform_jobs.install()
            args=run.call_args.args[0];command=args[args.index('/TR')+1]
            self.assertEqual(command,subprocess.list2cmdline([str(exe),'--background']))
            self.assertNotIn('temporary bundle',command);self.assertNotIn('start_background.py',command)

    def test_linux_source_scheduler_keeps_python_script_and_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'Source WUPHF';units=Path(d)/'units';exe=Path(d)/'Python Env'/'python'
            with patch.object(platform_jobs.sys,'platform','linux'),patch.object(platform_jobs.sys,'frozen',False,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs,'ROOT',root),patch.object(platform_jobs,'UNITS',units),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                platform_jobs.install()
            service=(units/'wuphf-resets.service').read_text()
            self.assertIn('WorkingDirectory='+platform_jobs._quote(root),service)
            self.assertIn('ExecStart='+platform_jobs._quote(exe)+' '+platform_jobs._quote(root/'start_background.py'),service)

    def test_windows_source_scheduler_keeps_python_script_with_spaces(self):
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'Source WUPHF';exe=Path(d)/'Python Env'/'python.exe'
            with patch.object(platform_jobs.sys,'platform','win32'),patch.object(platform_jobs.sys,'frozen',False,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs,'ROOT',root),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
                platform_jobs.install()
            args=run.call_args.args[0]
            self.assertEqual(args[args.index('/TR')+1],subprocess.list2cmdline([str(exe),str(root/'start_background.py')]))

    def test_linux_source_scheduler_escapes_dollar_in_exec_arguments_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'Source ${USER} 10%';units=Path(d)/'units';exe=Path(d)/'Python ${HOME}'/'python'
            with patch.object(platform_jobs.sys,'platform','linux'),patch.object(platform_jobs.sys,'frozen',False,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs,'ROOT',root),patch.object(platform_jobs,'UNITS',units),patch.dict(platform_jobs.os.environ,{'PATH':'/literal/${PATH}'}),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                platform_jobs.install()
            service=(units/'wuphf-resets.service').read_text()
            self.assertIn('WorkingDirectory='+platform_jobs._quote(root)+'\n',service)
            self.assertIn('Environment='+platform_jobs._quote('PATH=/literal/${PATH}')+'\n',service)
            self.assertIn('ExecStart=:'+platform_jobs._quote(exe)+' '+platform_jobs._quote(root/'start_background.py'),service)

    def test_linux_frozen_scheduler_escapes_dollar_in_exec_arguments_only(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'Installed ${USER}'/'WUPHF';units=Path(d)/'units'
            with patch.object(platform_jobs.sys,'platform','linux'),patch.object(platform_jobs.sys,'frozen',True,create=True),patch.object(platform_jobs.sys,'executable',str(exe)),patch.object(platform_jobs,'UNITS',units),patch.object(platform_jobs.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                platform_jobs.install()
            service=(units/'wuphf-resets.service').read_text()
            self.assertIn('WorkingDirectory='+platform_jobs._quote(exe.parent)+'\n',service)
            self.assertIn('ExecStart=:'+platform_jobs._quote(exe)+' "--background"',service)
