"""Interactive Google OAuth; credentials remain local to the user's machine."""
import base64
import hashlib
import json
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from . import cli
from .google import SCOPE, GoogleCalendar, create_calendar, reconcile, token_request
from .keychain import get_secret,set_secret,delete_secret
from .storage import load,save

BUNDLED_CLIENT=cli.ROOT/'google-client.json'
GOOGLE=cli.DATA/'google.json'
MAPPING=cli.DATA/'google-events.json'
status={'state':'disconnected','message':'Not connected'}
_lock=threading.Lock()


def parse_client(raw):
    data=raw.get('installed') if isinstance(raw,dict) else None
    if not isinstance(data,dict):raise ValueError('A Google desktop OAuth JSON file is required')
    ident,secret=data.get('client_id'),data.get('client_secret')
    if not isinstance(ident,str) or not ident.endswith('.apps.googleusercontent.com') or not isinstance(secret,str) or not secret:raise ValueError('Invalid desktop OAuth client file')
    return ident,secret


def start_connect(raw):
    if not raw:raw=load(BUNDLED_CLIENT,{})
    ident,secret=parse_client(raw)
    if load(GOOGLE,{}).get('client_id'):raise RuntimeError('A Google account is already connected.')
    with _lock:
        if status['state']=='connecting':raise RuntimeError('Google sign-in already in progress')
        status.update(state='connecting',message='Complete Google authorization in your browser.')
    threading.Thread(target=_connect,args=(ident,secret),daemon=True).start()


def _connect(ident,secret):
    state=secrets.token_urlsafe(32);verifier=secrets.token_urlsafe(48)
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    result={}
    class Callback(BaseHTTPRequestHandler):
        def log_message(self,*args):pass
        def do_GET(self):
            parsed=urllib.parse.urlsplit(self.path)
            values=urllib.parse.parse_qs(parsed.query)
            if parsed.path!='/oauth/callback' or values.get('state',[''])[0]!=state:
                self.send_error(400);return
            result.update({k:v[0] for k,v in values.items()})
            body=b'Google authorization response received. Return to WUPHF.'
            self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    server=None
    try:
        server=HTTPServer(('127.0.0.1',0),Callback);server.timeout=180
        redirect=f'http://127.0.0.1:{server.server_port}/oauth/callback'
        query={'client_id':ident,'redirect_uri':redirect,'response_type':'code','scope':SCOPE,'access_type':'offline','prompt':'consent','state':state,'code_challenge':challenge,'code_challenge_method':'S256'}
        webbrowser.open('https://accounts.google.com/o/oauth2/v2/auth?'+urllib.parse.urlencode(query))
        server.handle_request()
        if result.get('error') or not result.get('code'):raise RuntimeError('Google authorization was declined or timed out.')
        data=token_request({'client_id':ident,'client_secret':secret,'code':result['code'],'code_verifier':verifier,'redirect_uri':redirect,'grant_type':'authorization_code'})
        if not data.get('refresh_token'):raise RuntimeError('Google did not issue a refresh token; reconnect and allow access.')
        set_secret('google.client_secret',secret);set_secret('google.refresh_token',data['refresh_token'])
        save(GOOGLE,{'client_id':ident})
        status.update(state='connected',message='Google connected. WUPHF will sync on the next check.')
    except Exception:
        status.update(state='error',message='Google connection did not complete. Check the OAuth client and consent settings.')
    finally:
        if server:server.server_close()


def connected():
    data=load(GOOGLE,{})
    return bool(data.get('client_id') and get_secret('google.refresh_token') and get_secret('google.client_secret'))


def sync(snap):
    if not snap.get('complete'):return False
    config=load(GOOGLE,{})
    if not config.get('client_id'):return False
    secret=get_secret('google.client_secret');refresh=get_secret('google.refresh_token')
    if not secret or not refresh:raise RuntimeError('Google Calendar credentials are missing.')
    tokens=token_request({'client_id':config['client_id'],'client_secret':secret,'refresh_token':refresh,'grant_type':'refresh_token'})
    access=tokens.get('access_token')
    if not access:raise RuntimeError('Google did not return an access token.')
    language=load(cli.SETTINGS,{}).get('language','en')
    if not config.get('calendar_id'):
        config['calendar_id']=create_calendar(access,language);save(GOOGLE,config)
    api=GoogleCalendar(access,config['calendar_id'],language);mapping=load(MAPPING,{})
    reconcile(snap,mapping,api,lambda m:save(MAPPING,m))
    return True


def disconnect():
    with _lock:
        if status['state']=='connecting':raise RuntimeError('Wait for sign-in to finish.')
        delete_secret('google.refresh_token')
        delete_secret('google.client_secret')
        GOOGLE.unlink(missing_ok=True)
        MAPPING.unlink(missing_ok=True)
        status.update(state='disconnected',message='Disconnected locally. Existing Google calendar was not removed.')
