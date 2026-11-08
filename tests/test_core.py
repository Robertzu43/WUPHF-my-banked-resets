import unittest
from wuphf.core import snapshot, compare, due

class TrackingTests(unittest.TestCase):
    def test_complete_only_with_unique_rows_matching_count(self):
        self.assertFalse(snapshot({'availableCount': 0, 'credits': None})['complete'])
        self.assertFalse(snapshot({'availableCount': 2, 'credits': [{'id':'a'}]})['complete'])
        self.assertFalse(snapshot({'availableCount': 2, 'credits': [{'id':'a'}, {'id':'a'}]})['complete'])
        self.assertTrue(snapshot({'availableCount': 0, 'credits': []})['complete'])
    def test_incomplete_read_never_indicates_a_removal(self):
        a=snapshot({'availableCount':1,'credits':[{'id':'a','expiresAt':200}]})
        b=snapshot({'availableCount':1,'credits':None})
        self.assertIsNone(compare(a,b))
    def test_complete_change_detects_new_and_removed(self):
        a=snapshot({'availableCount':1,'credits':[{'id':'a','expiresAt':200}]})
        b=snapshot({'availableCount':1,'credits':[{'id':'b','expiresAt':300}]})
        self.assertEqual(compare(a,b),({'b'},{'a'}))
    def test_reminders_respect_threshold_repeat_and_expiration(self):
        item={'id':'a','expiresAt':1000}
        self.assertTrue(due(item, 900, 200, 50, None))
        self.assertFalse(due(item, 900, 200, 50, 875))
        self.assertFalse(due(item, 1000, 200, 50, None))
        self.assertFalse(due({'id':'a','expiresAt':None}, 900, 200, 50, None))
        self.assertFalse(due(item, 700, 200, 50, None))
    def test_invalid_expiry_is_not_due(self):
        self.assertFalse(due({'expiresAt':float('inf')}, 900, 1000, 50, None))
        self.assertFalse(due({'expiresAt':'soon'}, 900, 1000, 50, None))

    def test_app_server_uses_resolved_codex_launcher(self):
        from unittest.mock import MagicMock, patch
        from wuphf.core import read_snapshot
        process=MagicMock()
        process.stdout=iter(['{"id":1,"result":{}}\n','{"id":2,"result":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}}\n'])
        with patch('wuphf.core.shutil.which',return_value='C:/example/codex.cmd'),patch('wuphf.core.subprocess.Popen',return_value=process) as launch:
            result=read_snapshot()
        self.assertTrue(result['complete'])
        self.assertEqual(launch.call_args.args[0],['C:/example/codex.cmd','app-server'])
