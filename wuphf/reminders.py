import datetime
import hashlib
import math
from .core import due


def pending(snap, channels, ledger, now, advance, repeat):
    result=[]
    for credit in snap.get('credits') or []:
        if credit.get('status', 'available') != 'available': continue
        for channel in channels:
            if due(credit, now, advance, repeat, ledger.get(credit['id'] + ':' + channel)):
                result.append((credit, channel))
    return result


def message(credit):
    expiry=datetime.datetime.fromtimestamp(credit['expiresAt']).astimezone()
    return 'WUPHF! Your Codex banked reset expires ' + expiry.strftime('%B %d, %Y at %I:%M %p %Z') + '. Open Codex Usage to review it.'


def ics(snap):
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//WUPHF//Reset reminders//EN','CALSCALE:GREGORIAN','X-WR-CALNAME:WUPHF reset snapshot']
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for row in snap.get('credits') or []:
        if row.get('status','available') != 'available': continue
        expiry=row.get('expiresAt')
        if not isinstance(expiry,(int,float)) or isinstance(expiry,bool) or not math.isfinite(expiry) or expiry > 253402300739 or expiry <= datetime.datetime.now().timestamp(): continue
        stamp=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        end=datetime.datetime.fromtimestamp(expiry+60,datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        uid=hashlib.sha256(row['id'].encode()).hexdigest()+'@wuphf'
        lines += ['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+now,'DTSTART:'+stamp,'DTEND:'+end,'SUMMARY:Codex banked reset expires','DESCRIPTION:Snapshot only; this event does not update automatically.','BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY','DESCRIPTION:Codex banked reset expires soon','END:VALARM','END:VEVENT']
    return ('\r\n'.join(lines+['END:VCALENDAR',''])).encode()
