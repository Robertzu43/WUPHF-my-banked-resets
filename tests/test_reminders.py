import unittest
from unittest.mock import patch
from wuphf.reminders import pending, ics, message

class ReminderTests(unittest.TestCase):
    def test_due_separately_for_each_channel(self):
        row={'id':'a','expiresAt':1000,'status':'available'}
        snap={'credits':[row], 'complete':True}
        sent={'a:email':880}
        reminders=pending(snap,['email','ntfy'],sent,now=900,advance=200,repeat=50)
        self.assertEqual([(x[0]['id'],x[1]) for x in reminders],[('a','ntfy')])
    def test_no_reminder_for_missing_or_expired_dates(self):
        snap={'credits':[{'id':'a','expiresAt':None},{'id':'b','expiresAt':900}], 'complete':False}
        self.assertEqual(pending(snap,['email'],{},900,200,50),[])
    def test_calendar_is_a_snapshot_with_utc_expiry_and_escapes(self):
        with patch('wuphf.reminders.datetime') as clock:
            from datetime import datetime, timezone
            clock.datetime.now.return_value=datetime(1970,1,1,tzinfo=timezone.utc)
            clock.datetime.fromtimestamp.side_effect=datetime.fromtimestamp
            clock.timezone=timezone
            data=ics({'credits':[{'id':'a','expiresAt':1000}], 'complete':True}).decode()
        self.assertIn('DTSTART:19700101T001640Z',data)
        self.assertIn('BEGIN:VEVENT',data)
        self.assertTrue(data.endswith('END:VCALENDAR\r\n'))
    def test_notification_identifies_expiry(self):
        self.assertIn('1970',message({'expiresAt':172800}))
    def test_ics_excludes_unavailable_credit(self):
        from datetime import datetime, timedelta
        t=(datetime.now()+timedelta(days=3)).timestamp()
        data=ics({'credits':[{'id':'a','expiresAt':t,'status':'used'}]}).decode()
        self.assertNotIn('BEGIN:VEVENT',data)
    def test_invalid_expiry_is_not_added_to_calendar(self):
        data=ics({'credits':[{'id':'a','expiresAt':float('inf'),'status':'available'}]}).decode()
        self.assertNotIn('BEGIN:VEVENT',data)
