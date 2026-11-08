import hashlib
import json
import math
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time


def valid_identity(identity):
    return isinstance(identity,str) and re.fullmatch(r'[0-9a-f]{64}',identity) is not None


def snapshot(raw, account_id=None):
    identity=None
    if isinstance(account_id,str) and account_id.strip():
        try:identity=hashlib.sha256(b'wuphf-account-v1\0'+account_id.encode('utf-8')).hexdigest()
        except UnicodeEncodeError:pass
    if not isinstance(raw, dict):
        return {'count': None, 'credits': None, 'complete': False, 'account_fingerprint':identity}
    count, rows = raw.get('availableCount'), raw.get('credits')
    valid_count = isinstance(count, int) and not isinstance(count, bool) and count >= 0
    valid_rows = isinstance(rows, list) and all(isinstance(x, dict) and isinstance(x.get('id'), str) and x['id'] for x in rows)
    complete = bool(valid_count and valid_rows and len(rows) == count and len({x['id'] for x in rows}) == count)
    return {'count': count if valid_count else None, 'credits': rows if valid_rows else None, 'complete': complete, 'account_fingerprint':identity}


def compare(old, new):
    if not old or not old['complete'] or not new['complete']:
        return None
    identity=old.get('account_fingerprint')
    if not valid_identity(identity) or identity!=new.get('account_fingerprint'):return None
    before = {x['id'] for x in old['credits']}
    after = {x['id'] for x in new['credits']}
    return after - before, before - after


def valid_expiry(expiry):
    return (isinstance(expiry, (int, float)) and not isinstance(expiry, bool)
            and 0 <= expiry <= 253402300739 and math.isfinite(expiry))


def due(credit, now, advance, repeat, last):
    expiry = credit.get('expiresAt')
    return (valid_expiry(expiry) and now < expiry and now >= expiry - advance
            and (last is None or now - last >= repeat))


def _external_environment():
    env=os.environ.copy()
    bundle=getattr(sys,'_MEIPASS',None)
    if bundle:
        root=os.path.normcase(os.path.realpath(bundle))
        def outside(value):
            path=os.path.normcase(os.path.realpath(value or os.curdir))
            try:return os.path.commonpath((root,path))!=root
            except ValueError:return True
        keys=('PATH','DYLD_LIBRARY_PATH') if sys.platform=='darwin' else ('PATH',)
        for key in keys:
            if key in env:
                entries=[item for item in env[key].split(os.pathsep) if outside(item)]
                if entries:env[key]=os.pathsep.join(entries)
                elif key=='PATH':env[key]=os.defpath
                else:env.pop(key,None)
    if sys.platform.startswith('linux'):
        if 'LD_LIBRARY_PATH_ORIG' in env:env['LD_LIBRARY_PATH']=env['LD_LIBRARY_PATH_ORIG']
        else:env.pop('LD_LIBRARY_PATH',None)
    return env


def read_snapshot(timeout=20):
    env=_external_environment() if getattr(sys,'frozen',False) else None
    launcher=shutil.which('codex',path=env.get('PATH',os.defpath)) if env is not None else shutil.which('codex')
    options={'env':env} if env is not None else {}
    p = subprocess.Popen([launcher or 'codex', 'app-server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1, **options)
    messages = queue.Queue()
    def reader():
        try:
            for line in p.stdout:
                messages.put(json.loads(line))
        except (ValueError, OSError):
            messages.put({'error': {'message': 'Invalid app-server response'}})
    threading.Thread(target=reader, daemon=True).start()
    def send(value):
        p.stdin.write(json.dumps(value) + '\n'); p.stdin.flush()
    def response(number):
        deadline=time.monotonic()+timeout
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise queue.Empty
            value = messages.get(timeout=remaining)
            if 'error' in value and value.get('id') in (None, number):
                raise RuntimeError('Codex could not read account limits; check your sign-in.')
            if value.get('id') == number:
                return value.get('result', {})
    try:
        send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'wuphf_resets','title':'WUPHF My Resets','version':'0.1.0'}}})
        response(1)
        send({'method':'initialized','params':{}})
        send({'id':2,'method':'account/rateLimits/read'})
        result=response(2)
        return snapshot(result.get('rateLimitResetCredits'),result.get('accountId'))
    except queue.Empty as exc:
        raise RuntimeError('Codex account check timed out.') from exc
    finally:
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
