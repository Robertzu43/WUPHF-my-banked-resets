import tempfile, unittest
from unittest.mock import patch
from pathlib import Path
from wuphf.runner import check

class RunnerTests(unittest.TestCase):
    def test_failure_in_one_channel_does_not_stop_another(self):
        snap={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':87400}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'email':{},'ntfy':{}}}
        called=[]
        def deliver(name, config, text):
            called.append(name)
            if name=='email': raise RuntimeError('failed')
        with tempfile.TemporaryDirectory() as d:
            state=check(snap,settings,Path(d)/'state.json',now=87300,deliver=deliver)
            self.assertEqual(called,['email','ntfy'])
            self.assertNotIn('a:email',state['ledger'])
            self.assertEqual(state['ledger']['a:ntfy'],87300)
            self.assertIn('email',state['failures'])
    def test_same_channel_not_repeated_until_due(self):
        snap={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':87400}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        called=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            for now in [87300,87310]:check(snap,settings,p,now=now,deliver=lambda *args:called.append(args))
            self.assertEqual(len(called),1)
    def test_new_credit_notifies_once_without_waiting_for_expiry(self):
        first={'count':0,'complete':True,'credits':[]}
        second={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':9000000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            for s in (first,second,second):check(s,settings,p,now=900,deliver=lambda *a:calls.append(a))
            self.assertEqual(len(calls),1)
            self.assertIn('new',calls[0][2].lower())
    def test_partial_snapshot_does_not_send_expiry_reminders(self):
        partial={'count':2,'complete':False,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d:
            state=check(partial,settings,Path(d)/'state.json',now=900,deliver=lambda *args:calls.append(args))
            self.assertEqual(calls,[])
            self.assertEqual(state['ledger'],{})
    def test_failed_check_never_compares_across_incomplete_gap(self):
        old={'count':0,'complete':True,'credits':[]}
        partial={'count':1,'complete':False,'credits':None}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':9000000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}; calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            for s in (old,partial,new):check(s,settings,p,now=900,deliver=lambda *a:calls.append(a))
            self.assertEqual(calls,[])
    def test_failed_new_notification_is_dropped_if_credit_disappears(self):
        old={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':9000000}]}
        gone={'count':0,'complete':True,'credits':[]}; calls=[]
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        def fail(*a):raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(old,settings,p,now=900,deliver=fail)
            check(new,settings,p,now=900,deliver=fail)
            check(gone,settings,p,now=901,deliver=lambda *a:calls.append(a))
            self.assertEqual(calls,[])
    def test_new_reset_inside_warning_window_sends_one_message(self):
        first={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':87400}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(first,settings,p,now=87300,deliver=lambda *a:calls.append(a))
            state=check(new,settings,p,now=87300,deliver=lambda *a:calls.append(a))
            self.assertEqual(len(calls),1)
            self.assertEqual(state['ledger']['a:ntfy'],87300)
    def test_queued_new_reset_refreshes_expiry_before_retry(self):
        old={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':2000}]}
        changed={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':5000}]}
        settings={'advance_days':0.0001,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d, patch('wuphf.runner.message',side_effect=lambda c:str(c['expiresAt'])):
            p=Path(d)/'state.json'
            check(old,settings,p,now=900,deliver=lambda *a:None)
            check(new,settings,p,now=900,deliver=lambda *a:(_ for _ in ()).throw(RuntimeError('offline')))
            check(changed,settings,p,now=1450,deliver=lambda *a:calls.append(a))
            self.assertEqual(len(calls),1)
            self.assertIn('5000',calls[0][2])
            self.assertNotIn('2000',calls[0][2])
    def test_malformed_expiry_is_unknown_and_does_not_crash_queue(self):
        old={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':'unknown'}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(old,settings,p,now=900,deliver=lambda *a:None)
            check(new,settings,p,now=900,deliver=lambda *a:calls.append(a))
            self.assertEqual(len(calls),1)
            self.assertIn('Expiry is not available',calls[0][2])
    def test_failed_new_notice_suppresses_duplicate_expiry_attempt(self):
        old={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':87400}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        def send(channel, config, text):
            calls.append(text)
            if len(calls)==1:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(old,settings,p,now=87300,deliver=send)
            state=check(new,settings,p,now=87300,deliver=send)
            self.assertEqual(len(calls),1)
            self.assertEqual(len(state['new_queue']),1)
            self.assertNotIn('a:ntfy',state['ledger'])
            state=check(new,settings,p,now=87350,deliver=send)
            self.assertEqual(len(calls),2)
            self.assertEqual(state['ledger']['a:ntfy'],87350)
            self.assertEqual(state['new_queue'],[])

    def test_incomplete_snapshot_preserves_last_success_and_delivery_failure(self):
        from wuphf.storage import save
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        partial={'count':2,'complete':False,'credits':None}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            save(p,{'ledger':{},'snapshot':None,'last_check':800,'failures':{'ntfy':'Delivery failed'}})
            state=check(partial,settings,p,now=900,deliver=lambda *a:self.fail('must not send'))
            self.assertEqual(state['last_check'],800)
            self.assertEqual(state['last_attempt'],900)
            self.assertIn('ntfy',state['failures'])

    def test_earlier_expiry_retries_until_delivered_then_respects_cadence(self):
        settings={'advance_days':1,'repeat_hours':24,'channels':{'ntfy':{}}}
        initial={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':100000}]}
        changed={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':91000}]}
        attempts=[]
        def deliver(*args):
            attempts.append(args)
            if len(attempts)==2:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(initial,settings,p,now=90000,deliver=deliver)
            check(changed,settings,p,now=90001,deliver=deliver)
            state=check(changed,settings,p,now=90501,deliver=deliver)
            check(changed,settings,p,now=90502,deliver=deliver)
            self.assertEqual(len(attempts),3)
            self.assertEqual(state['ledger']['a:ntfy'],90501)
            self.assertNotIn('ntfy',state['failures'])

    def test_successful_delivery_does_not_clear_another_credit_failure(self):
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        snap={'count':2,'complete':True,'credits':[{'id':'a','expiresAt':100000},{'id':'b','expiresAt':100000}]}
        attempts=[]
        def deliver(*args):
            attempts.append(args)
            if len(attempts)==1:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            state=check(snap,settings,Path(d)/'state.json',now=90000,deliver=deliver)
            self.assertIn('ntfy',state['failures'])

    def test_existing_ledger_is_migrated_before_earlier_expiry(self):
        from wuphf.storage import save
        settings={'advance_days':1,'repeat_hours':24,'channels':{'ntfy':{}}}
        initial={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':100000}]}
        changed={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':91000}]}
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            save(p,{'ledger':{'a:ntfy':90000},'snapshot':initial,'failures':{}})
            check(changed,settings,p,now=90001,deliver=lambda *args:calls.append(args))
            self.assertEqual(len(calls),1)

    def test_later_expiry_does_not_bypass_repeat_interval(self):
        settings={'advance_days':1,'repeat_hours':24,'channels':{'ntfy':{}}}
        first={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':91000}]}
        later={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':92000}]}
        calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(first,settings,p,now=90000,deliver=lambda *args:calls.append(args))
            check(later,settings,p,now=90001,deliver=lambda *args:calls.append(args))
            self.assertEqual(len(calls),1)

    def test_channel_backoff_persists_across_checks_and_resets_after_success(self):
        now=1800000000
        snap={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':now+864000}]}
        settings={'advance_days':30,'repeat_hours':24,'channels':{'email':{},'ntfy':{}}}
        calls=[]
        def deliver(channel,config,text):
            calls.append(channel)
            if channel=='email' and calls.count('email')<3:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(snap,settings,p,now=now,deliver=deliver)
            check(snap,settings,p,now=now+599,deliver=deliver)
            self.assertEqual(calls,['email','ntfy'])
            check(snap,settings,p,now=now+600,deliver=deliver)
            check(snap,settings,p,now=now+1799,deliver=deliver)
            self.assertEqual(calls,['email','ntfy','email'])
            state=check(snap,settings,p,now=now+1800,deliver=deliver)
            self.assertEqual(calls,['email','ntfy','email','email'])
            self.assertNotIn('email',state.get('retry',{}))
            self.assertNotIn('email',state['failures'])
            self.assertIn('a:email',state['ledger'])

    def test_channel_failure_does_not_attempt_another_credit_until_retry(self):
        now=1800000000
        snap={'count':2,'complete':True,'credits':[{'id':'a','expiresAt':now+864000},{'id':'b','expiresAt':now+864000}]}
        settings={'advance_days':30,'repeat_hours':24,'channels':{'email':{},'ntfy':{}}}
        calls=[]
        def deliver(channel,config,text):
            calls.append(channel)
            if channel=='email' and calls.count('email')==1:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(snap,settings,p,now=now,deliver=deliver)
            self.assertEqual(calls,['email','ntfy','ntfy'])
            state=check(snap,settings,p,now=now+600,deliver=deliver)
            self.assertEqual(calls.count('email'),3)
            self.assertIn('a:email',state['ledger']);self.assertIn('b:email',state['ledger'])

    def test_new_urgent_expiry_shortens_existing_backoff(self):
        now=1800000000
        snap={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':now+864000}]}
        urgent={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':now+300}]}
        settings={'advance_days':30,'repeat_hours':24,'channels':{'email':{}}};calls=[]
        def fail(*args):calls.append(args);raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(snap,settings,p,now=now,deliver=fail)
            check(urgent,settings,p,now=now+100,deliver=fail)
            self.assertEqual(len(calls),2)
            state=check(urgent,settings,p,now=now+199,deliver=fail)
            self.assertEqual(len(calls),2)
            state=check(urgent,settings,p,now=now+200,deliver=fail)
            self.assertEqual(len(calls),3)

    def test_retry_delay_caps_at_one_hour(self):
        now=1800000000
        snap={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':now+864000}]}
        settings={'advance_days':30,'repeat_hours':24,'channels':{'email':{}}}
        calls=[]
        def fail(*args):calls.append(args);raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            for offset in (0,600,1800,4200,7800):state=check(snap,settings,p,now=now+offset,deliver=fail)
            self.assertEqual(len(calls),5)
            self.assertEqual(state['retry']['email']['delay'],3600)
            self.assertEqual(state['retry']['email']['next_attempt'],now+11400)
            state=check(snap,{'advance_days':30,'repeat_hours':24,'channels':{}},p,now=now+7801,deliver=fail)
            self.assertNotIn('email',state['retry'])
            self.assertNotIn('email',state['failures'])

    def test_clock_moving_back_does_not_block_retries_indefinitely(self):
        now=1800000000
        snap={'count':1,'complete':True,'credits':[{'id':'a','expiresAt':now+864000}]}
        settings={'advance_days':30,'repeat_hours':24,'channels':{'email':{}}};calls=[]
        def fail(*args):calls.append(args);raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(snap,settings,p,now=now,deliver=fail)
            check(snap,settings,p,now=now-7200,deliver=fail)
            self.assertEqual(len(calls),2)
