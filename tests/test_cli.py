import unittest
from unittest.mock import patch
from wuphf.cli import main

class CliTests(unittest.TestCase):
    def test_status_displays_available_count_without_raw_credit_id(self):
        snap={'count':1,'complete':True,'credits':[{'id':'sensitive-id','status':'available','expiresAt':None}]}
        with patch('wuphf.cli.read_snapshot',return_value=snap), patch('builtins.print') as output:
            main(['status'])
            text=' '.join(str(call) for call in output.call_args_list)
            self.assertIn('1',text)
            self.assertNotIn('sensitive-id',text)
    def test_a_locked_secret_only_breaks_its_own_channel(self):
        from wuphf.cli import send_with_secrets
        def lookup(key):
            if key=='telegram.token': raise OSError('keychain locked')
            return None
        with patch('wuphf.cli.get_secret',side_effect=lookup), patch('wuphf.cli.send') as sender:
            with self.assertRaises(OSError):send_with_secrets('telegram',{},'message')
            send_with_secrets('ntfy',{'url':'https://ntfy.sh','topic':'abc'},'message')
            self.assertEqual(sender.call_count,1)
    def test_install_will_not_overwrite_existing_job(self):
        from pathlib import Path
        import tempfile
        from wuphf.cli import install_agent
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'com.wuphf.resets.plist';p.write_text('existing')
            with patch('wuphf.cli.PLIST',p),patch('wuphf.cli.sys.platform','darwin'),patch('wuphf.cli.shutil.which',return_value='/bin/codex'),patch('wuphf.cli.subprocess.run'):
                with self.assertRaises(RuntimeError): install_agent()
            self.assertEqual(p.read_text(),'existing')
    def test_failed_background_check_records_failure(self):
        import tempfile
        from pathlib import Path
        from wuphf.storage import load
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            with patch('wuphf.cli.DATA',Path(d)),patch('wuphf.cli.STATE',p),patch('wuphf.cli.SETTINGS',Path(d)/'settings.json'),patch('wuphf.cli.read_snapshot',side_effect=RuntimeError('offline')):
                with self.assertRaises(RuntimeError):main(['run'])
            self.assertIn('last_error',load(p,{}))
    def test_status_warns_about_last_background_failure(self):
        import tempfile
        from pathlib import Path
        from wuphf.storage import save
        snap={'count':0,'complete':True,'credits':[]}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';save(p,{'last_error':'Codex check failed'})
            with patch('wuphf.cli.STATE',p),patch('wuphf.cli.read_snapshot',return_value=snap),patch('builtins.print') as output:
                main(['status'])
            self.assertIn('Codex check failed', ' '.join(str(x) for x in output.call_args_list))
    def test_failed_install_cleans_up_new_job_file(self):
        from pathlib import Path
        from types import SimpleNamespace
        import tempfile
        from wuphf.cli import install_agent
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'agent.plist'
            with patch('wuphf.cli.PLIST',p),patch('wuphf.cli.sys.platform','darwin'),patch('wuphf.cli.os.getuid',return_value=100,create=True),patch('wuphf.cli.shutil.which',return_value='/bin/codex'),patch('wuphf.cli.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):install_agent()
            self.assertFalse(p.exists())
    def test_google_sync_failure_is_recorded_after_successful_read(self):
        import tempfile
        from pathlib import Path
        from wuphf.storage import load
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';snap={'count':0,'complete':True,'credits':[]}
            with patch('wuphf.cli.DATA',Path(d)),patch('wuphf.cli.STATE',p),patch('wuphf.cli.SETTINGS',Path(d)/'settings.json'),patch('wuphf.cli.read_snapshot',return_value=snap),patch('wuphf.google_auth.sync',side_effect=RuntimeError('failure')),patch('builtins.print'):
                main(['run'])
            self.assertIn('google',load(p,{})['failures'])
    def test_uninstall_keeps_agent_file_if_bootout_fails(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'agent.plist';p.write_text('agent')
            with patch('wuphf.cli.PLIST',p),patch('wuphf.cli.sys.platform','darwin'),patch('wuphf.cli.os.getuid',return_value=100,create=True),patch('wuphf.cli.subprocess.run',side_effect=[SimpleNamespace(returncode=1),SimpleNamespace(returncode=0)]):
                with self.assertRaises(RuntimeError):main(['uninstall'])
            self.assertTrue(p.exists())
    def test_failure_in_reminder_engine_records_redacted_background_error(self):
        import tempfile
        from pathlib import Path
        from wuphf.storage import load
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json';snap={'count':0,'complete':True,'credits':[]}
            with patch('wuphf.cli.DATA',Path(d)),patch('wuphf.cli.STATE',p),patch('wuphf.cli.SETTINGS',Path(d)/'settings.json'),patch('wuphf.cli.read_snapshot',return_value=snap),patch('wuphf.cli.check',side_effect=ValueError('secret recipient@example.com')):
                with self.assertRaises(RuntimeError) as error:main(['run'])
            state=load(p,{})
            self.assertIn('last_error',state)
            self.assertNotIn('secret',str(state))
            self.assertNotIn('secret',str(error.exception))
    def test_export_rejects_incomplete_snapshot_without_creating_file(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'export.ics'
            with patch('wuphf.cli.read_snapshot',return_value={'count':2,'credits':None,'complete':False}):
                with self.assertRaisesRegex(ValueError,'incomplete'):
                    main(['export',str(p)])
            self.assertFalse(p.exists())

    def test_gmail_delivery_uses_saved_recipient_and_language(self):
        from wuphf.cli import send_with_secrets
        with patch('wuphf.gmail_auth.send') as sender:
            send_with_secrets('gmail',{'to':'person@example.com','language':'es'},'hello')
        sender.assert_called_once_with('person@example.com','person@example.com','hello','es')
