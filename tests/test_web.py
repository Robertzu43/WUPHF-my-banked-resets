import http.client,json,threading,unittest
from unittest.mock import patch
from wuphf.web import create_server

class WebTests(unittest.TestCase):
    def test_calendar_sync_returns_actionable_account_error_code_without_identity(self):
        from wuphf.google import CalendarAccountError
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as d,patch('wuphf.web.cli.DATA',Path(d)),patch('wuphf.web.read_snapshot',return_value={'complete':True}),patch('wuphf.google_auth.sync',side_effect=CalendarAccountError('calendar_account_mismatch')):
            res,body=self.request('POST','/api/google/sync',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,409)
        self.assertEqual(json.loads(body),{'error':'calendar_account_mismatch'})

    def test_calendar_data_and_conflicts_return_sanitized_codes(self):
        from wuphf.google import CalendarSyncError
        from pathlib import Path
        import tempfile
        for code in ('calendar_data_required','calendar_event_conflict'):
            with self.subTest(code=code),tempfile.TemporaryDirectory() as d,patch('wuphf.web.cli.DATA',Path(d)),patch('wuphf.web.read_snapshot',return_value={'complete':True}),patch('wuphf.google_auth.sync',side_effect=CalendarSyncError(code)):
                res,body=self.request('POST','/api/google/sync',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
                self.assertEqual(res.status,409);self.assertEqual(json.loads(body),{'error':code})

    def setUp(self):
        self.server=create_server(port=0, token='test-token')
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.port=self.server.server_port
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()
    def request(self, method, path, body=None, headers=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.port,timeout=3)
        headers=headers or {}
        if body is not None:body=json.dumps(body);headers['Content-Type']='application/json'
        conn.request(method,path,body,headers);response=conn.getresponse();payload=response.read();conn.close()
        return response,payload
    def test_requests_require_session_and_cross_site_post_is_rejected(self):
        res,_=self.request('GET','/api/settings');self.assertEqual(res.status,403)
        res,_=self.request('POST','/api/settings',{}, {'Cookie':'wuphf_session=test-token','Origin':'https://other.example','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,403)
    def test_protected_mac_install_explains_how_to_move_app(self):
        from pathlib import Path
        import tempfile
        from wuphf import cli
        with tempfile.TemporaryDirectory() as d:
            home=Path(d)
            with patch.object(Path,'home',return_value=home),patch.object(cli,'PLIST',home/'agent.plist'),patch.object(cli,'ROOT',home/'Documents'/'WUPHF'),patch.object(cli.sys,'platform','darwin'),patch.object(cli.sys,'frozen',False,create=True),patch.object(cli.shutil,'which',return_value='/usr/bin/codex'):
                res,body=self.request('POST','/api/install',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
            self.assertEqual(res.status,400);self.assertEqual(json.loads(body)['error'],'mac_protected_location')
            self.assertFalse((home/'agent.plist').exists())

    def test_pixel_font_is_same_origin_and_requires_session(self):
        res,_=self.request('GET','/assets/geist-pixel-square.woff2')
        self.assertEqual(res.status,403)
        res,body=self.request('GET','/assets/geist-pixel-square.woff2',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200)
        self.assertEqual(res.getheader('Content-Type'),'font/woff2')
        self.assertTrue(body.startswith(b'wOF2'))
        res,_=self.request('GET','/assets/not-a-font.woff2',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,404)
    def test_only_safe_status_is_exposed(self):
        sample={'count':1,'complete':True,'credits':[{'id':'SECRET-ID','status':'available','expiresAt':1796070020}]}
        with patch('wuphf.web.read_snapshot',return_value=sample),patch('wuphf.web.load',return_value={}):
            res,data=self.request('GET','/api/status',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200);self.assertNotIn(b'SECRET-ID',data)
        self.assertEqual(json.loads(data)['count'],1)
    def test_saving_secrets_never_writes_them_to_settings(self):
        payload={'advance_days':7,'repeat_hours':24,'channels':{'telegram':{'chat_id':'123','token':'123:secret'}}}
        with patch('wuphf.web.set_secret') as secret,patch('wuphf.web.save') as save:
            res,_=self.request('POST','/api/settings',payload,{'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,200);secret.assert_called_once_with('telegram.token','123:secret')
        self.assertNotIn('secret',str(save.call_args))
    def test_google_connect_starts_with_imported_client_without_returning_secret(self):
        client={'installed':{'client_id':'id.apps.googleusercontent.com','client_secret':'secret'}}
        with patch('wuphf.google_auth.start_connect') as start:
            res,data=self.request('POST','/api/google/connect',client,{'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,200);start.assert_called_once_with(client);self.assertNotIn(b'secret',data)
    def test_google_connect_failure_does_not_require_a_personal_oauth_registration(self):
        with patch('wuphf.google_auth.default_client',return_value={}):
            res,data=self.request('POST','/api/google/connect',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,400)
        self.assertEqual(json.loads(data),{'error':'Could not start Google sign-in. Check the connection status and try again.'})
    def test_provider_connect_validation_errors_use_generic_sign_in_guidance(self):
        for provider in ('gmail','google'):
            with self.subTest(provider=provider):
                res,body=self.request('POST','/api/'+provider+'/connect',{'invalid':'private-client-path'}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
                self.assertEqual(res.status,400)
                self.assertEqual(json.loads(body),{'error':'Could not start Google sign-in. Check the connection status and try again.'})
                self.assertNotIn(b'private-client-path',body)

    def test_incomplete_snapshot_refuses_calendar_export(self):
        with patch('wuphf.web.read_snapshot',return_value={'count':2,'credits':None,'complete':False}):
            res,body=self.request('GET','/api/calendar',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,409)
        self.assertIn(b'incomplete',body.lower())
        self.assertNotIn(b'BEGIN:VCALENDAR',body)
    def test_language_preference_preserves_channels(self):
        current={'advance_days':7,'repeat_hours':24,'channels':{'ntfy':{'topic':'sample'}}}
        with patch('wuphf.web.load',return_value=current),patch('wuphf.web.save') as save:
            res,_=self.request('POST','/api/language',{'language':'es'}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,200)
        self.assertEqual(save.call_args.args[1]['language'],'es')
        self.assertEqual(save.call_args.args[1]['channels'],current['channels'])
    def test_rejects_unknown_language(self):
        with patch('wuphf.web.load',return_value={'advance_days':7,'repeat_hours':24,'channels':{}}),patch('wuphf.web.save') as save:
            res,_=self.request('POST','/api/language',{'language':'xx'}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,400);save.assert_not_called()
    def test_incomplete_calendar_error_uses_selected_language(self):
        with patch('wuphf.web.read_snapshot',return_value={'count':2,'credits':None,'complete':False}),patch('wuphf.web.load',return_value={'language':'es'}):
            res,body=self.request('GET','/api/calendar',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,409)
        self.assertIn('incompletos',json.loads(body)['error'].lower())

    def test_gmail_channel_settings_save_recipient(self):
        payload={'advance_days':7,'repeat_hours':24,'channels':{'gmail':{'to':'person@example.com'}}}
        with patch('wuphf.web.save') as save:
            res,_=self.request('POST','/api/settings',payload,{'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,200)
        self.assertEqual(save.call_args.args[1]['channels']['gmail'],{'to':'person@example.com'})

    def test_gmail_rejects_injected_recipient(self):
        payload={'advance_days':7,'repeat_hours':24,'channels':{'gmail':{'to':'person@example.com\nBcc: other@example.com'}}}
        with patch('wuphf.web.save') as save:
            res,_=self.request('POST','/api/settings',payload,{'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,400);save.assert_not_called()

    def test_gmail_connect_requires_session_and_starts_oauth(self):
        client={'installed':{'client_id':'id.apps.googleusercontent.com','client_secret':'secret'}}
        with patch('wuphf.gmail_auth.start_connect') as start:
            res,_=self.request('POST','/api/gmail/connect',client)
            self.assertEqual(res.status,403);start.assert_not_called()
            res,data=self.request('POST','/api/gmail/connect',client,{'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
            self.assertEqual(res.status,200);start.assert_called_once_with(client);self.assertNotIn(b'secret',data)

    def test_gmail_status_and_disconnect_use_separate_authorization(self):
        with patch('wuphf.gmail_auth.status',{'state':'disconnected','message':'Not connected'}), patch('wuphf.web.load',return_value={'client_id':'saved'}),patch('wuphf.gmail_auth.disconnect') as disconnect,patch('wuphf.google_auth.disconnect') as calendar_disconnect,patch('wuphf.web.check_lock') as lock:
            res,body=self.request('GET','/api/gmail/status',headers={'Cookie':'wuphf_session=test-token'})
            self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['state'],'saved')
            res,_=self.request('POST','/api/gmail/disconnect',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
            self.assertEqual(res.status,200);disconnect.assert_called_once_with();calendar_disconnect.assert_not_called()

    def test_gmail_saved_configuration_without_keychain_credentials_can_be_disconnected(self):
        import tempfile
        from pathlib import Path
        from wuphf import gmail_auth
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);config=root/'gmail.json'
            config.write_text(json.dumps({'client_id':'saved-private-id.apps.googleusercontent.com'}),encoding='utf-8')
            public={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'public-client-value'}}
            with patch.object(gmail_auth,'GMAIL',config),patch.object(gmail_auth,'status',{'state':'disconnected','message':'Not connected'}),patch.object(gmail_auth,'get_secret',return_value=None) as get_secret,patch.object(gmail_auth,'delete_secret') as delete_secret,patch.object(gmail_auth,'default_client',return_value=public),patch('wuphf.web.cli.DATA',root):
                res,body=self.request('GET','/api/gmail/status',headers=headers)
                self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['state'],'saved')
                self.assertIn('test',json.loads(body)['message'].lower())
                self.assertIn('disconnect',json.loads(body)['message'].lower())
                self.assertNotIn(b'saved-private-id',body);get_secret.assert_not_called()
                res,_=self.request('POST','/api/gmail/connect',{},headers)
                self.assertEqual(res.status,503,'An existing config still requires local disconnect before a new connection')
                self.assertTrue(config.exists())
                res,body=self.request('GET','/api/gmail/status',headers=headers)
                self.assertEqual(json.loads(body)['state'],'saved','A refused duplicate connection must not hide saved config')
                res,_=self.request('POST','/api/gmail/disconnect',{},headers)
                self.assertEqual(res.status,200);self.assertFalse(config.exists())
                self.assertEqual([call.args[0] for call in delete_secret.call_args_list],['gmail.refresh_token','gmail.client_secret'])
                res,body=self.request('GET','/api/gmail/status',headers=headers)
                self.assertEqual(json.loads(body)['state'],'disconnected')

    def test_gmail_saved_status_does_not_query_an_unavailable_keychain(self):
        import tempfile
        from pathlib import Path
        from wuphf import gmail_auth
        with tempfile.TemporaryDirectory() as tmp:
            config=Path(tmp)/'gmail.json';config.write_text(json.dumps({'client_id':'saved-private-id'}),encoding='utf-8')
            with patch.object(gmail_auth,'GMAIL',config),patch.object(gmail_auth,'status',{'state':'disconnected','message':'Not connected'}),patch.object(gmail_auth,'get_secret',side_effect=RuntimeError('private keychain error')) as get_secret:
                res,body=self.request('GET','/api/gmail/status',headers={'Cookie':'wuphf_session=test-token'})
                self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['state'],'saved')
                self.assertNotIn(b'private',body);get_secret.assert_not_called()

    def test_background_status_is_independent_of_live_codex_read(self):
        with patch('wuphf.web.read_snapshot',side_effect=RuntimeError('offline')),patch('wuphf.web.load',return_value={'last_check':100,'last_error':'check failed','failures':{'gmail':'private provider error','telegram':'private token'}}),patch('wuphf.platform_jobs.monitoring_status',return_value='enabled',create=True):
            res,data=self.request('GET','/api/background',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200)
        status=json.loads(data)
        self.assertEqual(status['scheduler'],'enabled')
        self.assertEqual(status['last_check'],100)
        self.assertTrue(status['last_error'])
        self.assertEqual(status.get('failures',[]),['gmail','telegram'])
        self.assertNotIn(b'private',data)

    def test_background_status_has_its_own_accessible_display(self):
        res,body=self.request('GET','/',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200)
        self.assertIn(b'id="background-status"',body)
        self.assertIn(b'/api/background',body)

    def test_background_check_age_and_failure_are_reported_separately(self):
        from wuphf import web
        background_check_status=getattr(web,"background_check_status",lambda state,now:"not implemented")
        self.assertEqual(background_check_status({},now=2000),'never')
        self.assertEqual(background_check_status({'last_check':1000},now=2000),'recent')
        self.assertEqual(background_check_status({'last_check':100},now=2000),'stale')
        self.assertEqual(background_check_status({'last_check':3000},now=2000),'unknown')
        self.assertEqual(background_check_status({'last_check':float('nan')},now=2000),'unknown')

    def test_background_poll_updates_scheduler_age_and_failures(self):
        import shutil, subprocess
        if not shutil.which('node'):self.skipTest('Node is unavailable')
        result=subprocess.run(['node','tests/test_background_ui.js'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_guided_setup_prevents_stale_tests_and_reports_truthful_readiness(self):
        import shutil, subprocess
        if not shutil.which('node'):self.skipTest('Node is unavailable')
        result=subprocess.run(['node','tests/test_setup_ui.js'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_legacy_ntfy_is_hidden_for_new_users_and_existing_settings_can_be_disabled(self):
        import shutil, subprocess
        res,body=self.request('GET','/',headers={'Cookie':'wuphf_session=test-token'})
        self.assertIn(b'id="ntfy-legacy" hidden',body)
        self.assertNotIn(b'id="ntfy-generate"',body)
        if not shutil.which('node'):self.skipTest('Node is unavailable')
        result=subprocess.run(['node','tests/test_legacy_ntfy_ui.js'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_telegram_discovery_requires_explicit_request_and_does_not_expose_token(self):
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        with patch('wuphf.channels.telegram_chat_id',return_value='12345',create=True) as lookup,patch('wuphf.web.load',return_value={'channels':{'telegram':{}}}):
            res,_=self.request('POST','/api/telegram/discover',{'token':'123:secret'})
            self.assertEqual(res.status,403);lookup.assert_not_called()
            res,body=self.request('POST','/api/telegram/pair',{},headers)
            self.assertEqual(res.status,200);phrase=json.loads(body)['phrase']
            res,body=self.request('POST','/api/telegram/discover',{'token':'123:secret'},headers)
            self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['chat_id'],'12345')
            self.assertNotIn(b'secret',body);lookup.assert_called_once_with('123:secret',phrase)

    def test_telegram_discovery_button_behaviour(self):
        import shutil, subprocess
        res,body=self.request('GET','/',headers={'Cookie':'wuphf_session=test-token'})
        self.assertTrue(b'id="telegram-discover"' in body)
        if not shutil.which('node'):self.skipTest('Node is unavailable')
        result=subprocess.run(['node','tests/test_telegram_ui.js'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_telegram_discovery_uses_saved_token_and_redacts_errors(self):
        from wuphf.channels import ChannelError
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        res,body=self.request('POST','/api/telegram/pair',{},headers)
        phrase=json.loads(body)['phrase']
        with patch('wuphf.cli.get_secret',return_value='123:saved-secret') as secret,patch('wuphf.channels.telegram_chat_id',side_effect=ChannelError('token or id: saved-secret')) as lookup:
            res,body=self.request('POST','/api/telegram/discover',{},headers)
        self.assertEqual(res.status,400)
        self.assertEqual(json.loads(body)['error'],'telegram_unavailable')
        self.assertNotIn(b'saved-secret',body)
        secret.assert_called_once_with('telegram.token');lookup.assert_called_once_with('123:saved-secret',phrase)

    def test_telegram_pairing_rotates_and_expires_before_lookup(self):
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        with patch('wuphf.web.time.monotonic',return_value=100),patch('wuphf.web.secrets.token_urlsafe',side_effect=['first','second']):
            res,body=self.request('POST','/api/telegram/pair',{},headers)
            self.assertEqual(res.status,200);first=json.loads(body)['phrase']
            res,body=self.request('POST','/api/telegram/pair',{},headers)
            self.assertEqual(res.status,200);second=json.loads(body)['phrase']
        self.assertNotEqual(first,second)
        with patch('wuphf.web.time.monotonic',return_value=701),patch('wuphf.channels.telegram_chat_id') as lookup:
            res,body=self.request('POST','/api/telegram/discover',{'token':'123:secret'},headers)
        self.assertEqual(res.status,400);self.assertEqual(json.loads(body)['error'],'telegram_pair_expired')
        lookup.assert_not_called()

    def test_telegram_pairing_is_single_use(self):
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        res,body=self.request('POST','/api/telegram/pair',{},headers)
        self.assertEqual(res.status,200);phrase=json.loads(body)['phrase']
        self.assertTrue(phrase.startswith('WUPHF-'))
        with patch('wuphf.channels.telegram_chat_id',return_value='12345') as lookup:
            res,body=self.request('POST','/api/telegram/discover',{'token':'123:secret'},headers)
            self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['chat_id'],'12345')
            res,body=self.request('POST','/api/telegram/discover',{'token':'123:secret'},headers)
            self.assertEqual(res.status,400);self.assertEqual(json.loads(body)['error'],'telegram_pair_expired')
            lookup.assert_called_once_with('123:secret',phrase)

    def test_telegram_replaced_pairing_during_lookup_never_returns_old_chat(self):
        headers={'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'}
        self.request('POST','/api/telegram/pair',{},headers)
        def replace(*args):
            res,_=self.request('POST','/api/telegram/pair',{},headers)
            self.assertEqual(res.status,200)
            return '98765'
        with patch('wuphf.channels.telegram_chat_id',side_effect=replace):
            res,body=self.request('POST','/api/telegram/discover',{'token':'123:secret'},headers)
        self.assertEqual(res.status,400);self.assertEqual(json.loads(body)['error'],'telegram_pair_expired')
        self.assertNotIn(b'98765',body)

    def test_status_does_not_expose_account_fingerprint(self):
        sample={'count':1,'complete':True,'account_fingerprint':'private-fingerprint','credits':[{'id':'private-credit','expiresAt':1796070020}]}
        with patch('wuphf.web.read_snapshot',return_value=sample),patch('wuphf.web.load',return_value={}):
            res,data=self.request('GET','/api/status',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200)
        self.assertNotIn(b'private-fingerprint',data);self.assertNotIn(b'private-credit',data)

    def test_rejected_small_post_waits_briefly_for_body_before_closing(self):
        import socket
        headers=(f'POST /api/settings HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n'
                 'Origin: https://other.example\r\nContent-Length: 2\r\n\r\n').encode()
        with socket.create_connection(('127.0.0.1',self.port),timeout=2) as conn:
            conn.sendall(headers);conn.settimeout(0.1)
            with self.assertRaises(socket.timeout):conn.recv(1024)
            conn.sendall(b'{}');conn.settimeout(2)
            self.assertIn(b' 403 ',conn.recv(1024))

    def test_rejected_oversized_post_does_not_wait_for_body(self):
        import socket
        headers=(f'POST /api/settings HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n'
                 'Origin: https://other.example\r\nContent-Length: 99999999\r\n\r\n').encode()
        with socket.create_connection(('127.0.0.1',self.port),timeout=1) as conn:
            conn.sendall(headers)
            self.assertIn(b' 403 ',conn.recv(1024))

    def test_rejected_partial_post_is_bounded(self):
        import socket,time
        headers=(f'POST /api/settings HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n'
                 'Origin: https://other.example\r\nContent-Length: 16384\r\n\r\n').encode()
        with socket.create_connection(('127.0.0.1',self.port),timeout=2) as conn:
            started=time.monotonic();conn.sendall(headers+b'{')
            self.assertIn(b' 403 ',conn.recv(1024))
            self.assertLess(time.monotonic()-started,1.5)

    def test_incomplete_unauthenticated_request_releases_connection(self):
        import socket
        with socket.create_connection(('127.0.0.1',self.port),timeout=7) as conn:
            conn.sendall(b'GET / HTTP/1.1\r\n')
            try:closed=conn.recv(1)
            except socket.timeout:self.fail('Incomplete request kept its worker past the read deadline')
            self.assertEqual(closed,b'')
        res,_=self.request('GET','/api/settings')
        self.assertEqual(res.status,403)

    def test_setup_server_bounds_concurrent_workers(self):
        import socket
        entered=threading.Condition();release=threading.Event();workers=[];connections=[]
        def hold(handler):
            with entered:
                workers.append(handler)
                entered.notify_all()
            release.wait(3)
        try:
            with patch.object(self.server.RequestHandlerClass,'handle',hold):
                for count in range(1,9):
                    connections.append(socket.create_connection(('127.0.0.1',self.port),timeout=2))
                    with entered:self.assertTrue(entered.wait_for(lambda:len(workers)>=count,timeout=2))
                with socket.create_connection(('127.0.0.1',self.port),timeout=1) as excess:
                    try:closed=excess.recv(1)
                    except socket.timeout:self.fail('Excess connection started an unbounded worker')
                    self.assertEqual(closed,b'')
                self.assertEqual(len(workers),8)
        finally:
            release.set()
            for conn in connections:conn.close()

    def test_failed_refresh_cannot_restore_stale_status_on_language_change(self):
        import shutil, subprocess
        if not shutil.which('node'):self.skipTest('Node is unavailable')
        result=subprocess.run(['node','tests/test_status_ui.js'],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
