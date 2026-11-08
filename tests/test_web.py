import http.client,json,threading,unittest
from unittest.mock import patch
from wuphf.web import create_server

class WebTests(unittest.TestCase):
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
    def test_direct_google_connect_explains_missing_client_setup(self):
        with patch('wuphf.google_auth.BUNDLED_CLIENT',new=__import__('pathlib').Path('/nonexistent/wuphf-client.json')):
            res,data=self.request('POST','/api/google/connect',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
        self.assertEqual(res.status,400)
        self.assertIn(b'OAuth',data)
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
        with patch('wuphf.gmail_auth.status',{'state':'disconnected','message':'Not connected'}), patch('wuphf.gmail_auth.connected',return_value=True),patch('wuphf.gmail_auth.disconnect') as disconnect,patch('wuphf.google_auth.disconnect') as calendar_disconnect,patch('wuphf.web.check_lock') as lock:
            res,body=self.request('GET','/api/gmail/status',headers={'Cookie':'wuphf_session=test-token'})
            self.assertEqual(res.status,200);self.assertEqual(json.loads(body)['state'],'saved')
            res,_=self.request('POST','/api/gmail/disconnect',{}, {'Cookie':'wuphf_session=test-token','Origin':f'http://127.0.0.1:{self.port}','X-WUPHF-Token':'test-token'})
            self.assertEqual(res.status,200);disconnect.assert_called_once_with();calendar_disconnect.assert_not_called()

    def test_background_status_is_independent_of_live_codex_read(self):
        with patch('wuphf.web.read_snapshot',side_effect=RuntimeError('offline')),patch('wuphf.web.load',return_value={'last_check':100,'last_error':'check failed'}),patch('wuphf.platform_jobs.monitoring_status',return_value='enabled',create=True):
            res,data=self.request('GET','/api/background',headers={'Cookie':'wuphf_session=test-token'})
        self.assertEqual(res.status,200)
        status=json.loads(data)
        self.assertEqual(status['scheduler'],'enabled')
        self.assertEqual(status['last_check'],100)
        self.assertTrue(status['last_error'])

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
