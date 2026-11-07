import unittest
from wuphf.google import reconcile

class FakeCalendar:
    def __init__(self):self.events={};self.calls=[]
    def put(self,event_id,expiry):self.events[event_id]=expiry;self.calls.append(('put',event_id,expiry))
    def delete(self,event_id):self.events.pop(event_id,None);self.calls.append(('delete',event_id))

class CalendarTests(unittest.TestCase):
    def test_create_update_preserves_old_events_when_account_changes(self):
        api=FakeCalendar();api.events['unrelated']=123;mapping={}
        a={'count':1,'complete':True,'credits':[{'id':'private-a','status':'available','expiresAt':2000}]}
        mapping=reconcile(a,mapping,api)
        self.assertEqual(len(api.events),2)
        event=next(x for x in api.events if x!='unrelated')
        self.assertNotIn('private-a',event)
        a['credits'][0]['expiresAt']=3000
        mapping=reconcile(a,mapping,api);self.assertEqual(api.events[event],3000)
        mapping=reconcile({'count':0,'complete':True,'credits':[]},mapping,api)
        self.assertEqual(api.events,{'unrelated':123,event:3000})
        self.assertIn('private-a',mapping)
    def test_incomplete_read_never_removes_or_changes_events(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        result=reconcile({'count':2,'complete':False,'credits':None},mapping,api)
        self.assertEqual(result,mapping);self.assertEqual(api.calls,[])
    def test_unknown_expiry_keeps_existing_event(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        result=reconcile({'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':None}]},mapping,api)
        self.assertEqual(result,mapping);self.assertEqual(api.calls,[])
    def test_restart_can_recreate_deleted_event(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        s={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':2000}]}
        reconcile(s,mapping,api);self.assertEqual(api.events['abc'],2000)
    def test_only_desktop_client_credentials_are_accepted(self):
        from wuphf.google_auth import parse_client
        good={'installed':{'client_id':'a.apps.googleusercontent.com','client_secret':'abc'}}
        self.assertEqual(parse_client(good),('a.apps.googleusercontent.com','abc'))
        with self.assertRaises(ValueError):parse_client({'web':good['installed']})
        with self.assertRaises(ValueError):parse_client({'installed':{'client_id':'x'}})
    def test_google_error_does_not_expose_refresh_secret(self):
        from unittest.mock import patch
        from wuphf.google import token_request
        with patch('wuphf.google.urllib.request.urlopen',side_effect=OSError('secret')):
            try:token_request({'refresh_token':'secret'})
            except RuntimeError as exc:self.assertIsNone(exc.__cause__);self.assertNotIn('secret',str(exc))
            else:self.fail('expected error')
    def test_incomplete_snapshot_does_not_create_calendar(self):
        from unittest.mock import patch
        from wuphf.google_auth import sync
        with patch('wuphf.google_auth.token_request') as refresh, patch('wuphf.google_auth.load',return_value={'client_id':'id'}), patch('wuphf.google_auth.get_secret',return_value='secret'):
            self.assertFalse(sync({'count':1,'complete':False,'credits':None}))
            refresh.assert_not_called()
    def test_event_id_obeys_google_base32hex_alphabet(self):
        import re
        from wuphf.google import event_id
        self.assertRegex(event_id('private-credit'), r'^[a-v0-9]{5,1024}$')
    def test_deleted_google_event_is_idempotent(self):
        from unittest.mock import patch
        from urllib.error import HTTPError
        from io import BytesIO
        from wuphf.google import GoogleCalendar
        error=HTTPError('https://example.test',410,'gone',{},BytesIO())
        with patch('wuphf.google.urllib.request.urlopen',side_effect=error):
            GoogleCalendar('token','calendar').delete('event')
        error.close()
    def test_cancelled_event_is_explicitly_restored(self):
        from unittest.mock import patch
        from wuphf.google import GoogleCalendar
        api=GoogleCalendar('token','calendar')
        with patch.object(api,'request',side_effect=[{'status':'cancelled'},{'id':'abc'}]) as req:
            api.put('abc',2000)
            self.assertEqual(req.call_args.args[2]['status'],'confirmed')
    def test_disconnect_removes_only_local_connection_and_preserves_remote_calendar(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from wuphf.google_auth import disconnect
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'mapping.json'
            config.write_text('{}');mapping.write_text('{}')
            with patch('wuphf.google_auth.GOOGLE',config),patch('wuphf.google_auth.MAPPING',mapping),patch('wuphf.google_auth.delete_secret') as delete:
                disconnect()
            self.assertFalse(config.exists());self.assertFalse(mapping.exists());self.assertEqual(delete.call_count,2)
    def test_installed_client_allows_direct_connect_without_file(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from wuphf.google_auth import start_connect
        client={'installed':{'client_id':'a.apps.googleusercontent.com','client_secret':'abc'}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'client.json';p.write_text(json.dumps(client))
            with patch('wuphf.google_auth.BUNDLED_CLIENT',p),patch('wuphf.google_auth.load',side_effect=lambda path,default: json.loads(p.read_text()) if path==p else {}),patch('wuphf.google_auth.threading.Thread') as thread:
                from wuphf import google_auth
                google_auth.status.update(state='disconnected',message='Not connected')
                start_connect({})
                self.assertTrue(thread.called)
                google_auth.status.update(state='disconnected',message='Not connected')
