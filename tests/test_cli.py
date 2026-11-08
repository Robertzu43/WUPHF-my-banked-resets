import unittest
from unittest.mock import patch
from wuphf.cli import main

class CliTests(unittest.TestCase):
    def test_mac_scheduler_launch_error_cleans_up_new_file(self):
        import tempfile
        from pathlib import Path
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plist=root/'agent.plist'
            with patch.object(cli,'PLIST',plist),patch.object(cli,'ROOT',root),patch.object(cli.sys,'platform','darwin'),patch.object(cli.os,'getuid',return_value=100,create=True),patch.object(cli.shutil,'which',return_value='/bin/codex'),patch.object(cli.subprocess,'run',side_effect=OSError('unavailable')):
                with self.assertRaises(RuntimeError):cli.install_agent()
            self.assertFalse(plist.exists())

    def test_mac_uninstall_preserves_file_if_scheduler_domain_is_unavailable(self):
        import tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            plist=Path(d)/'agent.plist';plist.write_text('existing')
            with patch.object(cli,'PLIST',plist),patch.object(cli.sys,'platform','darwin'),patch.object(cli.os,'getuid',return_value=100,create=True),patch.object(cli.subprocess,'run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):cli.main(['uninstall'])
            self.assertTrue(plist.exists())

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
    def test_mac_install_refuses_protected_source_and_frozen_paths_before_job_changes(self):
        import tempfile
        from pathlib import Path
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            home=Path(d); plist=home/'agent.plist'
            for folder,frozen in ((folder,frozen) for folder in ('Documents','Desktop','Downloads') for frozen in (False,True)):
                protected=home/folder/'WUPHF'
                with self.subTest(folder=folder,frozen=frozen),patch.object(Path,'home',return_value=home),patch.object(cli,'PLIST',plist),patch.object(cli,'ROOT',protected),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',frozen,create=True),patch.object(cli.sys,'executable',str(protected/'WUPHF')),patch.object(cli.shutil,'which',return_value='/usr/bin/codex'),patch.object(cli.subprocess,'run') as launch:
                    with self.assertRaisesRegex(RuntimeError,'Application Support'):cli.install_agent()
                    launch.assert_not_called();self.assertFalse(plist.exists())

    def test_mac_install_resolves_symlink_to_protected_source(self):
        import tempfile
        from pathlib import Path
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            home=Path(d);target=home/'Documents'/'app';target.mkdir(parents=True)
            alias=home/'app';alias.symlink_to(target,target_is_directory=True)
            with patch.object(Path,'home',return_value=home),patch.object(cli,'PLIST',home/'agent.plist'),patch.object(cli,'ROOT',alias),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',False,create=True),patch.object(cli.sys,'executable','/usr/bin/python3'),patch.object(cli.shutil,'which',return_value='/usr/bin/codex'),patch.object(cli.subprocess,'run') as launch:
                with self.assertRaises(cli.ProtectedMacLocation):cli.install_agent()
                launch.assert_not_called()

    def test_mac_install_rejects_protected_or_symlinked_codex(self):
        import tempfile
        from pathlib import Path
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            home=Path(d);codex=home/'Documents'/'bin'/'codex';codex.parent.mkdir(parents=True);codex.touch()
            alias=home/'codex';alias.symlink_to(codex)
            safe=home/'safe-codex';safe.touch();protected_alias=codex.parent/'alias';protected_alias.symlink_to(safe)
            for exe in (codex,alias,protected_alias):
                with self.subTest(exe=exe),patch.object(Path,'home',return_value=home),patch.object(cli,'PLIST',home/'agent.plist'),patch.object(cli,'ROOT',home/'safe-app'),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',False,create=True),patch.object(cli.sys,'executable','/usr/bin/python3'),patch.object(cli.shutil,'which',return_value=str(exe)),patch.object(cli.subprocess,'run') as launch:
                    with self.assertRaisesRegex(cli.ProtectedMacLocation,'Codex'):cli.install_agent()
                    launch.assert_not_called();self.assertFalse((home/'agent.plist').exists())

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
            with patch('wuphf.cli.PLIST',p),patch('wuphf.cli.ROOT',Path(d)),patch('wuphf.cli.sys.platform','darwin'),patch('wuphf.cli.os.getuid',return_value=100,create=True),patch('wuphf.cli.shutil.which',return_value='/bin/codex'),patch('wuphf.cli.subprocess.run',return_value=SimpleNamespace(returncode=1)):
                with self.assertRaises(RuntimeError):install_agent()
            self.assertFalse(p.exists())
    def test_calendar_account_errors_are_actionable_but_other_errors_are_redacted(self):
        import tempfile
        from pathlib import Path
        from wuphf.google import CalendarAccountError
        from wuphf.storage import load
        for error in (CalendarAccountError('calendar_identity_required'),RuntimeError('PRIVATE-SECRET')):
            with self.subTest(error=type(error).__name__),tempfile.TemporaryDirectory() as d:
                p=Path(d)/'state.json';snap={'count':0,'complete':True,'credits':[]}
                with patch('wuphf.cli.DATA',Path(d)),patch('wuphf.cli.STATE',p),patch('wuphf.cli.SETTINGS',Path(d)/'settings.json'),patch('wuphf.cli.read_snapshot',return_value=snap),patch('wuphf.google_auth.sync',side_effect=error),patch('builtins.print'):
                    main(['run'])
                text=load(p,{})['failures']['google']
                self.assertNotIn('PRIVATE-SECRET',text)
                if isinstance(error,CalendarAccountError):self.assertIn('stable account identity',text)

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

    def test_incomplete_background_read_reports_failure_and_preserves_last_success(self):
        import tempfile
        from pathlib import Path
        from wuphf.storage import save, load
        partial={'count':2,'complete':False,'credits':None}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'; save(p,{'last_check':100,'failures':{'ntfy':'Delivery failed'},'snapshot':None,'ledger':{}})
            save(Path(d)/'settings.json',{'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}})
            with patch('wuphf.cli.DATA',Path(d)),patch('wuphf.cli.STATE',p),patch('wuphf.cli.SETTINGS',Path(d)/'settings.json'),patch('wuphf.cli.read_snapshot',return_value=partial),patch('wuphf.google_auth.sync',return_value=False),patch('builtins.print'):
                main(['run'])
            state=load(p,{})
            self.assertEqual(state['last_check'],100)
            self.assertIn('last_error',state)
            self.assertIn('ntfy',state['failures'])

    def test_mac_frozen_agent_uses_installed_executable_and_directory(self):
        import plistlib,tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);exe=root/'Installed WUPHF'/'WUPHF';plist=root/'agent.plist'
            with patch.object(cli,'PLIST',plist),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',True,create=True),patch.object(cli.sys,'executable',str(exe)),patch.object(cli.sys,'_MEIPASS',str(root/'temporary bundle'),create=True),patch.object(cli.os,'getuid',return_value=100,create=True),patch.object(cli.shutil,'which',return_value='/usr/bin/codex'),patch.object(cli.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                cli.install_agent()
            job=plistlib.loads(plist.read_bytes())
            self.assertEqual(job['ProgramArguments'],[str(exe),'--background'])
            self.assertEqual(job['WorkingDirectory'],str(exe.parent))
            self.assertNotIn('temporary bundle',str(job))

    def test_mac_source_agent_keeps_python_module_command(self):
        import plistlib,tempfile
        from pathlib import Path
        from types import SimpleNamespace
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);plist=root/'agent.plist'
            with patch.object(cli,'PLIST',plist),patch.object(cli,'ROOT',root),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',False,create=True),patch.object(cli.sys,'executable','/usr/bin/python-example'),patch.object(cli.os,'getuid',return_value=100,create=True),patch.object(cli.shutil,'which',return_value='/usr/bin/codex'),patch.object(cli.subprocess,'run',return_value=SimpleNamespace(returncode=0)):
                cli.install_agent()
            job=plistlib.loads(plist.read_bytes())
            self.assertEqual(job['ProgramArguments'],['/usr/bin/python-example','-m','wuphf.cli','run'])
            self.assertEqual(job['WorkingDirectory'],str(root))

    def test_new_cli_setup_does_not_offer_ntfy_but_existing_users_can_disable_it(self):
        from wuphf import cli
        def exercise(channels):
            prompts=[]
            def answer(label,default=''):
                prompts.append(label)
                return 'n' if label.startswith('Enable ') else default
            with patch.object(cli,'load',return_value={'advance_days':7,'repeat_hours':24,'channels':channels}),patch.object(cli,'prompt',side_effect=answer),patch.object(cli,'save') as save:
                cli.configure()
            return prompts,save.call_args.args[1]
        prompts,_=exercise({});self.assertNotIn('Enable ntfy? (y/n)',prompts)
        prompts,settings=exercise({'ntfy':{'url':'https://example.test','topic':'legacy'}})
        self.assertIn('Enable ntfy? (y/n)',prompts);self.assertNotIn('ntfy',settings['channels'])
