import importlib
import importlib.util
import unittest
from unittest.mock import patch

class EntrypointTests(unittest.TestCase):
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
