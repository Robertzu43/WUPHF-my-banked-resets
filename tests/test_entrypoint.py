import importlib
import importlib.util
import unittest
from unittest.mock import patch

class EntrypointTests(unittest.TestCase):
    def test_mac_frozen_launch_finds_homebrew_codex_from_finder(self):
        import os
        import wuphf_launcher as launcher
        with patch.object(launcher.sys,'platform','darwin'),patch.object(launcher.sys,'frozen',True,create=True),patch.dict(os.environ,{'PATH':'/usr/bin:/bin'}),patch('wuphf.web.main') as web:
            web.side_effect=lambda:self.assertEqual(os.environ['PATH'],'/usr/bin:/bin:/opt/homebrew/bin:/usr/local/bin')
            launcher.main([])

    def test_version_reads_bundled_metadata_without_opening_ui(self):
        import tempfile
        from pathlib import Path
        from io import StringIO
        import wuphf_launcher as launcher
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'VERSION').write_text('0.1.0-beta.1\n')
            with patch.object(launcher,'__file__',str(root/'wuphf_launcher.py')),patch('sys.stdout',new_callable=StringIO) as output,patch('wuphf.web.main') as web:
                launcher.main(['--version'])
            self.assertEqual(output.getvalue(),'WUPHF 0.1.0-beta.1\n');web.assert_not_called()

    def test_windows_bundle_clears_inherited_dll_path_before_dispatch_once(self):
        import ctypes, os
        from unittest.mock import Mock
        import wuphf_launcher as launcher
        kernel=Mock(); kernel.SetDllDirectoryW.return_value=1
        directory=Mock()
        with patch.object(launcher.sys,'platform','win32'),patch.object(launcher.sys,'frozen',True,create=True),patch.object(launcher.sys,'_MEIPASS','C:/bundle',create=True),patch.object(launcher,'_dll_directory',None,create=True),patch.object(os,'add_dll_directory',return_value=directory,create=True) as add,patch.object(ctypes,'WinDLL',return_value=kernel,create=True),patch('wuphf.web.main') as web:
            def check_start():
                kernel.SetDllDirectoryW.assert_called_once_with(None)
                self.assertIs(launcher._dll_directory,directory)
            web.side_effect=check_start
            launcher.main([]);launcher.main([])
            add.assert_called_once_with('C:/bundle');directory.close.assert_not_called()

    def test_windows_dll_reset_failure_prevents_start_and_closes_handle(self):
        import ctypes, os
        from unittest.mock import Mock
        import wuphf_launcher as launcher
        kernel=Mock();kernel.SetDllDirectoryW.return_value=0
        directory=Mock()
        with patch.object(launcher.sys,'platform','win32'),patch.object(launcher.sys,'frozen',True,create=True),patch.object(launcher.sys,'_MEIPASS','C:/bundle',create=True),patch.object(launcher,'_dll_directory',None,create=True),patch.object(os,'add_dll_directory',return_value=directory,create=True),patch.object(ctypes,'WinDLL',return_value=kernel,create=True),patch('wuphf.web.main') as web:
            with self.assertRaisesRegex(RuntimeError,'DLL'):launcher.main([])
            web.assert_not_called();directory.close.assert_called_once_with()
            self.assertIsNone(launcher._dll_directory)

    def test_background_dispatch_does_not_open_ui(self):
        spec=importlib.util.find_spec('wuphf_launcher')
        self.assertIsNotNone(spec,'frozen launcher entrypoint is missing')
        launcher=importlib.import_module('wuphf_launcher')
        with patch('wuphf.cli.main') as cli,patch('wuphf.web.main') as web:
            launcher.main(['--background'])
        cli.assert_called_once_with(['run']);web.assert_not_called()

    def test_default_dispatch_opens_ui(self):
        spec=importlib.util.find_spec('wuphf_launcher')
        self.assertIsNotNone(spec,'frozen launcher entrypoint is missing')
        launcher=importlib.import_module('wuphf_launcher')
        with patch('wuphf.cli.main') as cli,patch('wuphf.web.main') as web:
            launcher.main([])
        web.assert_called_once_with();cli.assert_not_called()

    def test_unknown_arguments_do_not_open_ui_or_run_reminders(self):
        spec=importlib.util.find_spec('wuphf_launcher')
        self.assertIsNotNone(spec,'frozen launcher entrypoint is missing')
        launcher=importlib.import_module('wuphf_launcher')
        with patch('wuphf.cli.main') as cli,patch('wuphf.web.main') as web:
            with self.assertRaises(SystemExit):launcher.main(['--unknown'])
        web.assert_not_called();cli.assert_not_called()

    def test_asset_check_does_not_open_ui_or_run_reminders(self):
        from io import StringIO
        import wuphf_launcher
        with patch('wuphf.cli.main') as cli,patch('wuphf.web.main') as web,patch('sys.stdout',new_callable=StringIO) as output:
            try:wuphf_launcher.main(['--check-assets'])
            except SystemExit:self.fail('packaged asset smoke check is missing')
        self.assertIn('assets OK',output.getvalue())
        cli.assert_not_called();web.assert_not_called()

    def test_asset_check_fails_when_ui_file_is_missing(self):
        from pathlib import Path
        import wuphf_launcher
        with patch('wuphf.web.PAGE',Path('/missing-wuphf-ui-file')):
            with self.assertRaises(FileNotFoundError):wuphf_launcher.main(['--check-assets'])

    def test_codex_check_is_read_only_and_does_not_print_identity(self):
        from io import StringIO
        import wuphf_launcher
        with patch('wuphf.core.read_snapshot',return_value={'complete':True,'account_fingerprint':'private-identity','credits':[{'id':'private-credit'}]}) as read,patch('wuphf.cli.main') as cli,patch('wuphf.web.main') as web,patch('sys.stdout',new_callable=StringIO) as output:
            try:wuphf_launcher.main(['--check-codex'])
            except SystemExit:self.fail('read-only Codex check is missing')
        read.assert_called_once_with();cli.assert_not_called();web.assert_not_called()
        self.assertNotIn('private-identity',output.getvalue());self.assertNotIn('private-credit',output.getvalue())
