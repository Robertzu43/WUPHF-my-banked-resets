import unittest
from wuphf.google import reconcile

class FakeCalendar:
    def __init__(self):self.events={};self.calls=[]
    def put(self,event_id,expiry):self.events[event_id]=expiry;self.calls.append(('put',event_id,expiry))
    def delete(self,event_id):self.events.pop(event_id,None);self.calls.append(('delete',event_id))

class CalendarTests(unittest.TestCase):
    def test_reconcile_refuses_cross_account_and_unknown_ownership_before_writes(self):
        from wuphf.google import CalendarAccountError
        for identity in ('b'*64,None):
            with self.subTest(identity=identity):
                api=FakeCalendar();api.events['owned-by-a']=2000
                snap={'complete':True,'account_fingerprint':identity,'credits':[{'id':'same','expiresAt':3000}]}
                with self.assertRaises(CalendarAccountError):
                    reconcile(snap,{'same':{'event_id':'owned-by-a'}},api,account_fingerprint='a'*64)
                self.assertEqual(api.events,{'owned-by-a':2000});self.assertEqual(api.calls,[])

    def test_sync_binds_stable_account_and_refuses_legacy_or_changed_account(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from wuphf import google_auth
        from wuphf.google import CalendarAccountError
        from wuphf.storage import save,load
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json'
            snap={'complete':True,'count':0,'credits':[],'account_fingerprint':'a'*64}
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake'),patch.object(google_auth,'token_request',return_value={'access_token':'fake'}) as token,patch.object(google_auth,'create_calendar',return_value='new-calendar') as create:
                save(config,{'client_id':'public'})
                self.assertTrue(google_auth.sync(snap))
                self.assertEqual(load(config,{})['account_fingerprint'],'a'*64)
                create.assert_called_once()
                for data in ({'client_id':'public','calendar_id':'legacy'}, {'client_id':'public','calendar_id':'old','account_fingerprint':'b'*64}):
                    save(config,data);token.reset_mock()
                    with self.assertRaisesRegex(CalendarAccountError,'Reconnect'):
                        google_auth.sync(snap)
                    token.assert_not_called();self.assertEqual(load(config,{}),data)
                save(config,{'client_id':'public'});save(mapping,{'same':{'event_id':'legacy'}})
                with self.assertRaises(CalendarAccountError):google_auth.sync(snap)

    def test_zero_reset_sync_requires_identity_and_failed_first_binding_is_retryable(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from wuphf import google_auth
        from wuphf.google import CalendarAccountError
        from wuphf.storage import save,load
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json'
            snap={'complete':True,'count':0,'credits':[],'account_fingerprint':None}
            save(config,{'client_id':'public'})
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake'),patch.object(google_auth,'token_request',return_value={'access_token':'fake'}) as token,patch.object(google_auth,'create_calendar',return_value='new-calendar') as create:
                with self.assertRaisesRegex(CalendarAccountError,'Codex'):
                    google_auth.sync(snap)
                token.assert_not_called();create.assert_not_called()
                snap['account_fingerprint']='a'*64
                with patch.object(google_auth,'save',side_effect=OSError('disk full')):
                    with self.assertRaises(OSError):google_auth.sync(snap)
                create.assert_not_called();self.assertNotIn('account_fingerprint',load(config,{}))
                self.assertTrue(google_auth.sync(snap));create.assert_called_once()

    def test_refresh_failure_preserves_binding_and_mapping_for_restart_recovery(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from wuphf import google_auth
        from wuphf.storage import save,load
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json'
            saved={'client_id':'public','calendar_id':'owned','account_fingerprint':'a'*64}
            history={'same':{'event_id':'owned-event','expiresAt':2000}}
            save(config,saved);save(mapping,history)
            snap={'complete':True,'count':1,'credits':[{'id':'same','expiresAt':3000}],'account_fingerprint':'a'*64}
            api=FakeCalendar();api.events['unrelated']=123
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake'),patch.object(google_auth,'token_request',side_effect=[RuntimeError('offline'),{'access_token':'fake'}]),patch.object(google_auth,'GoogleCalendar',return_value=api),patch.object(google_auth,'create_calendar') as create:
                with self.assertRaises(RuntimeError):google_auth.sync(snap)
                self.assertEqual(load(config,{}),saved);self.assertEqual(load(mapping,{}),history)
                self.assertTrue(google_auth.sync(snap));create.assert_not_called()
            self.assertEqual(api.events,{'unrelated':123,'owned-event':3000})
            self.assertEqual(load(mapping,{})['same']['event_id'],'owned-event')

    def test_oversized_expiry_is_unknown_for_calendar_sync(self):
        from wuphf.google import valid_expiry
        self.assertFalse(valid_expiry(10**1000))

    def test_same_account_create_update_preserves_old_and_unrelated_events(self):
        api=FakeCalendar();api.events['unrelated']=123;mapping={}
        a={'account_fingerprint':'a'*64,'count':1,'complete':True,'credits':[{'id':'private-a','status':'available','expiresAt':2000}]}
        mapping=reconcile(a,mapping,api,account_fingerprint='a'*64)
        self.assertEqual(len(api.events),2)
        event=next(x for x in api.events if x!='unrelated')
        self.assertNotIn('private-a',event)
        a['credits'][0]['expiresAt']=3000
        mapping=reconcile(a,mapping,api,account_fingerprint='a'*64);self.assertEqual(api.events[event],3000)
        mapping=reconcile({'account_fingerprint':'a'*64,'count':0,'complete':True,'credits':[]},mapping,api,account_fingerprint='a'*64)
        self.assertEqual(api.events,{'unrelated':123,event:3000})
        self.assertIn('private-a',mapping)
    def test_incomplete_read_never_removes_or_changes_events(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        result=reconcile({'count':2,'complete':False,'credits':None},mapping,api,account_fingerprint='a'*64)
        self.assertEqual(result,mapping);self.assertEqual(api.calls,[])
    def test_unknown_expiry_keeps_existing_event(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        result=reconcile({'account_fingerprint':'a'*64,'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':None}]},mapping,api,account_fingerprint='a'*64)
        self.assertEqual(result,mapping);self.assertEqual(api.calls,[])
    def test_restart_can_recreate_deleted_event(self):
        api=FakeCalendar();mapping={'a':{'event_id':'abc','expiresAt':2000}}
        s={'account_fingerprint':'a'*64,'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':2000}]}
        reconcile(s,mapping,api,account_fingerprint='a'*64);self.assertEqual(api.events['abc'],2000)
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

    def test_oauth_ignores_stray_and_malformed_callbacks_until_valid(self):
        import json, tempfile, threading, urllib.error, urllib.parse, urllib.request
        from pathlib import Path
        from unittest.mock import patch
        from wuphf import google_auth
        responses=[];callback_done=threading.Event()
        def open_browser(url):
            query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            redirect=query['redirect_uri'][0]; state=query['state'][0]
            def callbacks():
                paths=['?state=wrong&code=bad', '?'+urllib.parse.urlencode({'state':'☃','code':'bad'}),
                       '?'+urllib.parse.urlencode([('state',state),('state',state),('code','bad')]),
                       '?'+urllib.parse.urlencode([('state',state),('state',''),('code','bad')]),
                       '?'+urllib.parse.urlencode([('state',state),('code','bad'),('code','')]),
                       '?'+urllib.parse.urlencode([('state',state),('error','denied'),('error','')]),
                       '?'+urllib.parse.urlencode({'state':state,'code':''}),
                       '?'+urllib.parse.urlencode({'state':state,'error':''}),
                       '?'+urllib.parse.urlencode({'state':state}),
                       '?'+urllib.parse.urlencode({'state':state,'code':'good'})]
                for path in paths:
                    try:
                        with urllib.request.urlopen(redirect+path,timeout=2) as response:responses.append(response.status)
                    except urllib.error.HTTPError as error:responses.append(error.code)
                    except (urllib.error.URLError,OSError):break
                callback_done.set()
            threading.Thread(target=callbacks,daemon=True).start()
        with tempfile.TemporaryDirectory() as tmp, patch.object(google_auth,'GOOGLE',Path(tmp)/'google.json'), \
             patch.object(google_auth.webbrowser,'open',side_effect=open_browser), \
             patch.object(google_auth,'token_request',return_value={'refresh_token':'refresh'}) as request, \
             patch.object(google_auth,'set_secret'):
            google_auth._connect('client.apps.googleusercontent.com','secret')
            self.assertTrue(callback_done.wait(2))
            self.assertEqual(google_auth.status['state'],'connected')
            self.assertEqual(request.call_args.args[0]['code'],'good')
            self.assertEqual(json.loads(google_auth.GOOGLE.read_text()),{'client_id':'client.apps.googleusercontent.com'})
        self.assertEqual(responses,[400,400,400,400,400,400,400,400,400,200])

    def test_oauth_stray_requests_do_not_extend_deadline(self):
        from unittest.mock import patch
        from wuphf import google_auth
        class Server:
            server_port=1234
            def __init__(self):self.timeouts=[];self.closed=False
            def handle_request(self):self.timeouts.append(self.timeout)
            def server_close(self):self.closed=True
        server=Server()
        with patch.object(google_auth,'CallbackServer',return_value=server), \
             patch.object(google_auth.webbrowser,'open'), \
             patch.object(google_auth.time,'monotonic',side_effect=[0,100,150,181]), \
             patch.object(google_auth,'token_request') as request:
            google_auth._connect('client.apps.googleusercontent.com','secret')
        self.assertEqual(server.timeouts,[0.25,0.25])
        self.assertTrue(server.closed)
        self.assertEqual(google_auth.status['state'],'error')
        request.assert_not_called()

    def test_oauth_stalled_client_does_not_block_valid_callback(self):
        import socket, tempfile, threading, urllib.parse, urllib.request
        from pathlib import Path
        from unittest.mock import patch
        from wuphf import google_auth
        valid_before_release=[]; callback_done=threading.Event()
        def open_browser(url):
            query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            redirect=query['redirect_uri'][0];state=query['state'][0]
            port=urllib.parse.urlsplit(redirect).port
            def callbacks():
                stalled=socket.create_connection(('127.0.0.1',port),timeout=2)
                completed=threading.Event()
                def valid():
                    try:
                        with urllib.request.urlopen(redirect+'?'+urllib.parse.urlencode({'state':state,'code':'good'}),timeout=2):completed.set()
                    except OSError:pass
                threading.Thread(target=valid,daemon=True).start()
                valid_before_release.append(completed.wait(0.5))
                stalled.close();callback_done.set()
            threading.Thread(target=callbacks,daemon=True).start()
        with tempfile.TemporaryDirectory() as tmp, patch.object(google_auth,'GOOGLE',Path(tmp)/'google.json'), \
             patch.object(google_auth.webbrowser,'open',side_effect=open_browser), \
             patch.object(google_auth,'token_request',return_value={'refresh_token':'refresh'}), \
             patch.object(google_auth,'set_secret'):
            google_auth._connect('client.apps.googleusercontent.com','secret')
            self.assertEqual(google_auth.status['state'],'connected')
        self.assertTrue(callback_done.wait(2))
        self.assertEqual(valid_before_release,[True])

    def test_oauth_callback_server_limits_simultaneous_workers(self):
        from unittest.mock import patch
        from wuphf import google_auth
        cls=getattr(google_auth,'CallbackServer',None)
        self.assertIsNotNone(cls)
        with cls(('127.0.0.1',0),google_auth.BaseHTTPRequestHandler) as server:
            with patch.object(google_auth.ThreadingHTTPServer,'process_request') as dispatch,patch.object(server,'shutdown_request') as close:
                for _ in range(9):server.process_request(object(),('127.0.0.1',1))
                self.assertEqual(dispatch.call_count,8)
                self.assertEqual(close.call_count,1)
                with patch.object(google_auth.ThreadingHTTPServer,'process_request_thread'):
                    server.process_request_thread(object(),('127.0.0.1',1))
                server.process_request(object(),('127.0.0.1',1))
                self.assertEqual(dispatch.call_count,9)
