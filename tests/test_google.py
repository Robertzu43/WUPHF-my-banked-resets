import copy
import json
import unittest
from unittest.mock import patch
from wuphf.google import reconcile

class FakeCalendar:
    calendar_id='owned'
    language='en'
    def __init__(self):self.events={};self.calls=[];self.failure=None
    def get(self,eid):
        from wuphf.google import CalendarRequestError
        self.calls.append(('get',eid))
        if self.failure:raise self.failure
        if eid not in self.events:raise CalendarRequestError(404)
        return copy.deepcopy(self.events[eid])
    def insert(self,eid,body):
        self.calls.append(('insert',eid,copy.deepcopy(body)))
        if self.failure:raise self.failure
        self.events[eid]={**copy.deepcopy(body),'etag':'"1"'}
        return copy.deepcopy(self.events[eid])
    def update(self,eid,body,*,etag):
        self.calls.append(('update',eid,etag))
        if self.failure:raise self.failure
        self.events[eid]={**copy.deepcopy(body),'etag':'"2"'}
        return copy.deepcopy(self.events[eid])
    def delete(self,eid,*,etag):
        self.calls.append(('delete',eid,etag))
        if self.failure:raise self.failure
        self.events[eid]={'id':eid,'status':'cancelled'}


def reading(*credits):
    return {'complete':True,'count':len(credits),'credits':list(credits),'account_fingerprint':'a'*64}


