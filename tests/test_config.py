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
