import tempfile, unittest
from unittest.mock import patch
from pathlib import Path
from wuphf.runner import check

class RunnerTests(unittest.TestCase):
    def test_failure_in_one_channel_does_not_stop_another(self):
        snap={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'email':{},'ntfy':{}}}
        called=[]
        def deliver(name, config, text):
            called.append(name)
            if name=='email': raise RuntimeError('failed')
        with tempfile.TemporaryDirectory() as d:
            state=check(snap,settings,Path(d)/'state.json',now=900,deliver=deliver)
            self.assertEqual(called,['email','ntfy'])
            self.assertNotIn('a:email',state['ledger'])
            self.assertEqual(state['ledger']['a:ntfy'],900)
            self.assertIn('email',state['failures'])
    def test_same_channel_not_repeated_until_due(self):
        snap={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}}
        called=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            for now in [900,910]:check(snap,settings,p,now=now,deliver=lambda *args:called.append(args))
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
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(first,settings,p,now=900,deliver=lambda *a:calls.append(a))
            state=check(new,settings,p,now=900,deliver=lambda *a:calls.append(a))
            self.assertEqual(len(calls),1)
            self.assertEqual(state['ledger']['a:ntfy'],900)
    def test_queued_new_reset_refreshes_expiry_before_retry(self):
        old={'count':0,'complete':True,'credits':[]}
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':2000}]}
        changed={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':5000}]}
        settings={'advance_days':0.0001,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        with tempfile.TemporaryDirectory() as d, patch('wuphf.runner.message',side_effect=lambda c:str(c['expiresAt'])):
            p=Path(d)/'state.json'
            check(old,settings,p,now=900,deliver=lambda *a:None)
            check(new,settings,p,now=900,deliver=lambda *a:(_ for _ in ()).throw(RuntimeError('offline')))
            check(changed,settings,p,now=901,deliver=lambda *a:calls.append(a))
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
        new={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}}};calls=[]
        def send(channel, config, text):
            calls.append(text)
            if len(calls)==1:raise RuntimeError('offline')
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'state.json'
            check(old,settings,p,now=900,deliver=send)
            state=check(new,settings,p,now=900,deliver=send)
            self.assertEqual(len(calls),1)
            self.assertEqual(len(state['new_queue']),1)
            self.assertNotIn('a:ntfy',state['ledger'])
            state=check(new,settings,p,now=901,deliver=send)
            self.assertEqual(len(calls),2)
            self.assertEqual(state['ledger']['a:ntfy'],901)
            self.assertEqual(state['new_queue'],[])
