import argparse
import datetime
import getpass
import time
import os
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

from .channels import send, ChannelError
from .config import validate
from .core import read_snapshot
from .keychain import get_secret, set_secret
from .reminders import ics
from .i18n import translate
from .google import CalendarSyncError
from .runner import check
from .storage import load, save, check_lock

ROOT=Path(__file__).resolve().parent.parent
DATA=Path.home()/'.local'/'share'/'wuphf-resets'
SETTINGS=DATA/'settings.json'
STATE=DATA/'state.json'
PLIST=Path.home()/'Library'/'LaunchAgents'/'com.wuphf.resets.plist'
SECRET_FIELDS={'telegram':['token'], 'email':['password'], 'ntfy':['token'], 'gmail':[]}


def prompt(label, default=''):
    value=input(f'{label}' + (f' [{default}]' if default else '') + ': ').strip()
    return value or default


def configure():
    settings=load(SETTINGS,{'advance_days':7,'repeat_hours':24,'channels':{}})
    settings['advance_days']=float(prompt('Start reminding this many days before expiry',str(settings['advance_days'])))
    settings['repeat_hours']=float(prompt('Repeat every how many hours',str(settings['repeat_hours'])))
    channels={}
    available=('telegram','email')+(('ntfy',) if 'ntfy' in settings['channels'] else ())+('gmail',)
    for channel in available:
        enabled=prompt('Enable '+channel+'? (y/n)','y' if channel in settings['channels'] else 'n').lower()=='y'
        if not enabled: continue
        old=settings['channels'].get(channel,{})
        if channel=='gmail':
            channels[channel]={'to':prompt('Gmail recipient address',old.get('to',''))}
            continue
        if channel=='telegram':
            data={'chat_id':prompt('Telegram chat ID',old.get('chat_id',''))};secret='token'
            text='Telegram bot token'
        elif channel=='email':
            data={'host':prompt('SMTP server',old.get('host','smtp.gmail.com')),'port':int(prompt('SMTP SSL port',str(old.get('port',465)))), 'username':prompt('SMTP username',old.get('username','')), 'from':prompt('From email',old.get('from','')), 'to':prompt('To email',old.get('to',''))};secret='password';text='SMTP app password'
        else:
            data={'url':prompt('ntfy HTTPS server',old.get('url','https://ntfy.sh')),'topic':prompt('ntfy topic',old.get('topic',''))};secret='token';text='ntfy access token (optional)'
        value=getpass.getpass(text+' (blank to keep existing): ')
        if value: set_secret(channel+'.'+secret,value)
        channels[channel]=data
    settings['channels']=channels;validate(settings);save(SETTINGS,settings)
    print('Settings saved. Use test CHANNEL to check each enabled channel.')


def send_with_secrets(name, config, text):
    if name=='gmail':
        from . import gmail_auth
        gmail_auth.send(config['to'],config['to'],text,config.get('language','en'))
        return
    item=dict(config)
    for field in SECRET_FIELDS[name]:
        value=get_secret(name+'.'+field)
        if value: item[field]=value
    send(name,item,text)


class ProtectedMacLocation(RuntimeError):
    pass


def install_agent():
    codex=shutil.which('codex')
    if not codex: raise RuntimeError('Codex CLI was not found in PATH.')
    if sys.platform!='darwin':
        from . import platform_jobs
        platform_jobs.install()
        print('Background job installed. Keep your computer awake, online, and logged in.')
        return
    if PLIST.exists(): raise RuntimeError('Background job is already installed; uninstall before reinstalling.')
    frozen=getattr(sys,'frozen',False)
    arguments=[sys.executable,'--background'] if frozen else [sys.executable,'-m','wuphf.cli','run']
    directory=Path(sys.executable).parent if frozen else ROOT
    folders=[(Path.home()/name).absolute() for name in ('Documents','Desktop','Downloads')]
    protected=folders+[folder.resolve() for folder in folders]
    locations=[directory.absolute(),Path(sys.executable).absolute(),Path(codex).absolute()]
    paths=locations+[path.resolve() for path in locations]
    # macOS privacy rules can also block other locations; status still needs monitoring.
    if any(path==folder or folder in path.parents for path in paths for folder in protected):
        raise ProtectedMacLocation('Move WUPHF and its Python environment out of Documents, Desktop, or Downloads, for example to ~/Library/Application Support/WUPHF. If Codex is in one of these folders, move or reinstall it elsewhere. Reopen WUPHF and enable checks again.')
    PLIST.parent.mkdir(parents=True,exist_ok=True)
    job={'Label':'com.wuphf.resets','ProgramArguments':arguments,'WorkingDirectory':str(directory),'RunAtLoad':True,'StartInterval':600,'EnvironmentVariables':{'PATH':os.environ.get('PATH','/usr/bin:/bin')}}
    with open(PLIST,'wb') as f: plistlib.dump(job,f)
    os.chmod(PLIST,0o600)
    try:
        result=subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(PLIST)],capture_output=True,text=True)
        if result.returncode:raise RuntimeError('Could not start the background job; it may already be installed.')
    except (OSError,RuntimeError):
        PLIST.unlink(missing_ok=True)
        raise RuntimeError('Could not start the background job; it may already be installed.') from None
    print('Background job installed. Keep your Mac awake, online, and logged in.')


