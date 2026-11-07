import unittest
from unittest.mock import patch
from wuphf.keychain import set_secret, get_secret

class KeychainTests(unittest.TestCase):
    def test_empty_key_rejected_before_os_call(self):
        with self.assertRaises(ValueError): set_secret('', 'x')
    def test_unavailable_keychain_is_not_silently_ignored(self):
        with patch('wuphf.keychain._security', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError): get_secret('token')
