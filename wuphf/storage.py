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
        if callable(getattr(os,'fchmod',None)): os.fchmod(fd,0o600)
        with os.fdopen(fd,'w',encoding='utf8') as f:
            json.dump(value,f);f.flush();os.fsync(f.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name): os.unlink(name)


from contextlib import contextmanager
try:
    import fcntl
except ImportError:
    fcntl=None
    import msvcrt

@contextmanager
def check_lock(path):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT,0o600)
    with os.fdopen(fd,'a+b') as lock:
        if fcntl is not None:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise RuntimeError('A WUPHF check is already running.') from None
        else:
            lock.seek(0,os.SEEK_END)
            if not lock.tell():lock.write(b'\0');lock.flush()
            lock.seek(0)
            try:msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
            except OSError:raise RuntimeError('A WUPHF check is already running or lock unavailable.') from None
        try:yield
        finally:
            if fcntl is None:
                lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
