"""Per-user background scheduling outside macOS."""
import os
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
UNITS=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'systemd'/'user'
TASK='WUPHF Banked Resets'


def _quote(value):
    value=str(value)
    if any(ord(c)<32 for c in value):raise RuntimeError('Unsupported control character in path.')
    return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'


def _run(args):
    try:return subprocess.run(args,capture_output=True,text=True).returncode==0
    except OSError:raise RuntimeError('Background scheduler is unavailable.') from None


def install():
    if sys.platform=='win32':
        command=subprocess.list2cmdline([sys.executable,str(ROOT/'start_background.py')])
        if not _run(['schtasks','/Create','/TN',TASK,'/TR',command,'/SC','MINUTE','/MO','10','/IT']):
            raise RuntimeError('Could not create the Windows task; it may already exist.')
        return
    if sys.platform!='linux':raise RuntimeError('Background installation is unsupported on this platform.')
    service=UNITS/'wuphf-resets.service';timer=UNITS/'wuphf-resets.timer'
    if service.exists() or timer.exists():raise RuntimeError('A WUPHF background job already exists.')
    UNITS.mkdir(parents=True,exist_ok=True)
    path=os.environ.get('PATH','/usr/bin:/bin')
    service_text='[Unit]\nDescription=WUPHF reset reminders\n[Service]\nType=oneshot\nWorkingDirectory='+_quote(ROOT)+'\nEnvironment='+_quote('PATH='+path)+'\nExecStart='+_quote(sys.executable)+' '+_quote(ROOT/'start_background.py')+'\n'
    timer_text='[Unit]\nDescription=Check WUPHF reset reminders\n[Timer]\nOnStartupSec=1min\nOnUnitActiveSec=10min\nAccuracySec=10s\n[Install]\nWantedBy=timers.target\n'
    created=[]
    try:
        for path,content in ((service,service_text),(timer,timer_text)):
            with path.open('x',encoding='utf-8') as f:f.write(content)
            created.append(path)
        if not _run(['systemctl','--user','daemon-reload']) or not _run(['systemctl','--user','enable','--now',timer.name]):
            raise RuntimeError('Could not enable the Linux user timer; check your user systemd session.')
    except Exception:
        for path in created:path.unlink(missing_ok=True)
        try:_run(['systemctl','--user','daemon-reload'])
        except RuntimeError:pass
        raise


def uninstall():
    if sys.platform=='win32':
        if not _run(['schtasks','/Delete','/TN',TASK,'/F']):raise RuntimeError('Could not remove the Windows task.')
        return
    if sys.platform!='linux':raise RuntimeError('Background installation is unsupported on this platform.')
    service=UNITS/'wuphf-resets.service';timer=UNITS/'wuphf-resets.timer'
    if not service.exists() and not timer.exists():return
    if not _run(['systemctl','--user','disable','--now',timer.name]):raise RuntimeError('Could not stop the Linux timer; no files were removed.')
    service.unlink(missing_ok=True);timer.unlink(missing_ok=True)
    if not _run(['systemctl','--user','daemon-reload']):raise RuntimeError('Timer removed but systemd reload failed.')
