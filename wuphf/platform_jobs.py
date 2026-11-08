"""Per-user background scheduling outside macOS."""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
UNITS=Path(os.environ.get('XDG_CONFIG_HOME',Path.home()/'.config'))/'systemd'/'user'
TASK='WUPHF Banked Resets'


def monitoring_status():
    try:
        def query(args):return subprocess.run(args,capture_output=True,text=True,timeout=3)
        if sys.platform=='darwin':
            domain='gui/'+str(os.getuid())
            if query(['launchctl','print',domain+'/com.wuphf.resets']).returncode==0:return 'enabled'
            return 'disabled' if query(['launchctl','print',domain]).returncode==0 else 'unknown'
        if sys.platform=='linux':
            enabled=query(['systemctl','--user','is-enabled','wuphf-resets.timer'])
            if enabled.stdout.strip()=='disabled':return 'disabled'
            if enabled.returncode!=0 or enabled.stdout.strip()!='enabled':return 'unknown'
            active=query(['systemctl','--user','is-active','wuphf-resets.timer'])
            return 'enabled' if active.returncode==0 and active.stdout.strip()=='active' else 'unknown'
        if sys.platform=='win32':
            result=query(['schtasks','/Query','/TN',TASK,'/XML'])
            if result.returncode!=0:return 'unknown'
            value=ET.fromstring(result.stdout).findtext('{*}Settings/{*}Enabled')
            return {'true':'enabled','false':'disabled'}.get((value or '').lower(),'unknown')
    except (OSError,subprocess.SubprocessError,ET.ParseError,ValueError):
        pass
    return 'unknown'


def _quote(value):
    value=str(value)
    if any(ord(c)<32 for c in value):raise RuntimeError('Unsupported control character in path.')
    return '"'+value.replace('\\','\\\\').replace('"','\\"').replace('%','%%')+'"'


def _run(args):
    try:return subprocess.run(args,capture_output=True,text=True,stdin=subprocess.DEVNULL,timeout=15).returncode==0
    except (OSError,subprocess.SubprocessError):raise RuntimeError('Background scheduler is unavailable or did not respond.') from None


def install():
    frozen=getattr(sys,'frozen',False)
    command=[sys.executable,'--background'] if frozen else [sys.executable,str(ROOT/'start_background.py')]
    if sys.platform=='win32':
        if not _run(['schtasks','/Create','/TN',TASK,'/TR',subprocess.list2cmdline(command),'/SC','MINUTE','/MO','10','/IT']):
            raise RuntimeError('Could not create the Windows task; it may already exist.')
        script=("$ErrorActionPreference='Stop';$task=Get-ScheduledTask -TaskName '"+TASK.replace("'","''")+"' -TaskPath '\\';"
                '$task.Settings.DisallowStartIfOnBatteries=$false;$task.Settings.StopIfGoingOnBatteries=$false;'
                'Set-ScheduledTask -InputObject $task | Out-Null')
        try:
            if not _run(['powershell.exe','-NoProfile','-NonInteractive','-Command',script]):
                raise RuntimeError('Could not configure the Windows task.')
        except RuntimeError:
            try:removed=_run(['schtasks','/Delete','/TN',TASK,'/F'])
            except RuntimeError:removed=False
            if not removed:raise RuntimeError('Windows battery configuration failed and the new task could not be removed; disable it in Task Scheduler.') from None
            raise RuntimeError('Windows battery configuration failed; the new task was removed.') from None
        return
    if sys.platform!='linux':raise RuntimeError('Background installation is unsupported on this platform.')
    service=UNITS/'wuphf-resets.service';timer=UNITS/'wuphf-resets.timer'
    if service.exists() or timer.exists():raise RuntimeError('A WUPHF background job already exists.')
    UNITS.mkdir(parents=True,exist_ok=True)
    path=os.environ.get('PATH','/usr/bin:/bin')
    directory=Path(sys.executable).parent if frozen else ROOT
    # The systemd ':' prefix preserves literal dollar signs in command paths.
    literal=':' if any('$' in arg for arg in command) else ''
    service_text='[Unit]\nDescription=WUPHF reset reminders\n[Service]\nType=oneshot\nWorkingDirectory='+_quote(directory)+'\nEnvironment='+_quote('PATH='+path)+'\nExecStart='+literal+' '.join(_quote(arg) for arg in command)+'\n'
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
    if not _run(['systemctl','--user','stop',service.name]):raise RuntimeError('Could not stop the running Linux check; no files were removed.')
    service.unlink(missing_ok=True);timer.unlink(missing_ok=True)
    if not _run(['systemctl','--user','daemon-reload']):raise RuntimeError('Timer removed but systemd reload failed.')
