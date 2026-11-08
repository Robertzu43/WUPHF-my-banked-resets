"""Local setup UI. Bound to loopback with a per-run session and same-origin POSTs."""
import datetime
import hmac
import json
import math
import secrets
import threading
import time
import urllib.parse
import webbrowser
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import cli
from .config import validate
from .core import read_snapshot
from .keychain import set_secret
from .storage import load, save, check_lock
from .reminders import ics
from .i18n import languages, _all, translate

PAGE=Path(__file__).with_name('web.html')
PIXEL_FONT=Path(__file__).with_name('assets')/'geist-pixel-square.woff2'
FIELDS={'telegram':{'chat_id','token'},'email':{'host','port','username','from','to','password'},'ntfy':{'url','topic','token'},'gmail':{'to'}}


def clean_settings(payload):
    if not isinstance(payload,dict) or not isinstance(payload.get('channels'),dict): raise ValueError('Invalid settings')
    raw=payload['channels']; channels={}; secret_values=[]
    for name,values in raw.items():
        if name not in FIELDS or not isinstance(values,dict) or set(values)-FIELDS[name]: raise ValueError('Invalid channel settings')
        entry={}
        for key,value in values.items():
            if not isinstance(value,(str,int)) or isinstance(value,bool) or len(str(value))>2048: raise ValueError('Invalid channel value')
            if key in cli.SECRET_FIELDS[name]:
                if value: secret_values.append((name+'.'+key,str(value)))
            else: entry[key]=value
        channels[name]=entry
    settings={'advance_days':payload.get('advance_days'),'repeat_hours':payload.get('repeat_hours'),'channels':channels,'language':payload.get('language',load(cli.SETTINGS,{}).get('language','en'))}
    validate(settings)
    for name,value in secret_values: set_secret(name,value)
    return settings


def safe_status():
    old=load(cli.STATE,{})
    snap=read_snapshot()
    entries=[]
    for c in snap.get('credits') or []:
        expiry=c.get('expiresAt'); local=None
        if isinstance(expiry,(int,float)) and not isinstance(expiry,bool):
            try: local=datetime.datetime.fromtimestamp(expiry).astimezone().isoformat()
            except (OverflowError,ValueError,OSError): pass
        entries.append({'status':c.get('status'),'expires':local})
    return {'count':snap['count'],'complete':snap['complete'],'credits':entries,'last_check':old.get('last_check'),'last_error':old.get('last_error'),'failures':list(old.get('failures',{}))}


def background_check_status(state,now=None):
    last=state.get('last_check')
    if last is None:return 'never'
    if not isinstance(last,(int,float)) or isinstance(last,bool) or not math.isfinite(last):return 'unknown'
    age=(time.time() if now is None else now)-last
    if age<0:return 'unknown'
    return 'stale' if age>1800 else 'recent'


