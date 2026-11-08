import json
import math
import queue
import shutil
import subprocess
import threading


def snapshot(raw):
    if not isinstance(raw, dict):
        return {'count': None, 'credits': None, 'complete': False}
    count, rows = raw.get('availableCount'), raw.get('credits')
    valid_count = isinstance(count, int) and not isinstance(count, bool) and count >= 0
    valid_rows = isinstance(rows, list) and all(isinstance(x, dict) and isinstance(x.get('id'), str) and x['id'] for x in rows)
    complete = bool(valid_count and valid_rows and len(rows) == count and len({x['id'] for x in rows}) == count)
    return {'count': count if valid_count else None, 'credits': rows if valid_rows else None, 'complete': complete}


def compare(old, new):
    if not old or not old['complete'] or not new['complete']:
        return None
    before = {x['id'] for x in old['credits']}
    after = {x['id'] for x in new['credits']}
    return after - before, before - after


def valid_expiry(expiry):
    return (isinstance(expiry, (int, float)) and not isinstance(expiry, bool)
            and math.isfinite(expiry) and 0 <= expiry <= 253402300739)


def due(credit, now, advance, repeat, last):
    expiry = credit.get('expiresAt')
    return (valid_expiry(expiry) and now < expiry and now >= expiry - advance
            and (last is None or now - last >= repeat))


def read_snapshot(timeout=20):
    p = subprocess.Popen([shutil.which('codex') or 'codex', 'app-server'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
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
        while True:
            value = messages.get(timeout=timeout)
            if 'error' in value and value.get('id') in (None, number):
                raise RuntimeError('Codex could not read account limits; check your sign-in.')
            if value.get('id') == number:
                return value.get('result', {})
    try:
        send({'id':1,'method':'initialize','params':{'clientInfo':{'name':'wuphf_resets','title':'WUPHF My Resets','version':'0.1.0'}}})
        response(1)
        send({'method':'initialized','params':{}})
        send({'id':2,'method':'account/rateLimits/read'})
        return snapshot(response(2).get('rateLimitResetCredits'))
    except queue.Empty as exc:
        raise RuntimeError('Codex account check timed out.') from exc
    finally:
        p.terminate()
        try: p.wait(timeout=5)
        except subprocess.TimeoutExpired: p.kill(); p.wait()
