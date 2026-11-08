import unittest
from wuphf.core import snapshot, compare, due

class TrackingTests(unittest.TestCase):
    def test_complete_only_with_unique_rows_matching_count(self):
        self.assertFalse(snapshot({'availableCount': 0, 'credits': None})['complete'])
        self.assertFalse(snapshot({'availableCount': 2, 'credits': [{'id':'a'}]})['complete'])
        self.assertFalse(snapshot({'availableCount': 2, 'credits': [{'id':'a'}, {'id':'a'}]})['complete'])
        self.assertTrue(snapshot({'availableCount': 0, 'credits': []})['complete'])
    def test_incomplete_read_never_indicates_a_removal(self):
        a=snapshot({'availableCount':1,'credits':[{'id':'a','expiresAt':200}]})
        b=snapshot({'availableCount':1,'credits':None})
        self.assertIsNone(compare(a,b))
    def test_complete_change_detects_new_and_removed(self):
        a=snapshot({'availableCount':1,'credits':[{'id':'a','expiresAt':200}]},'account-a')
        b=snapshot({'availableCount':1,'credits':[{'id':'b','expiresAt':300}]},'account-a')
        self.assertEqual(compare(a,b),({'b'},{'a'}))
    def test_reminders_respect_threshold_repeat_and_expiration(self):
        item={'id':'a','expiresAt':1000}
        self.assertTrue(due(item, 900, 200, 50, None))
        self.assertFalse(due(item, 900, 200, 50, 875))
        self.assertFalse(due(item, 1000, 200, 50, None))
        self.assertFalse(due({'id':'a','expiresAt':None}, 900, 200, 50, None))
        self.assertFalse(due(item, 700, 200, 50, None))
    def test_invalid_expiry_is_not_due(self):
        self.assertFalse(due({'expiresAt':float('inf')}, 900, 1000, 50, None))
        self.assertFalse(due({'expiresAt':'soon'}, 900, 1000, 50, None))

    def test_app_server_uses_resolved_codex_launcher(self):
        from unittest.mock import MagicMock, patch
        from wuphf.core import read_snapshot
        process=MagicMock()
        process.stdout=iter(['{"id":1,"result":{}}\n','{"id":2,"result":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}}\n'])
        with patch('wuphf.core.shutil.which',return_value='C:/example/codex.cmd'),patch('wuphf.core.subprocess.Popen',return_value=process) as launch:
            result=read_snapshot()
        self.assertTrue(result['complete'])
        self.assertEqual(launch.call_args.args[0],['C:/example/codex.cmd','app-server'])

    def test_snapshot_fingerprints_account_without_exposing_raw_id(self):
        import json
        from wuphf.core import snapshot
        try:a=snapshot({'availableCount':0,'credits':[]},'account-private-a')
        except TypeError:self.fail('snapshot must support optional account identity')
        b=snapshot({'availableCount':0,'credits':[]},'account-private-b')
        self.assertNotIn('account-private-a',json.dumps(a))
        self.assertNotEqual(a.get('account_fingerprint'),b.get('account_fingerprint'))
        self.assertRegex(a.get('account_fingerprint',''),r'^[0-9a-f]{64}$')
        self.assertIsNone(snapshot({'availableCount':0,'credits':[]},None).get('account_fingerprint'))

    def test_app_server_captures_identity_from_same_response(self):
        import json
        from unittest.mock import MagicMock,patch
        from wuphf.core import read_snapshot
        process=MagicMock();process.stdout=iter(['{"id":1,"result":{}}\n',json.dumps({'id':2,'result':{'accountId':'private-account','rateLimitResetCredits':{'availableCount':0,'credits':[]}}})+'\n'])
        with patch('wuphf.core.subprocess.Popen',return_value=process):result=read_snapshot()
        self.assertNotIn('private-account',json.dumps(result))
        self.assertRegex(result.get('account_fingerprint',''),r'^[0-9a-f]{64}$')
        self.assertEqual(process.stdin.write.call_count,3)

    def test_comparison_requires_same_known_identity(self):
        raw={'availableCount':0,'credits':[]}
        self.assertIsNone(compare(snapshot(raw,None),snapshot(raw,None)))
        self.assertIsNone(compare(snapshot(raw,'a'),snapshot(raw,'b')))
        self.assertIsNone(compare(snapshot(raw,'a'),snapshot(raw,None)))
        self.assertEqual(compare(snapshot(raw,'a'),snapshot(raw,'a')),(set(),set()))
        for invalid in (None,'',False,{},'   '):
            self.assertIsNone(snapshot(raw,invalid)['account_fingerprint'])

    def test_invalid_account_identifiers_do_not_become_known_identity(self):
        raw={'availableCount':0,'credits':[]}
        self.assertIsNone(snapshot(raw,'\ud800')['account_fingerprint'])
        self.assertIsNone(compare({'complete':True,'credits':[],'account_fingerprint':'not-a-hash'},
                                  {'complete':True,'credits':[],'account_fingerprint':'not-a-hash'}))

    def test_frozen_linux_restores_library_path_only_for_codex_child(self):
        import json,os,sys,tempfile
        from pathlib import Path
        from unittest.mock import MagicMock,patch
        from wuphf.core import read_snapshot
        with tempfile.TemporaryDirectory() as d:
            bundle=str(Path(d)/'bundle');other=str(Path(d)/'system')
            env={'PATH':bundle+os.pathsep+other,'LD_LIBRARY_PATH':bundle+os.pathsep+other,'LD_LIBRARY_PATH_ORIG':other}
            process=MagicMock();process.stdout=iter(['{"id":1,"result":{}}\n',json.dumps({'id':2,'result':{'rateLimitResetCredits':{'availableCount':0,'credits':[]}}})+'\n'])
            with patch.dict(os.environ,env,clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',bundle,create=True),patch.object(sys,'platform','linux'),patch('wuphf.core.shutil.which',return_value='codex') as which,patch('wuphf.core.subprocess.Popen',return_value=process) as launch:
                read_snapshot();self.assertEqual(os.environ['LD_LIBRARY_PATH'],env['LD_LIBRARY_PATH'])
            child=launch.call_args.kwargs.get('env',{})
            self.assertEqual(child.get('LD_LIBRARY_PATH'),other)
            self.assertEqual(child.get('PATH'),other)
            self.assertEqual(which.call_args.kwargs.get('path'),other)

    def test_frozen_mac_filters_bundle_only_paths_from_child(self):
        import json,os,sys,tempfile
        from pathlib import Path
        from unittest.mock import MagicMock,patch
        from wuphf.core import read_snapshot
        with tempfile.TemporaryDirectory() as d:
            bundle=str(Path(d)/'bundle');other=str(Path(d)/'system')
            env={'PATH':bundle+os.pathsep+other,'DYLD_LIBRARY_PATH':bundle+os.pathsep+other}
            process=MagicMock();process.stdout=iter(['{"id":1,"result":{}}\n',json.dumps({'id':2,'result':{'rateLimitResetCredits':{'availableCount':0,'credits':[]}}})+'\n'])
            with patch.dict(os.environ,env,clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',bundle,create=True),patch.object(sys,'platform','darwin'),patch('wuphf.core.shutil.which',return_value='codex'),patch('wuphf.core.subprocess.Popen',return_value=process) as launch:
                read_snapshot();self.assertEqual(os.environ['DYLD_LIBRARY_PATH'],env['DYLD_LIBRARY_PATH'])
            child=launch.call_args.kwargs.get('env',{})
            self.assertEqual(child.get('DYLD_LIBRARY_PATH'),other);self.assertEqual(child.get('PATH'),other)

    def test_source_mode_inherits_environment_without_changes(self):
        import json,sys
        from unittest.mock import MagicMock,patch
        from wuphf.core import read_snapshot
        process=MagicMock();process.stdout=iter(['{"id":1,"result":{}}\n',json.dumps({'id':2,'result':{'rateLimitResetCredits':{'availableCount':0,'credits':[]}}})+'\n'])
        with patch.object(sys,'frozen',False,create=True),patch('wuphf.core.shutil.which',return_value='codex'),patch('wuphf.core.subprocess.Popen',return_value=process) as launch:
            read_snapshot()
        self.assertNotIn('env',launch.call_args.kwargs)

    def test_frozen_linux_unsets_modified_library_path_when_no_original(self):
        import os,sys,tempfile
        from unittest.mock import patch
        from wuphf.core import _external_environment
        with tempfile.TemporaryDirectory() as root,patch.dict(os.environ,{'PATH':'/outside','LD_LIBRARY_PATH':root},clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',root,create=True),patch.object(sys,'platform','linux'):
            child=_external_environment()
            self.assertNotIn('LD_LIBRARY_PATH',child)
            self.assertEqual(os.environ['LD_LIBRARY_PATH'],root)

    def test_frozen_windows_filters_bundle_path_but_does_not_claim_dll_reset(self):
        import os,sys,tempfile
        from pathlib import Path
        from unittest.mock import patch
        from wuphf.core import _external_environment
        with tempfile.TemporaryDirectory() as root:
            bundle=str(Path(root)/'bundle');sibling=str(Path(root)/'bundle-other')
            with patch.dict(os.environ,{'PATH':bundle+os.pathsep+sibling},clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',bundle,create=True),patch.object(sys,'platform','win32'):
                child=_external_environment()
                self.assertEqual(child['PATH'],sibling)
                self.assertEqual(os.environ['PATH'],bundle+os.pathsep+sibling)

    def test_frozen_mac_removes_empty_bundle_only_library_path(self):
        import os,sys,tempfile
        from unittest.mock import patch
        from wuphf.core import _external_environment
        with tempfile.TemporaryDirectory() as bundle,patch.dict(os.environ,{'PATH':'/outside','DYLD_LIBRARY_PATH':bundle},clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',bundle,create=True),patch.object(sys,'platform','darwin'):
            child=_external_environment()
            self.assertNotIn('DYLD_LIBRARY_PATH',child)

    def test_frozen_child_path_falls_back_to_system_path_when_only_bundle_is_present(self):
        import os,sys,tempfile
        from unittest.mock import patch
        from wuphf.core import _external_environment
        with tempfile.TemporaryDirectory() as bundle,patch.dict(os.environ,{'PATH':bundle},clear=True),patch.object(sys,'frozen',True,create=True),patch.object(sys,'_MEIPASS',bundle,create=True),patch.object(sys,'platform','darwin'):
            self.assertEqual(_external_environment()['PATH'],os.defpath)

    def test_oversized_numeric_expiry_is_unknown(self):
        from wuphf.core import valid_expiry
        self.assertFalse(valid_expiry(10**1000))
        self.assertFalse(due({'expiresAt':10**1000},900,1000,50,None))

    def test_notifications_do_not_extend_account_response_timeout(self):
        from unittest.mock import MagicMock,patch
        from wuphf.core import read_snapshot
        process=MagicMock()
        process.stdout=iter(['{"id":1,"result":{}}\n','{"method":"progress"}\n',
            '{"id":2,"result":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}}\n'])
        with patch('wuphf.core.subprocess.Popen',return_value=process),patch('time.monotonic',side_effect=[0,0,0,0,2]):
            with self.assertRaisesRegex(RuntimeError,'timed out'):
                read_snapshot(timeout=1)
