import base64
import json
import unittest
import tempfile
from pathlib import Path
import urllib.parse
import urllib.request
from email import message_from_bytes
from unittest.mock import patch

from wuphf import gmail_auth


class GmailTests(unittest.TestCase):
    def test_send_uses_gmail_send_scope_and_localized_message(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'{"id":"message-id"}'
        with patch.object(gmail_auth, 'load', return_value={'client_id': 'example.apps.googleusercontent.com'}), \
             patch.object(gmail_auth, 'get_secret', side_effect=lambda name: {'gmail.client_secret':'client-secret','gmail.refresh_token':'refresh'}[name]), \
             patch.object(gmail_auth, 'token_request', return_value={'access_token':'access'}) as refresh, \
             patch.object(gmail_auth.urllib.request, 'urlopen', return_value=Response()) as request:
            gmail_auth.send('sender@example.com', 'person@example.com', 'Reminder text', 'es')
        req=request.call_args.args[0]
        self.assertEqual(req.full_url, 'https://gmail.googleapis.com/gmail/v1/users/me/messages/send')
        self.assertEqual(req.get_header('Authorization'), 'Bearer access')
        msg=message_from_bytes(base64.urlsafe_b64decode(json.loads(req.data)['raw']))
        self.assertEqual(msg['To'], 'person@example.com')
        self.assertIn('Reminder text', msg.get_payload(decode=True).decode())
        self.assertEqual(msg['From'], 'sender@example.com')
        self.assertEqual(refresh.call_args.args[0]['grant_type'], 'refresh_token')
        self.assertEqual(gmail_auth.SCOPE, 'https://www.googleapis.com/auth/gmail.send')

    def test_disconnect_only_removes_gmail_credentials(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(gmail_auth, 'GMAIL', Path(tmp)/'gmail.json'), patch.object(gmail_auth, 'delete_secret') as delete:
            gmail_auth.disconnect()
        self.assertEqual([c.args[0] for c in delete.call_args_list], ['gmail.refresh_token', 'gmail.client_secret'])

    def test_oauth_requests_only_send_permission_and_saves_credentials(self):
        tokens = {}
        def open_browser(url):
            query=urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            self.assertEqual(query['scope'], [gmail_auth.SCOPE])
            self.assertEqual(query['code_challenge_method'], ['S256'])
            callback=query['redirect_uri'][0] + '?' + urllib.parse.urlencode({'state':query['state'][0],'code':'authorization-code'})
            import threading
            threading.Thread(target=lambda: urllib.request.urlopen(callback, timeout=2).close(), daemon=True).start()
            return True
        with tempfile.TemporaryDirectory() as tmp, patch.object(gmail_auth, 'GMAIL', Path(tmp)/'gmail.json'), \
             patch.object(gmail_auth.webbrowser, 'open', side_effect=open_browser), \
             patch.object(gmail_auth, 'token_request', return_value={'refresh_token':'secret-refresh'}), \
             patch.object(gmail_auth, 'set_secret', side_effect=lambda k,v: tokens.update({k:v})):
            gmail_auth._connect('client.apps.googleusercontent.com', 'client-secret')
            self.assertEqual(json.loads(gmail_auth.GMAIL.read_text()), {'client_id':'client.apps.googleusercontent.com'})
        self.assertEqual(tokens, {'gmail.client_secret':'client-secret','gmail.refresh_token':'secret-refresh'})
        self.assertEqual(gmail_auth.status['state'], 'connected')

    def test_invalid_callback_does_not_end_authorization(self):
        import threading
        import urllib.error
        def open_browser(url):
            query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
            redirect = query['redirect_uri'][0]
            def callbacks():
                try:
                    urllib.request.urlopen(redirect + '?state=wrong&code=bad', timeout=2).close()
                except urllib.error.HTTPError:
                    pass
                try:
                    valid = redirect + '?' + urllib.parse.urlencode({'state': query['state'][0], 'code': 'good'})
                    urllib.request.urlopen(valid, timeout=2).close()
                except (OSError, urllib.error.URLError):
                    pass
            threading.Thread(target=callbacks, daemon=True).start()
            return True
        with tempfile.TemporaryDirectory() as tmp, patch.object(gmail_auth, 'GMAIL', Path(tmp)/'gmail.json'), \
             patch.object(gmail_auth.webbrowser, 'open', side_effect=open_browser), \
             patch.object(gmail_auth, 'token_request', return_value={'refresh_token': 'refresh'}), \
             patch.object(gmail_auth, 'set_secret'):
            gmail_auth._connect('client.apps.googleusercontent.com', 'secret')
            self.assertEqual(gmail_auth.status['state'], 'connected')

    def test_oauth_deadline_does_not_reset_after_bad_requests(self):
        class Server:
            server_port = 1234
            timeouts = []
            def handle_request(self): self.timeouts.append(self.timeout)
            def server_close(self): pass
        server = Server()
        with patch.object(gmail_auth, 'HTTPServer', return_value=server), \
             patch.object(gmail_auth.webbrowser, 'open'), \
             patch.object(gmail_auth.time, 'monotonic', side_effect=[0, 100, 150, 181]):
            gmail_auth._connect('client.apps.googleusercontent.com', 'secret')
        self.assertEqual(server.timeouts, [80, 30])
        self.assertEqual(gmail_auth.status['state'], 'error')

    def test_send_rejects_missing_credentials_without_network(self):
        with patch.object(gmail_auth, 'load', return_value={}), patch.object(gmail_auth.urllib.request, 'urlopen') as network:
            with self.assertRaises(RuntimeError): gmail_auth.send('sender@example.com','person@example.com','Test')
            network.assert_not_called()

if __name__ == '__main__': unittest.main()