class CalendarLifecycleTests(unittest.TestCase):
    def test_stale_owned_event_is_removed_from_mapping(self):
        api=FakeCalendar()
        entry={'event_id':'abcde','expiresAt':2000,'owner':'1'*32,'account_fingerprint':'a'*64,'calendar_id':'owned','etag':'"1"'}
        import hashlib
        api.events['abcde']={'id':'abcde','status':'confirmed','etag':'"1"','extendedProperties':{'private':{'wuphfSchema':'1','wuphfOwner':'1'*32,'wuphfAccount':'a'*64,'wuphfCredit':hashlib.sha256(b'wuphf-credit-v1\0a').hexdigest()}}}
        self.assertEqual(reconcile(reading(),{'a':entry},api,lambda _:None,account_fingerprint='a'*64),{})

    def run_sync(self,snap,mapping,api,saves=None,now=1000):
        return reconcile(snap,mapping,api,lambda m:saves.append(copy.deepcopy(m)) if saves is not None else None,account_fingerprint='a'*64,now=now)

    def managed(self,ident='private-a',expiry=2000):
        api=FakeCalendar();saves=[]
        mapping=self.run_sync(reading({'id':ident,'expiresAt':expiry}),{},api,saves)
        return api,mapping,saves

    def conflict(self,snap,mapping,api):
        from wuphf.google import CalendarSyncError
        before=copy.deepcopy(api.events);local=copy.deepcopy(mapping)
        with self.assertRaises(CalendarSyncError) as caught:self.run_sync(snap,mapping,api)
        self.assertEqual(caught.exception.code,'calendar_event_conflict')
        self.assertEqual(api.events,before);self.assertEqual(mapping,local)

    def test_reserves_marked_random_event_before_insert_then_deletes_stale(self):
        api=FakeCalendar();saves=[]
        def save(m):
            saves.append(copy.deepcopy(m))
            if len(saves)==1:self.assertFalse(api.events)
        snap=reading({'id':'private-credit','expiresAt':2000})
        mapping=reconcile(snap,{},api,save,account_fingerprint='a'*64,now=1000)
        entry=mapping['private-credit'];eid=entry['event_id']
        self.assertRegex(eid,r'^[a-v0-9]{5,1024}$');self.assertNotIn('private-credit',eid)
        self.assertNotIn('etag',saves[0]['private-credit']);self.assertEqual(entry['etag'],'"1"')
        import hashlib
        expected={'wuphfSchema':'1','wuphfOwner':entry['owner'],'wuphfAccount':'a'*64,'wuphfCredit':hashlib.sha256(b'wuphf-credit-v1\0private-credit').hexdigest()}
        self.assertEqual(api.events[eid]['extendedProperties']['private'],expected)
        api.events['unrelated']={'id':'unrelated','summary':'Mine'}
        cleaned=self.run_sync(reading(),mapping,api,saves)
        self.assertEqual(cleaned,{})
        self.assertEqual(api.calls[-1],('delete',eid,'"1"'))
        self.assertEqual(api.events['unrelated'],{'id':'unrelated','summary':'Mine'})
        new=self.run_sync(snap,cleaned,api)
        self.assertNotEqual(new['private-credit']['event_id'],eid)

    def test_invalid_whole_snapshot_blocks_all_writes(self):
        from wuphf.google import CalendarSyncError
        api,mapping,_=self.managed()
        good=reading({'id':'different','expiresAt':3000})
        variants=[{**good,'complete':False},{**good,'complete':1},{**good,'count':True},{**good,'count':None},{**good,'count':2},{**good,'credits':None},reading({'id':'x','expiresAt':2000},{'id':'x','expiresAt':2000}),reading({'id':'','expiresAt':2000}),reading(None)]
        variants.extend(reading({'id':'different','expiresAt':expiry}) for expiry in (None,True,float('nan'),float('inf'),-1,10**1000))
        variants.extend(reading({'id':'different','expiresAt':3000,'status':status}) for status in (None,'used','unknown',True))
        for snap in variants:
            with self.subTest(snap=snap):
                api.calls=[];before=copy.deepcopy(api.events)
                with self.assertRaises(CalendarSyncError) as caught:self.run_sync(snap,mapping,api)
                self.assertEqual(caught.exception.code,'calendar_data_required');self.assertEqual(api.calls,[]);self.assertEqual(api.events,before)

    def test_update_uses_saved_version_and_past_present_credit_is_not_deleted(self):
        api,mapping,_=self.managed();eid=mapping['private-a']['event_id'];api.calls=[]
        self.run_sync(reading({'id':'private-a','expiresAt':2000}),mapping,api)
        self.assertEqual(api.calls,[('get',eid)])
        updated=self.run_sync(reading({'id':'private-a','expiresAt':500}),mapping,api)
        self.assertEqual(api.calls[-1],('update',eid,'"1"'));self.assertEqual(updated['private-a']['etag'],'"2"')
        self.assertEqual(updated['private-a']['expiresAt'],500)
        self.assertEqual(self.run_sync(reading({'id':'old','expiresAt':1000}),{},FakeCalendar()),{})

    def test_legacy_events_are_never_adopted_updated_or_removed(self):
        api=FakeCalendar();api.events['legacy']={'id':'legacy','summary':'old'}
        mapping={'private-a':{'event_id':'legacy','expiresAt':2000}}
        for snap in (reading(),reading({'id':'private-a','expiresAt':3000})):
            self.conflict(snap,mapping,api)
        self.assertEqual(api.calls,[])

    def test_every_ownership_or_version_mismatch_preserves_remote_and_local(self):
        for change in ('owner','account','credit','schema','id','etag','missing_etag','missing_markers','attendees','recurrence','special','unknown_status','missing_status'):
            for snap in (reading(),reading({'id':'private-a','expiresAt':3000})):
                with self.subTest(change=change,snap=snap):
                    api,mapping,_=self.managed();eid=mapping['private-a']['event_id'];event=api.events[eid]
                    marker={'owner':'wuphfOwner','account':'wuphfAccount','credit':'wuphfCredit','schema':'wuphfSchema'}.get(change)
                    if marker:event['extendedProperties']['private'][marker]='wrong'
                    elif change=='id':event['id']='replaced'
                    elif change=='etag':event['etag']='"edited"'
                    elif change=='missing_etag':event.pop('etag')
                    elif change=='missing_markers':event.pop('extendedProperties')
                    elif change=='special':event['eventType']='birthday'
                    elif change=='unknown_status':event['status']=None
                    elif change=='missing_status':event.pop('status')
                    else:event[change]=[{'email':'someone@example.test'}] if change=='attendees' else ['RRULE:FREQ=DAILY']
                    self.conflict(snap,mapping,api)
                    self.assertFalse(any(c[0] in ('update','delete') for c in api.calls))

    def test_bad_local_bindings_shapes_and_duplicate_ids_block_before_remote_calls(self):
        api,mapping,_=self.managed()
        variants=[]
        for key,value in (('calendar_id','other'),('account_fingerprint','b'*64),('owner',''),('etag',''),('event_id','bad!'),('expiresAt',True)):
            bad=copy.deepcopy(mapping);bad['private-a'][key]=value;variants.append(bad)
        bad=copy.deepcopy(mapping);bad['duplicate']=copy.deepcopy(bad['private-a']);variants.append(bad)
        variants.extend(({'private-a':None},{'private-a':{}},[],{'':mapping['private-a']}))
        for bad in variants:
            with self.subTest(mapping=bad):
                api.calls=[];self.conflict(reading(),bad,api);self.assertEqual(api.calls,[])

    def test_preinsert_save_failure_causes_zero_remote_writes(self):
        api=FakeCalendar()
        with self.assertRaises(OSError):
            reconcile(reading({'id':'a','expiresAt':2000}),{},api,lambda _:(_ for _ in ()).throw(OSError('full')),account_fingerprint='a'*64,now=1000)
        self.assertFalse(api.events);self.assertEqual(api.calls,[])

    def test_pending_reservation_retries_absent_insert_but_never_adopts_existing_resource(self):
        api,mapping,saves=self.managed();pending=saves[0];eid=mapping['private-a']['event_id']
        self.conflict(reading({'id':'private-a','expiresAt':2000}),pending,api)
        self.conflict(reading(),pending,api)
        api.events.pop(eid);api.calls=[]
        retried=self.run_sync(reading({'id':'private-a','expiresAt':3000}),pending,api)
        self.assertEqual(retried['private-a']['event_id'],eid)
        self.assertEqual([c[0] for c in api.calls],['get','insert'])

    def test_cancelled_resource_suppresses_active_recreation_and_retires_absent_mapping(self):
        api,mapping,_=self.managed();eid=mapping['private-a']['event_id']
        api.events[eid]={'id':eid,'status':'cancelled'};api.calls=[]
        for _ in range(2):mapping=self.run_sync(reading({'id':'private-a','expiresAt':3000}),mapping,api)
        self.assertIn('private-a',mapping);self.assertTrue(all(c[0]=='get' for c in api.calls))
        self.assertEqual(self.run_sync(reading(),mapping,api),{})

    def test_delete_save_loss_recovers_without_second_delete(self):
        api,mapping,_=self.managed();eid=mapping['private-a']['event_id']
        with self.assertRaises(OSError):
            reconcile(reading(),mapping,api,lambda _:(_ for _ in ()).throw(OSError('full')),account_fingerprint='a'*64,now=1000)
        api.calls=[]
        self.assertEqual(self.run_sync(reading(),mapping,api),{});self.assertEqual(api.calls,[('get',eid)])

    def test_insert_and_update_final_save_loss_stay_visible_conflicts_on_restart(self):
        from wuphf.google import CalendarSyncError
        for operation in ('insert','update'):
            api,mapping,saves=self.managed();persisted=copy.deepcopy(mapping if operation=='update' else {})
            def save(m):
                nonlocal persisted
                if operation=='insert' and 'etag' not in m['private-a']:persisted=copy.deepcopy(m)
                else:raise OSError('full')
            if operation=='insert':api=FakeCalendar()
            snap=reading({'id':'private-a','expiresAt':3000})
            with self.assertRaises(OSError):reconcile(snap,{} if operation=='insert' else mapping,api,save,account_fingerprint='a'*64,now=1000)
            self.conflict(snap,persisted,api)
            with self.assertRaises(CalendarSyncError):self.run_sync(reading(),persisted,api)

    def test_request_failures_and_race_preserve_saved_state(self):
        from wuphf.google import CalendarRequestError,CalendarSyncError
        for status in (401,403,404,410,412,429,500):
            api,mapping,_=self.managed();api.failure=CalendarRequestError(status,'fullSyncRequired' if status==410 else None)
            with self.assertRaises(RuntimeError):self.run_sync(reading(),mapping,api)
            self.assertIn('private-a',mapping)
        api,mapping,_=self.managed()
        with patch.object(api,'delete',side_effect=CalendarRequestError(412)) as delete:
            with self.assertRaises(CalendarSyncError) as caught:self.run_sync(reading(),mapping,api)
            self.assertEqual(caught.exception.code,'calendar_event_conflict');delete.assert_called_once_with(mapping['private-a']['event_id'],etag='"1"')
        self.assertEqual(mapping['private-a']['etag'],'"1"')

    def test_malformed_get_never_triggers_recreation_or_cleanup(self):
        for response in (None,{},[],{'id':'wrong'}):
            for pending in (False,True):
                api,mapping,saves=self.managed()
                if pending:mapping=saves[0]
                with self.subTest(response=response,pending=pending),patch.object(api,'get',return_value=response):
                    self.conflict(reading({'id':'private-a','expiresAt':3000}),mapping,api)

    def test_lost_insert_response_and_409_keep_one_reservation_without_overwrite(self):
        from wuphf.google import CalendarRequestError,CalendarSyncError
        for failure in (RuntimeError('offline'),CalendarRequestError(409)):
            api=FakeCalendar();saves=[];original=api.insert
            def insert(eid,body):
                original(eid,body)
                raise failure
            with patch.object(api,'insert',side_effect=insert):
                with self.assertRaises(RuntimeError):self.run_sync(reading({'id':'a','expiresAt':2000}),{},api,saves)
            self.assertEqual(len(saves),1);eid=saves[0]['a']['event_id'];self.assertIn(eid,api.events)
            with self.assertRaises(CalendarSyncError):self.run_sync(reading({'id':'a','expiresAt':2000}),saves[0],api)
            self.assertEqual(len(api.events),1);self.assertEqual(len([c for c in api.calls if c[0]=='insert']),1)

    def test_pending_absent_insert_that_has_expired_is_preserved_without_creation(self):
        api,mapping,saves=self.managed();eid=mapping['private-a']['event_id'];api.events.clear();api.calls=[]
        self.conflict(reading({'id':'private-a','expiresAt':500}),saves[0],api)
        self.assertEqual(api.calls,[('get',eid)])

    def test_lost_update_response_preserves_old_etag_and_reports_on_restart(self):
        api,mapping,_=self.managed();original=api.update
        def update(eid,body,*,etag):
            original(eid,body,etag=etag)
            raise RuntimeError('offline')
        snap=reading({'id':'private-a','expiresAt':3000})
        with patch.object(api,'update',side_effect=update):
            with self.assertRaises(RuntimeError):self.run_sync(snap,mapping,api)
        self.assertEqual(mapping['private-a']['etag'],'"1"');self.conflict(snap,mapping,api)

    def test_user_edits_to_any_event_content_are_not_overwritten(self):
        for field,value in (('summary','My title'),('start',{'dateTime':'2030-01-01T00:00:00Z'}),('reminders',{'useDefault':True}),('description','My notes')):
            for snap in (reading(),reading({'id':'private-a','expiresAt':3000})):
                api,mapping,_=self.managed();eid=mapping['private-a']['event_id']
                api.events[eid][field]=value;api.events[eid]['etag']='"edited"'
                self.conflict(snap,mapping,api)

    def test_partial_progress_is_persisted_before_later_failure(self):
        api=FakeCalendar();saves=[]
        original=api.insert
        def insert(eid,body):
            if len(api.events):raise RuntimeError('offline')
            return original(eid,body)
        with patch.object(api,'insert',side_effect=insert):
            with self.assertRaises(RuntimeError):self.run_sync(reading({'id':'a','expiresAt':2000},{'id':'b','expiresAt':3000}),{},api,saves)
        self.assertIn('etag',saves[-1]['a']);self.assertNotIn('etag',saves[-1]['b'])

    def test_invalid_success_resources_do_not_gain_saved_etag(self):
        from wuphf.google import CalendarSyncError
        for response in ({},None,{'id':'wrong','etag':'new'}):
            api=FakeCalendar();saves=[]
            with patch.object(api,'insert',return_value=response):
                with self.assertRaises(CalendarSyncError):self.run_sync(reading({'id':'a','expiresAt':2000}),{},api,saves)
            self.assertEqual(len(saves),1);self.assertNotIn('etag',saves[-1]['a'])