def create_server(port=0,token=None):
    token=token or secrets.token_urlsafe(32)
    pairing={};pair_lock=threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def write(self,status,body,content='application/json',headers=None):
            if isinstance(body,dict):body=json.dumps(body).encode()
            self.send_response(status);self.send_header('Content-Type',content);self.send_header('Content-Length',str(len(body)))
            self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('Referrer-Policy','no-referrer');self.send_header('Content-Security-Policy',"default-src 'self'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            for k,v in (headers or {}).items():self.send_header(k,v)
            self.end_headers();self.wfile.write(body)
        def valid_host(self):return self.headers.get('Host')==f'127.0.0.1:{self.server.server_port}'
        def authorized(self):
            try:
                cookie=SimpleCookie();cookie.load(self.headers.get('Cookie',''));value=cookie.get('wuphf_session')
                return bool(value and hmac.compare_digest(value.value,token))
            except Exception:return False
        def reject_post(self):
            lengths=self.headers.get_all('Content-Length',[])
            if (not self.headers.get('Transfer-Encoding') and len(lengths)==1 and
                    lengths[0].isascii() and lengths[0].isdigit() and len(lengths[0])<=5 and int(lengths[0])<=16384):
                remaining=int(lengths[0]);deadline=time.monotonic()+0.25
                timeout=self.connection.gettimeout()
                try:
                    while remaining:
                        wait=deadline-time.monotonic()
                        if wait<=0:break
                        self.connection.settimeout(wait)
                        chunk=self.rfile.read1(min(remaining,4096))
                        if not chunk:break
                        remaining-=len(chunk)
                except OSError:pass
                finally:self.connection.settimeout(timeout)
            self.close_connection=True
            return self.write(403,{'error':'Forbidden'})
        def do_GET(self):
            if not self.valid_host():return self.write(403,{'error':'Forbidden'})
            url=urllib.parse.urlsplit(self.path)
            if url.path=='/' and hmac.compare_digest(urllib.parse.parse_qs(url.query).get('token',[''])[0],token):
                return self.write(303,b'',headers={'Set-Cookie':f'wuphf_session={token}; HttpOnly; SameSite=Strict; Path=/','Location':'/'})
            if not self.authorized():return self.write(403,{'error':'Forbidden'})
            try:
                if url.path=='/':return self.write(200,PAGE.read_bytes().replace(b'__CSRF_TOKEN__',token.encode()),'text/html; charset=utf-8')
                if url.path=='/assets/geist-pixel-square.woff2':return self.write(200,PIXEL_FONT.read_bytes(),'font/woff2')
                if url.path=='/api/settings':return self.write(200,load(cli.SETTINGS,{'advance_days':7,'repeat_hours':24,'channels':{}}))
                if url.path=='/api/translations':return self.write(200,_all())
                if url.path=='/api/background':
                    from .platform_jobs import monitoring_status
                    state=load(cli.STATE,{})
                    last=state.get('last_check')
                    if not isinstance(last,(int,float)) or isinstance(last,bool) or not math.isfinite(last):last=None
                    failures=state.get('failures',{})
                    failures=[name for name in failures if name in ('gmail','email','telegram','ntfy','google')] if isinstance(failures,dict) else []
                    return self.write(200,{'scheduler':monitoring_status(),'last_check':last,'check_status':background_check_status(state),'last_error':bool(state.get('last_error')),'failures':failures})
                if url.path=='/api/status':return self.write(200,safe_status())
                if url.path=='/api/google/status':
                    from . import google_auth
                    info=dict(google_auth.status)
                    if info['state']=='disconnected' and load(google_auth.GOOGLE,{}).get('client_id'):info={'state':'saved','message':'Google authorization is saved. Sync to verify it still works.'}
                    return self.write(200,info)
                if url.path=='/api/gmail/status':
                    from . import gmail_auth
                    info=dict(gmail_auth.status)
                    if info.get('state')=='disconnected' and gmail_auth.connected():info={'state':'saved','message':'Gmail authorization is saved.'}
                    return self.write(200,info)
                if url.path=='/api/calendar':
                    snap=read_snapshot()
                    if not snap['complete']:return self.write(409,{'error':translate('api_incomplete_error',load(cli.SETTINGS,{}).get('language','en'))})
                    return self.write(200,ics(snap,load(cli.SETTINGS,{}).get('language','en')),'text/calendar; charset=utf-8',{'Content-Disposition':'attachment; filename="wuphf-resets.ics"'})
                return self.write(404,{'error':'Not found'})
            except Exception:return self.write(503,{'error':'Could not check Codex. Verify sign-in and connection.'})
        def do_POST(self):
            origin=f'http://127.0.0.1:{self.server.server_port}'
            if not self.valid_host() or not self.authorized() or self.headers.get('Origin')!=origin or not hmac.compare_digest(self.headers.get('X-WUPHF-Token',''),token):return self.reject_post()
            try:
                length=int(self.headers.get('Content-Length','0'))
                if length<0 or length>16384:raise ValueError('Request too large')
                payload=json.loads(self.rfile.read(length) or b'{}')
                if self.path=='/api/settings':save(cli.SETTINGS,clean_settings(payload))
                elif self.path=='/api/language':
                    language=payload.get('language')
                    if language not in languages():raise ValueError('Unknown language')
                    settings=load(cli.SETTINGS,{'advance_days':7,'repeat_hours':24,'channels':{}})
                    settings['language']=language;validate(settings);save(cli.SETTINGS,settings)
                elif self.path=='/api/test':
                    name=payload.get('channel');settings=load(cli.SETTINGS,{})
                    if name not in settings.get('channels',{}):raise ValueError('Save this channel first')
                    cli.send_with_secrets(name,{**settings['channels'][name],'language':settings.get('language','en')},translate('test_message',settings.get('language','en')))
                elif self.path=='/api/telegram/pair':
                    with pair_lock:
                        pairing.update(phrase='WUPHF-'+secrets.token_urlsafe(16),expires=time.monotonic()+600)
                        phrase=pairing['phrase']
                    return self.write(200,{'phrase':phrase})
                elif self.path=='/api/telegram/discover':
                    from .channels import telegram_chat_id, ChannelError
                    supplied=payload.get('token','')
                    if not isinstance(supplied,str) or len(supplied)>2048:raise ValueError('Invalid token')
                    with pair_lock:
                        if not pairing or time.monotonic()>=pairing['expires']:
                            return self.write(400,{'error':'telegram_pair_expired'})
                        phrase=pairing['phrase']
                    try:chat_id=telegram_chat_id(supplied or cli.get_secret('telegram.token'),phrase)
                    except ChannelError as exc:
                        code=str(exc)
                        if code not in ('telegram_invalid','telegram_no_messages','telegram_ambiguous','telegram_webhook','telegram_unavailable','telegram_pair_expired'):code='telegram_unavailable'
                        return self.write(400,{'error':code})
                    with pair_lock:
                        if not pairing or pairing['phrase']!=phrase or time.monotonic()>=pairing['expires']:
                            return self.write(400,{'error':'telegram_pair_expired'})
                        pairing.clear()
                    return self.write(200,{'chat_id':chat_id})
                elif self.path=='/api/gmail/connect':
                    from . import gmail_auth
                    gmail_auth.start_connect(payload)
                elif self.path=='/api/gmail/disconnect':
                    from . import gmail_auth
                    with check_lock(cli.DATA/'check.lock'):gmail_auth.disconnect()
                elif self.path=='/api/google/connect':
                    from . import google_auth
                    google_auth.start_connect(payload)
                elif self.path=='/api/google/disconnect':
                    from . import google_auth
                    with check_lock(cli.DATA/'check.lock'):google_auth.disconnect()
                elif self.path=='/api/google/sync':
                    from . import google_auth
                    with check_lock(cli.DATA/'check.lock'):
                        if not google_auth.sync(read_snapshot()):raise ValueError('Complete Codex data and a Google connection are required')
                elif self.path=='/api/install':cli.install_agent()
                elif self.path=='/api/uninstall':cli.main(['uninstall'])
                else:return self.write(404,{'error':'Not found'})
                return self.write(200,{'ok':True})
            except (ValueError,KeyError,TypeError):
                message='This build needs a Google desktop OAuth client in Developer setup before it can connect.' if self.path in ('/api/google/connect','/api/gmail/connect') else 'Please check your settings and try again.'
                return self.write(400,{'error':message})
            except Exception:return self.write(503,{'error':'Action failed. Check your settings, permissions, and connection.'})
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True
    server.session_token=token
    return server


def main():
    server=create_server();url=f'http://127.0.0.1:{server.server_port}/?token={server.session_token}'
    print('WUPHF setup is open in your browser. Keep this window open; press Ctrl+C to close.')
    webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
