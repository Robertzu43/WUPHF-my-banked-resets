import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from wuphf import google_auth, gmail_auth


class PublicClientTests(unittest.TestCase):
    def test_default_client_uses_bundled_registration_without_personal_file(self):
        client={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'public-client-parameter'}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);public=root/'oauth-client.json';public.write_text(json.dumps(client))
            with patch.object(google_auth,'BUNDLED_CLIENT',root/'missing.json'),patch.object(google_auth,'PUBLIC_CLIENT',public):
                self.assertEqual(google_auth.default_client(),client)

    def test_personal_desktop_client_takes_precedence(self):
        personal={'installed':{'client_id':'own.apps.googleusercontent.com','client_secret':'own'}}
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);local=root/'google-client.json';local.write_text(json.dumps(personal))
            with patch.object(google_auth,'BUNDLED_CLIENT',local),patch.object(google_auth,'PUBLIC_CLIENT',root/'missing.json'):
                self.assertEqual(google_auth.default_client(),personal)

    def test_gmail_connect_uses_default_client_and_preserves_send_only_flow(self):
        client={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'parameter'}}
        with tempfile.TemporaryDirectory() as tmp,patch.object(gmail_auth,'GMAIL',Path(tmp)/'gmail.json'),patch.object(gmail_auth,'default_client',return_value=client),patch.object(gmail_auth.threading,'Thread') as thread:
            gmail_auth.status.update(state='disconnected',message='Not connected')
            try:
                gmail_auth.start_connect({})
                self.assertEqual(thread.call_args.kwargs['args'],('public.apps.googleusercontent.com','parameter'))
                self.assertEqual(gmail_auth.SCOPE,'https://www.googleapis.com/auth/gmail.send')
            finally:gmail_auth.status.update(state='disconnected',message='Not connected')

    def test_calendar_connect_uses_default_client(self):
        client={'installed':{'client_id':'public.apps.googleusercontent.com','client_secret':'parameter'}}
        with tempfile.TemporaryDirectory() as tmp,patch.object(google_auth,'GOOGLE',Path(tmp)/'google.json'),patch.object(google_auth,'default_client',return_value=client),patch.object(google_auth.threading,'Thread') as thread:
            google_auth.status.update(state='disconnected',message='Not connected')
            try:
                google_auth.start_connect({})
                self.assertEqual(thread.call_args.kwargs['args'],('public.apps.googleusercontent.com','parameter'))
            finally:google_auth.status.update(state='disconnected',message='Not connected')

    def test_public_registration_contains_only_app_parameters(self):
        path=Path(google_auth.__file__).with_name('oauth-client.json')
        raw=json.loads(path.read_text())
        self.assertEqual(set(raw),{'installed'})
        self.assertEqual(set(raw['installed']),{'client_id','client_secret'})
        self.assertEqual(google_auth.parse_client(raw)[0],'74953808851-v91oc6jtr86ncoi81p1g23ks84ajl3hl.apps.googleusercontent.com')
