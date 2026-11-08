"""Run only on an ephemeral Windows CI machine, never as part of unit discovery."""
import os
import subprocess
import sys
import tempfile
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from wuphf import platform_jobs
from wuphf.core import read_snapshot
from wuphf.keychain import set_secret,get_secret,delete_secret

if sys.platform!='win32':raise SystemExit('Windows CI only')

key='wuphf-ci-'+uuid.uuid4().hex
try:
    set_secret(key,'synthetic-value')
    assert get_secret(key)=='synthetic-value'
finally:
    delete_secret(key)
assert get_secret(key) is None
print('Windows Credential Manager round trip passed')

with tempfile.TemporaryDirectory(prefix='wuphf smoke ') as d:
    root=Path(d)
    helper=root/'fake_codex.py'
    helper.write_text('import json,sys\nfor line in sys.stdin:\n r=json.loads(line)\n if r.get("id")==1: print(json.dumps({"id":1,"result":{}}),flush=True)\n if r.get("id")==2:\n  print(json.dumps({"id":2,"result":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}}),flush=True);break\n',encoding='utf-8')
    (root/'codex.cmd').write_text('@"'+sys.executable+'" "'+str(helper)+'" %*\r\n',encoding='utf-8')
    old=os.environ.get('PATH','')
    try:
        os.environ['PATH']=str(root)+os.pathsep+old
        assert read_snapshot()['complete']
    finally:os.environ['PATH']=old
print('Windows Codex launcher round trip passed')

installed=False
try:
    platform_jobs.install();installed=True
    result=subprocess.run(['schtasks','/Query','/TN',platform_jobs.TASK,'/XML'],capture_output=True,text=True,check=True)
    assert result.returncode==0,'Windows task was not registered'
    task=ET.fromstring(result.stdout)
    for name in ('DisallowStartIfOnBatteries','StopIfGoingOnBatteries'):
        assert task.findtext('{*}Settings/{*}'+name)=='false',name+' must allow battery operation'
    assert task.findtext('{*}Principals/{*}Principal/{*}LogonType')=='InteractiveToken'
    assert task.findtext('{*}Triggers/*/{*}Repetition/{*}Interval')=='PT10M'
    assert task.findtext('{*}Settings/{*}WakeToRun','false')=='false'
    print('Windows Task Scheduler registration, battery settings, and interactive schedule passed')
finally:
    if installed:platform_jobs.uninstall()
