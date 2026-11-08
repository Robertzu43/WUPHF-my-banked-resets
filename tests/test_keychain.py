import unittest
from unittest.mock import patch
from wuphf.keychain import set_secret, get_secret

class KeychainTests(unittest.TestCase):
    def test_empty_key_rejected_before_os_call(self):
        with self.assertRaises(ValueError): set_secret('', 'x')
    def test_unavailable_keychain_is_not_silently_ignored(self):
        with patch('wuphf.keychain.sys.platform','darwin'),patch('wuphf.keychain._security', side_effect=OSError('unavailable')):
            with self.assertRaises(OSError): get_secret('token')

class CrossPlatformSecrets(unittest.TestCase):
    def test_windows_uses_native_credential_store(self):
        import sys, types
        class Backend:
            __module__='keyring.backends.Windows'
            def __init__(self): self.values={}
            def set_password(self,service,key,value): self.values[service,key]=value
            def get_password(self,service,key): return self.values.get((service,key))
            def delete_password(self,service,key): del self.values[service,key]
        Backend.__name__='WinVaultKeyring'
        backend=Backend(); fake=types.SimpleNamespace(get_keyring=lambda:backend)
        from wuphf.keychain import delete_secret
        with patch.dict(sys.modules,{'keyring':fake}),patch('wuphf.keychain.sys.platform','win32'):
            set_secret('token','sample');self.assertEqual(get_secret('token'),'sample')
            delete_secret('token');self.assertIsNone(get_secret('token'))

    def test_rejects_untrusted_plaintext_backend(self):
        import sys,types
        fake=types.SimpleNamespace(get_keyring=lambda:object())
        with patch.dict(sys.modules,{'keyring':fake}),patch('wuphf.keychain.sys.platform','linux'):
            with self.assertRaises(RuntimeError):set_secret('token','sample')
    def test_chained_keyring_uses_secret_service_not_other_backends(self):
        import sys,types
        class Secure:
            __module__='keyring.backends.SecretService'
            def __init__(self):self.value=None
            def set_password(self,service,key,value):self.value=value
        Secure.__name__='Keyring'
        class Chain:
            __module__='keyring.backends.chainer'
            def __init__(self,secure):self.backends=[object(),secure]
        Chain.__name__='ChainerBackend'
        secure=Secure();fake=types.SimpleNamespace(get_keyring=lambda:Chain(secure))
        with patch.dict(sys.modules,{'keyring':fake}),patch('wuphf.keychain.sys.platform','linux'):
            set_secret('token','sample')
        self.assertEqual(secure.value,'sample')
