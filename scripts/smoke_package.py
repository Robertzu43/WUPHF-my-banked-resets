"""Smoke-test a package with a synthetic Codex process and isolated user home."""
import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('package',type=Path)
    package=parser.parse_args().package.resolve()
    executable=package/('WUPHF.exe' if os.name=='nt' else 'WUPHF')
    forbidden={'google-client.json','settings.json','state.json','gmail.json','google.json','google-events.json','auth.json','.env','.env.local','credentials.json','client_secret.json'}
    for path in package.rglob('*'):
        if path.name in forbidden:raise SystemExit('User configuration found in package.')
        if path.is_symlink() and not path.resolve().is_relative_to(package):
            raise SystemExit('Package contains a symlink outside the package.')
    with tempfile.TemporaryDirectory(prefix='wuphf-package-smoke-') as tmp:
        root=Path(tmp);home=root/'home';home.mkdir();bin_dir=root/'fake bin';bin_dir.mkdir()
        fake=bin_dir/'fake_codex.py';marker=root/'codex-was-run';diagnostic=root/'synthetic-child-stderr.txt'
        fake.write_text('import json,sys\nfrom pathlib import Path\nmarker=Path('+repr(str(marker))+')\nmarker.write_text("started")\nif sys.platform=="win32":\n import ctypes\n buffer=ctypes.create_unicode_buffer(32768)\n length=ctypes.windll.kernel32.GetDllDirectoryW(len(buffer),buffer)\n required=ctypes.windll.kernel32.GetDllDirectoryW(0,None)\n marker.write_text(json.dumps({"dll_directory":buffer.value,"length":length,"required":required}))\n assert length==0 and buffer.value=="", "Child inherited the frozen DLL directory"\nmarker.write_text("ok")\nfor line in sys.stdin:\n request=json.loads(line)\n if request.get("id")==1: print(json.dumps({"id":1,"result":{}}),flush=True)\n if request.get("id")==2:\n  print(json.dumps({"id":2,"result":{"rateLimitResetCredits":{"availableCount":0,"credits":[]}}}),flush=True);break\n',encoding='utf-8')
        if os.name=='nt':
            launcher=bin_dir/'codex.cmd';launcher.write_text('@"'+sys.executable+'" "'+str(fake)+'" %* 2>"'+str(diagnostic)+'"\r\n',encoding='utf-8')
            baseline=subprocess.run([sys.executable,str(fake)],input='',capture_output=True,text=True,timeout=10)
            print('Synthetic interpreter baseline:',marker.read_text() if marker.exists() else 'not started',baseline.stderr,flush=True)
            marker.unlink(missing_ok=True)
        else:
            launcher=bin_dir/'codex';launcher.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(fake))+' "$@"\n',encoding='utf-8');launcher.chmod(0o755)
        env={**os.environ,'HOME':str(home),'USERPROFILE':str(home),'PATH':str(bin_dir)+os.pathsep+os.environ.get('PATH','')}
        subprocess.run([str(executable),'--check-assets'],env=env,check=True,timeout=30)
        subprocess.run([str(executable),'--version'],env=env,check=True,timeout=30)
        try:subprocess.run([str(executable),'--background'],env=env,check=True,timeout=30)
        except (subprocess.CalledProcessError,subprocess.TimeoutExpired):
            print('Synthetic child marker:',marker.read_text() if marker.exists() else 'not started',flush=True)
            if diagnostic.exists():print('Synthetic child stderr:',diagnostic.read_text(errors='replace'),flush=True)
            raise
        state=home/'.local'/'share'/'wuphf-resets'/'state.json'
        if not marker.exists() or not json.loads(state.read_text()).get('last_check'):
            raise SystemExit('Synthetic background check did not complete.')
    print('Packaged assets and isolated background check passed.')


if __name__=='__main__':main()