def main(argv=None):
    parser=argparse.ArgumentParser(prog='wuphf')
    parser.add_argument('command',choices=['status','configure','test','run','export','install','uninstall'])
    parser.add_argument('argument',nargs='?')
    args=parser.parse_args(argv)
    if args.command=='status':
        previous=load(STATE,{})
        if previous.get('last_error'): print('Last background check:',previous['last_error'])
        if previous.get('last_check'): print('Last successful check:',datetime.datetime.fromtimestamp(previous['last_check']).astimezone().strftime('%Y-%m-%d %H:%M %Z'))
        s=read_snapshot();print('Available resets:',s['count'] if s['count'] is not None else 'unknown')
        if not s['complete']:print('Details are incomplete or unavailable.')
        for row in s['credits'] or []:
            expiry=row.get('expiresAt')
            print('Expires:',datetime.datetime.fromtimestamp(expiry).astimezone().strftime('%Y-%m-%d %H:%M %Z') if isinstance(expiry,(int,float)) else 'unknown')
    elif args.command=='configure':configure()
    elif args.command=='test':
        settings=load(SETTINGS,{});name=args.argument
        if name not in settings.get('channels',{}):raise ValueError('Channel is not enabled.')
        send_with_secrets(name,{**settings['channels'][name],'language':settings.get('language','en')},translate('test_message',settings.get('language','en')))
        print('Provider accepted the test. Check your device or inbox.')
    elif args.command=='run':
        DATA.mkdir(parents=True,exist_ok=True,mode=0o700)
        with check_lock(DATA/'check.lock'):
            try:
                settings=load(SETTINGS,{'advance_days':7,'repeat_hours':24,'channels':{}});validate(settings)
                snap=read_snapshot()
                state=check(snap,settings,STATE,deliver=send_with_secrets)
                try:
                    from . import google_auth
                    synced=google_auth.sync(snap)
                    if snap.get('complete') or synced:state['failures'].pop('google',None)
                except CalendarSyncError as exc:
                    state['failures']['google']=str(exc)
                except Exception:
                    state['failures']['google']='Google Calendar sync failed; reconnect or check your connection.'
                if snap.get('complete'):state.pop('last_error',None)
                else:state['last_error']='Reset details are incomplete; background reminders are paused.'
                save(STATE,state)
            except Exception:
                # Preserve corrupt state rather than silently replacing it.
                try:
                    previous=load(STATE,{})
                    previous['last_error']='Background check failed; verify settings, sign-in and connectivity.'
                    previous['last_attempt']=time.time();previous['snapshot']=None
                    save(STATE,previous)
                except (OSError,ValueError):pass
                raise RuntimeError('Background check failed; verify settings, sign-in and connectivity.') from None
        if state['failures']:print('Some channels failed:',', '.join(state['failures']))
    elif args.command=='export':
        target=Path(args.argument or 'wuphf-resets.ics').expanduser()
        if target.exists():raise FileExistsError('Refusing to overwrite an existing file.')
        snap=read_snapshot()
        if not snap['complete']: raise ValueError('Reset details are incomplete; refresh before exporting.')
        target.write_bytes(ics(snap,load(SETTINGS,{}).get('language','en')));print('Calendar snapshot saved to',target)
    elif args.command=='install':install_agent()
    elif args.command=='uninstall':
        if sys.platform!='darwin':
            from . import platform_jobs
            platform_jobs.uninstall()
            print('Background job removed. Settings and credentials remain.')
            return
        if PLIST.exists():
            result=subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}',str(PLIST)],capture_output=True)
            if result.returncode:
                active=subprocess.run(['launchctl','print',f'gui/{os.getuid()}/com.wuphf.resets'],capture_output=True)
                if active.returncode==0 or subprocess.run(['launchctl','print',f'gui/{os.getuid()}'],capture_output=True).returncode!=0:
                    raise RuntimeError('Could not stop the background job; no files were removed.')
            PLIST.unlink();print('Background job removed. Settings and Keychain entries remain.')
        else: print('No background job installed.')

if __name__=='__main__':
    try: main()
    except (ValueError,RuntimeError,OSError,ChannelError) as exc:
        print('WUPHF:',str(exc),file=sys.stderr);sys.exit(1)
