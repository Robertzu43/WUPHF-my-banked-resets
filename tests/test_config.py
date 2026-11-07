import unittest
from wuphf.config import validate

class ConfigTests(unittest.TestCase):
    def test_rejects_zero_or_negative_cadence(self):
        with self.assertRaises(ValueError): validate({'advance_days':0,'repeat_hours':1})
        with self.assertRaises(ValueError): validate({'advance_days':1,'repeat_hours':-1})
    def test_rejects_unknown_channels(self):
        with self.assertRaises(ValueError): validate({'advance_days':1,'repeat_hours':1,'channels':{'unknown':{}}})
    def test_accepts_calendar_only(self):
        validate({'advance_days':7,'repeat_hours':24,'channels':{}})

    def test_gmail_requires_one_plain_recipient_address(self):
        base={'advance_days':7,'repeat_hours':24}
        validate({**base,'channels':{'gmail':{'to':'person@example.com'}}})
        for address in ('', 'person@example.com\nBcc: other@example.com', 'one@example.com,two@example.com', 'Name <person@example.com>', 'not-an-address'):
            with self.subTest(address=address), self.assertRaises(ValueError):
                validate({**base,'channels':{'gmail':{'to':address}}})
