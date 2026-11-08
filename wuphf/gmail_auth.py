"""Gmail send-only OAuth for the desktop application; tokens stay local."""
import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler

from . import cli
from .google_auth import CallbackServer, parse_client, default_client
from .i18n import translate
from .keychain import get_secret, set_secret, delete_secret
from .storage import load, save

SCOPE = 'https://www.googleapis.com/auth/gmail.send'
GMAIL = cli.DATA / 'gmail.json'
status = {'state': 'disconnected', 'message': 'Not connected'}
_lock = threading.Lock()


def token_request(data):
    request = urllib.request.Request('https://oauth2.googleapis.com/token', data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.load(response)
    except Exception:
        raise RuntimeError('Gmail authorization failed; reconnect Gmail.') from None


def start_connect(raw):
    if not raw:
        raw = default_client()
    ident, secret = parse_client(raw)
    with _lock:
        if status['state'] == 'connecting':
            raise RuntimeError('Gmail sign-in already in progress.')
        if load(GMAIL, {}).get('client_id'):
            raise RuntimeError('A Gmail account is already connected.')
        status.update(state='connecting', message='Complete Gmail authorization in your browser.')
        threading.Thread(target=_connect, args=(ident, secret), daemon=True).start()


def _connect(ident, secret):
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    result = {}
    result_lock = threading.Lock()
    class Callback(BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(5)
        def log_message(self, *args): pass
        def do_GET(self):
            parsed = urllib.parse.urlsplit(self.path)
            values = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
            states, codes, errors = values.get('state', []), values.get('code', []), values.get('error', [])
            if (parsed.path != '/oauth/callback' or len(states) != 1
                    or not secrets.compare_digest(states[0].encode(), state.encode())
                    or not ((len(codes) == 1 and codes[0] and not errors) or (len(errors) == 1 and errors[0] and not codes))):
                self.send_error(400)
                return
            with result_lock:
                if result or time.monotonic() >= deadline:
                    self.send_error(400)
                    return
                result.update({k: v[0] for k, v in values.items()})
            body = b'Google authorization response received. Return to WUPHF.'
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = None
    try:
        server = CallbackServer(('127.0.0.1', 0), Callback)
        deadline = time.monotonic() + 180
        redirect = f'http://127.0.0.1:{server.server_port}/oauth/callback'
        query = {'client_id': ident, 'redirect_uri': redirect, 'response_type': 'code', 'scope': SCOPE,
                 'access_type': 'offline', 'prompt': 'consent', 'state': state,
                 'code_challenge': challenge, 'code_challenge_method': 'S256'}
        webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(query))
        while not result:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            server.timeout = min(remaining, 0.25)
            server.handle_request()
        if result.get('error') or not result.get('code'):
            raise RuntimeError('Gmail authorization was declined or timed out.')
        data = token_request({'client_id': ident, 'client_secret': secret, 'code': result['code'],
                              'code_verifier': verifier, 'redirect_uri': redirect, 'grant_type': 'authorization_code'})
        if not data.get('refresh_token'):
            raise RuntimeError('Google did not issue a Gmail refresh token.')
        set_secret('gmail.client_secret', secret)
        set_secret('gmail.refresh_token', data['refresh_token'])
        save(GMAIL, {'client_id': ident})
        status.update(state='connected', message='Gmail connected.')
    except Exception:
        status.update(state='error', message='Gmail connection failed. Check the OAuth client and consent settings.')
    finally:
        if server: server.server_close()


def connected():
    return bool(load(GMAIL, {}).get('client_id') and get_secret('gmail.refresh_token') and get_secret('gmail.client_secret'))


def disconnect():
    with _lock:
        if status['state'] == 'connecting':
            raise RuntimeError('Wait for Gmail sign-in to finish.')
        delete_secret('gmail.refresh_token')
        delete_secret('gmail.client_secret')
        GMAIL.unlink(missing_ok=True)
        status.update(state='disconnected', message='Gmail disconnected locally.')


def send(sender, recipient, text, language='en'):
    config = load(GMAIL, {})
    if not config.get('client_id'):
        raise RuntimeError('Gmail is not connected.')
    secret, refresh = get_secret('gmail.client_secret'), get_secret('gmail.refresh_token')
    if not secret or not refresh:
        raise RuntimeError('Gmail credentials are missing.')
    data = token_request({'client_id': config['client_id'], 'client_secret': secret,
                          'refresh_token': refresh, 'grant_type': 'refresh_token'})
    if not data.get('access_token'):
        raise RuntimeError('Gmail authorization failed; reconnect Gmail.')
    msg = EmailMessage()
    msg['Subject'] = translate('email_subject', language)
    msg['From'], msg['To'] = sender, recipient
    msg.set_content(text)
    payload = json.dumps({'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode()}).encode()
    request = urllib.request.Request('https://gmail.googleapis.com/gmail/v1/users/me/messages/send', data=payload,
                                     headers={'Authorization': 'Bearer ' + data['access_token'], 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            response.read()
    except Exception:
        raise RuntimeError('Gmail delivery failed; check your connection and Gmail authorization.') from None