class CalendarTransportTests(unittest.TestCase):
    def error(self,status,reason=None):
        from io import BytesIO
        from urllib.error import HTTPError
        body=json.dumps({'error':{'errors':[{'reason':reason}]}}).encode() if reason else b'invalid'
        return HTTPError('https://example.test/secret',status,'private provider detail',{},BytesIO(body))

    def test_conditional_headers_empty_delete_and_encoded_paths(self):
        from unittest.mock import MagicMock
        from wuphf.google import GoogleCalendar
        response=MagicMock();response.__enter__.return_value.read.return_value=b''
        api=GoogleCalendar('private-token','calendar/id')
        with patch('wuphf.google.urllib.request.urlopen',return_value=response) as request:
            api.delete('abcde',etag='"saved"')
            req=request.call_args.args[0]
            self.assertEqual(req.method,'DELETE');self.assertEqual(req.get_header('If-match'),'"saved"')
            self.assertTrue(req.full_url.endswith('/calendars/calendar%2Fid/events/abcde?sendUpdates=none'))
            api.update('abcde',{'id':'abcde'},etag='"saved"')
            self.assertEqual(request.call_args.args[0].get_header('If-match'),'"saved"')
            self.assertEqual(request.call_args.args[0].method,'PUT')
            api.insert('abcde',{'id':'abcde'})
            self.assertEqual(request.call_args.args[0].method,'POST')
            self.assertIsNone(request.call_args.args[0].get_header('If-match'))

    def test_http_statuses_are_not_conflated_with_missing_events(self):
        from wuphf.google import GoogleCalendar,CalendarRequestError
        api=GoogleCalendar('token','calendar')
        for method,path,status,reason in (('GET',api.path('abcde'),404,None),('POST',api.path(),404,None),('PUT',api.path('abcde'),404,None),('GET',api.path('abcde'),410,'fullSyncRequired'),('DELETE',api.path('abcde'),410,None),('GET','/calendars/calendar',410,'deleted'),('PUT',api.path('abcde'),412,'conditionNotMet'),('GET',api.path('abcde'),403,'forbidden'),('POST',api.path(),409,'duplicate')):
            with self.subTest(method=method,status=status,reason=reason):
                with patch('wuphf.google.urllib.request.urlopen',side_effect=self.error(status,reason)):
                    with self.assertRaises(CalendarRequestError) as caught:api.request(method,path)
                self.assertEqual(caught.exception.status,status);self.assertEqual(caught.exception.reason,reason)
                self.assertNotIn('private',str(caught.exception));self.assertNotIn('secret',str(caught.exception))
        with patch('wuphf.google.urllib.request.urlopen',side_effect=self.error(410,'deleted')):
            self.assertEqual(api.get('abcde'),{'id':'abcde','status':'cancelled'})
        with patch('wuphf.google.urllib.request.urlopen',side_effect=self.error(410,'deleted')):
            api.delete('abcde',etag='"saved"')

    def test_gate_and_corrupt_mapping_precede_token_and_calendar_calls(self):
        import tempfile
        from pathlib import Path
        from wuphf import google_auth
        from wuphf.google import CalendarSyncError
        from wuphf.storage import save
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json'
            save(config,{'client_id':'public','account_fingerprint':'a'*64,'calendar_id':'owned'})
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake') as secret,patch.object(google_auth,'token_request',return_value={'access_token':'fake'}) as token,patch.object(google_auth,'create_calendar',return_value='new-calendar') as create:
                for snap in (reading({'id':'x','expiresAt':True}),reading({'id':'x','expiresAt':2000,'status':'used'}),{**reading(),'complete':False}):
                    with self.assertRaises(CalendarSyncError):google_auth.sync(snap)
                save(mapping,{'bad':None})
                with self.assertRaises(CalendarSyncError):google_auth.sync(reading())
                secret.assert_not_called();token.assert_not_called();create.assert_not_called()

    def test_malformed_local_config_and_json_never_reach_tokens(self):
        import tempfile
        from pathlib import Path
        from wuphf import google_auth
        from wuphf.storage import save
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json'
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake') as secret,patch.object(google_auth,'token_request',return_value={'access_token':'fake'}) as token,patch.object(google_auth,'create_calendar',return_value='new-calendar') as create:
                for data in ([],{'client_id':True},{'client_id':'public','calendar_id':37,'account_fingerprint':'a'*64}):
                    save(config,data)
                    with self.assertRaises(RuntimeError):google_auth.sync(reading())
                config.write_text('{broken')
                with self.assertRaises(ValueError):google_auth.sync(reading())
                save(config,{'client_id':'public','calendar_id':'owned','account_fingerprint':'a'*64})
                mapping.write_text('{broken')
                with self.assertRaises(ValueError):google_auth.sync(reading())
                secret.assert_not_called();token.assert_not_called();create.assert_not_called()

    def test_auth_persists_managed_mapping_for_real_file_restart_and_cleanup(self):
        import tempfile
        from pathlib import Path
        from wuphf import google_auth
        from wuphf.storage import save,load
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'google.json';mapping=Path(d)/'events.json';api=FakeCalendar()
            saved={'client_id':'public','calendar_id':'owned','account_fingerprint':'a'*64};save(config,saved)
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake'),patch.object(google_auth,'token_request',return_value={'access_token':'fake'}),patch.object(google_auth,'GoogleCalendar',return_value=api):
                self.assertTrue(google_auth.sync(reading({'id':'private-credit','expiresAt':20000000000})))
                persisted=load(mapping,{});entry=persisted['private-credit']
                self.assertEqual(entry['etag'],'"1"');self.assertEqual(entry['calendar_id'],'owned')
                self.assertTrue(google_auth.sync(reading({'id':'private-credit','expiresAt':20000000000})))
                self.assertEqual(load(mapping,{}),persisted)
                self.assertTrue(google_auth.sync(reading()));self.assertEqual(load(mapping,{}),{})
                self.assertEqual(load(config,{}),saved)

    def test_malformed_provider_error_keeps_typed_sanitized_status(self):
        from io import BytesIO
        from urllib.error import HTTPError
        from wuphf.google import GoogleCalendar,CalendarRequestError
        for errors in ({'private':'provider'},[None],['private'],[]):
            error=HTTPError('https://example.test/private',410,'private',{},BytesIO(json.dumps({'error':{'errors':errors}}).encode()))
            with self.subTest(errors=errors),patch('wuphf.google.urllib.request.urlopen',side_effect=error):
                with self.assertRaises(CalendarRequestError) as caught:GoogleCalendar('secret','calendar').get('abcde')
                self.assertEqual(caught.exception.status,410);self.assertIsNone(caught.exception.reason)
                self.assertNotIn('private',str(caught.exception))



