"""Google Calendar access for a user-supplied desktop OAuth client."""
import base64
import datetime
import hashlib
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from .i18n import translate

SCOPE='https://www.googleapis.com/auth/calendar.app.created'
BASE='https://www.googleapis.com/calendar/v3'


def event_id(credit_id):
    return hashlib.sha256(('wuphf:'+credit_id).encode()).hexdigest()[:48]


def valid_expiry(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value) and 0<=value<=253402300739


def reconcile(snap, mapping, api, save_mapping=lambda _:None):
    mapping=dict(mapping)
    if not snap.get('complete'):return mapping
    active={x['id']:x for x in snap.get('credits') or [] if x.get('status','available')=='available'}
    for ident,credit in active.items():
        expiry=credit.get('expiresAt')
        if not valid_expiry(expiry):continue
        eid=mapping.get(ident,{}).get('event_id') or event_id(ident)
        api.put(eid,expiry)
        mapping[ident]={'event_id':eid,'expiresAt':expiry}
        save_mapping(mapping)
    # shortcut: account/workspace changes cannot be detected reliably; keep old events until stable identity is available.
    return mapping


def token_request(data):
    req=urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(req,timeout=20) as response: return json.load(response)
    except Exception:raise RuntimeError('Google authorization failed; reconnect your calendar.') from None


class GoogleCalendar:
    def __init__(self,token,calendar_id,language='en'):self.token,self.calendar_id,self.language=token,calendar_id,language
    def request(self,method,path,payload=None):
        request=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                data=response.read();return json.loads(data) if data else {}
        except urllib.error.HTTPError as exc:
            if exc.code==404 or (exc.code==410 and method in ('GET','DELETE') and '/events/' in path):return None
            raise RuntimeError('Google Calendar request failed.') from None
        except Exception:raise RuntimeError('Google Calendar request failed.') from None
    def path(self,eid=None):
        return '/calendars/'+urllib.parse.quote(self.calendar_id,safe='')+'/events'+('/'+urllib.parse.quote(eid,safe='') if eid else '')
    def put(self,eid,expiry):
        start=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc)
        end=start+datetime.timedelta(minutes=1)
        body={'id':eid,'status':'confirmed','summary':translate('calendar_summary',self.language),'description':translate('google_event_description',self.language),'start':{'dateTime':start.isoformat()},'end':{'dateTime':end.isoformat()},'reminders':{'useDefault':False,'overrides':[{'method':'popup','minutes':1440}]}}
        if self.request('GET',self.path(eid)) is None:
            if self.request('POST',self.path(),body) is None:raise RuntimeError('Could not create event.')
        else:
            if self.request('PUT',self.path(eid),body) is None:raise RuntimeError('Could not update event.')
    def delete(self,eid):self.request('DELETE',self.path(eid))


def create_calendar(token,language='en'):
    api=GoogleCalendar(token,'',language)
    data=api.request('POST','/calendars',{'summary':translate('calendar_name',language),'timeZone':'UTC'})
    if not data or not data.get('id'):raise RuntimeError('Google Calendar creation failed.')
    return data['id']
