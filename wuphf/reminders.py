import datetime
import hashlib
import math
from .core import due
from .i18n import translate


def pending(snap, channels, ledger, now, advance, repeat):
    if not snap.get('complete'): return []
    result=[]
    for credit in snap.get('credits') or []:
        if credit.get('status', 'available') != 'available': continue
        for channel in channels:
            if due(credit, now, advance, repeat, ledger.get(credit['id'] + ':' + channel)):
                result.append((credit, channel))
    return result


def message(credit, language="en"):
    expiry=datetime.datetime.fromtimestamp(credit['expiresAt']).astimezone()
    return translate('reminder_expiry', language, date=expiry.strftime('%Y-%m-%d %H:%M %Z'))


def _ics_escape(text):
    return text.replace('\\','\\\\').replace(';','\\;').replace(',','\\,').replace('\n','\\n')


def _ics_fold(line):
    parts=[]; current=''; size=0
    for char in line:
        n=len(char.encode('utf-8'))
        if size+n>75:
            parts.append(current);current=' ';size=1
        current+=char;size+=n
    parts.append(current)
    return '\r\n'.join(parts)


def ics(snap, language='en'):
    lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//WUPHF//Reset reminders//EN','CALSCALE:GREGORIAN','X-WR-CALNAME:'+_ics_escape(translate('calendar_name',language))]
    now=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    for row in snap.get('credits') or []:
        if row.get('status','available') != 'available': continue
        expiry=row.get('expiresAt')
        if not isinstance(expiry,(int,float)) or isinstance(expiry,bool) or not math.isfinite(expiry) or expiry > 253402300739 or expiry <= datetime.datetime.now().timestamp(): continue
        stamp=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        end=datetime.datetime.fromtimestamp(expiry+60,datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        uid=hashlib.sha256(row['id'].encode()).hexdigest()+'@wuphf'
        lines += ['BEGIN:VEVENT','UID:'+uid,'DTSTAMP:'+now,'DTSTART:'+stamp,'DTEND:'+end,'SUMMARY:'+_ics_escape(translate('calendar_summary',language)),'DESCRIPTION:'+_ics_escape(translate('calendar_description',language)),'BEGIN:VALARM','TRIGGER:-P1D','ACTION:DISPLAY','DESCRIPTION:'+_ics_escape(translate('calendar_alarm',language)),'END:VALARM','END:VEVENT']
    return ('\r\n'.join(_ics_fold(line) for line in lines+['END:VCALENDAR',''])).encode('utf-8')