class CalendarTests(unittest.TestCase):
    def test_reconcile_refuses_cross_account_and_unknown_ownership_before_writes(self):
        from wuphf.google import CalendarAccountError
        for identity in ('b'*64,None):
            with self.subTest(identity=identity):
                api=FakeCalendar();api.events['owned-by-a']=2000
                snap={'complete':True,'count':1,'account_fingerprint':identity,'credits':[{'id':'same','expiresAt':3000}]}
                with self.assertRaises(CalendarAccountError):
                    reconcile(snap,{'same':{'event_id':'owned-by-a'}},api,lambda _:None,account_fingerprint='a'*64)
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
            history={}
            save(config,saved);save(mapping,history)
            snap=reading()
            api=FakeCalendar();api.events['unrelated']=123
            with patch.object(google_auth,'GOOGLE',config),patch.object(google_auth,'MAPPING',mapping),patch.object(google_auth,'get_secret',return_value='fake'),patch.object(google_auth,'token_request',side_effect=[RuntimeError('offline'),{'access_token':'fake'}]),patch.object(google_auth,'GoogleCalendar',return_value=api),patch.object(google_auth,'create_calendar') as create:
                with self.assertRaises(RuntimeError):google_auth.sync(snap)
                self.assertEqual(load(config,{}),saved);self.assertEqual(load(mapping,{}),history)
                self.assertTrue(google_auth.sync(snap));create.assert_not_called()
            self.assertEqual(api.events,{'unrelated':123})
            self.assertEqual(load(mapping,{}),{})

    def test_oversized_expiry_is_unknown_for_calendar_sync(self):
        from wuphf.google import valid_expiry
        self.assertFalse(valid_expiry(10**1000))

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
            from wuphf.google import CalendarSyncError
            with self.assertRaises(CalendarSyncError):sync({'count':1,'complete':False,'credits':None})
            refresh.assert_not_called()
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
                    except urllib.error.HTTPError as error:responses.append(error.code);error.close()
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
