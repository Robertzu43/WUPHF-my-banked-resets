import json
import os
import tempfile
from pathlib import Path


def load(path, default):
    try:
        with open(path, encoding='utf8') as f: return json.load(f)
    except FileNotFoundError: return default
    except json.JSONDecodeError as exc: raise ValueError('Local settings or state is corrupt') from exc


def save(path, value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.wuphf-')
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w',encoding='utf8') as f:
            json.dump(value,f);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


from contextlib import contextmanager
import fcntl

@contextmanager
def check_lock(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT,0o600)
    with os.fdopen(fd,'a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('A WUPHF check is already running.') from None
        yield
