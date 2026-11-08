import importlib
import importlib.util
import unittest
from unittest.mock import patch

class EntrypointTests(unittest.TestCase):
    def test_mac_frozen_launch_sets_os_trust_before_importing_web(self):
        import builtins, os
        import wuphf_launcher as launcher
        original_import=builtins.__import__
        def check_import(name,*args,**kwargs):
            if name=='wuphf.web':
                self.assertEqual(os.environ.get('SSL_CERT_FILE'),'/etc/ssl/cert.pem')
                self.assertNotIn('SSL_CERT_DIR',os.environ)
            return original_import(name,*args,**kwargs)
        with patch('wuphf.web.main'),patch.object(launcher.sys,'platform','darwin'),patch.object(launcher.sys,'frozen',True,create=True),patch.dict(os.environ,{},clear=True),patch.object(launcher.Path,'is_file',return_value=True),patch('builtins.__import__',side_effect=check_import):
            launcher.main([])
            self.assertEqual(os.environ['SSL_CERT_FILE'],'/etc/ssl/cert.pem')

    def test_mac_frozen_launch_without_os_ca_file_keeps_trust_environment_unset(self):
        import os
        import wuphf_launcher as launcher
        with patch('wuphf.web.main'),patch.object(launcher.sys,'platform','darwin'),patch.object(launcher.sys,'frozen',True,create=True),patch.dict(os.environ,{},clear=True),patch.object(launcher.Path,'is_file',return_value=False):
            launcher.main([])
            self.assertNotIn('SSL_CERT_FILE',os.environ)
            self.assertNotIn('SSL_CERT_DIR',os.environ)

    def test_mac_frozen_launch_preserves_explicit_trust_including_empty_values(self):
        import os
        import wuphf_launcher as launcher
        for overrides in ({'SSL_CERT_FILE':'/custom/ca.pem'},{'SSL_CERT_DIR':'/custom/certs'},{'SSL_CERT_FILE':''},{'SSL_CERT_DIR':''},{'SSL_CERT_FILE':'/custom/ca.pem','SSL_CERT_DIR':'/custom/certs'}):
            with self.subTest(overrides=overrides),patch('wuphf.web.main'),patch.object(launcher.sys,'platform','darwin'),patch.object(launcher.sys,'frozen',True,create=True),patch.dict(os.environ,overrides,clear=True),patch.object(launcher.Path,'is_file',return_value=True):
                launcher.main([])
                self.assertEqual({key:value for key,value in os.environ.items() if key in ('SSL_CERT_FILE','SSL_CERT_DIR')},overrides)

    def test_source_and_non_mac_launches_keep_trust_environment_unset(self):
        import os
        import wuphf_launcher as launcher
        for platform,frozen in (('darwin',False),('linux',False),('linux',True),('win32',False),('win32',True)):
            with self.subTest(platform=platform,frozen=frozen),patch('wuphf.web.main'),patch.object(launcher,'_prepare_windows_dlls'),patch.object(launcher.sys,'platform',platform),patch.object(launcher.sys,'frozen',frozen,create=True),patch.dict(os.environ,{},clear=True),patch.object(launcher.Path,'is_file',return_value=True):
                launcher.main([])
                self.assertNotIn('SSL_CERT_FILE',os.environ)
                self.assertNotIn('SSL_CERT_DIR',os.environ)

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

    def test_asset_check_requires_public_client_even_when_personal_override_exists(self):
        import json, os, tempfile
        from pathlib import Path
        import wuphf_launcher as launcher
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);personal=root/'google-client.json'
            personal.write_text(json.dumps({'installed':{'client_id':'own.apps.googleusercontent.com','client_secret':'public-parameter'}}))
            for frozen in (False,True):
                with self.subTest(frozen=frozen),patch.object(launcher.sys,'frozen',frozen,create=True),patch.object(launcher,'_prepare_windows_dlls'),patch.dict(os.environ),patch('wuphf.google_auth.PUBLIC_CLIENT',root/'missing-public.json'),patch('wuphf.google_auth.BUNDLED_CLIENT',personal):
                    with self.assertRaises(ValueError):launcher.main(['--check-assets'])

    def test_asset_check_parses_public_client_registration(self):
        import json, tempfile
        from pathlib import Path
        import wuphf_launcher as launcher
        with tempfile.TemporaryDirectory() as tmp:
            public=Path(tmp)/'oauth-client.json'
            for raw in ({'installed':{}},{'installed':{'client_id':'invalid','client_secret':'value'}}):
                public.write_text(json.dumps(raw))
                with self.subTest(raw=raw),patch('wuphf.google_auth.PUBLIC_CLIENT',public):
                    with self.assertRaises(ValueError):launcher.main(['--check-assets'])

    def test_asset_check_needs_no_personal_client_override(self):
        import json, tempfile
        from io import StringIO
        from pathlib import Path
        import wuphf_launcher as launcher
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public=root/'oauth-client.json'
            public.write_text(json.dumps({'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'public-parameter'}}))
            with patch('wuphf.google_auth.PUBLIC_CLIENT',public),patch('wuphf.google_auth.BUNDLED_CLIENT',root/'missing-personal.json'),patch('wuphf.google_auth.default_client',side_effect=AssertionError('Asset check must use PUBLIC_CLIENT')),patch('sys.stdout',new_callable=StringIO) as output:
                launcher.main(['--check-assets'])
            self.assertIn('assets OK',output.getvalue())

    def test_install_dispatch_rejects_source_without_opening_setup_or_running_reminders(self):
        import wuphf_launcher as launcher
        with patch.object(launcher.sys,'frozen',False,create=True),patch('wuphf.web.main') as web,patch('wuphf.cli.main') as cli:
            with self.assertRaisesRegex(SystemExit,'frozen.*source'):
                launcher.main(['--install'])
        web.assert_not_called();cli.assert_not_called()
