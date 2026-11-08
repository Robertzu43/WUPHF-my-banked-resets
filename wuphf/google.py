"""Google Calendar access through a desktop OAuth client."""
import datetime
import hashlib
import json
import re
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from .i18n import translate
from .core import valid_expiry, valid_identity

SCOPE='https://www.googleapis.com/auth/calendar.app.created'
BASE='https://www.googleapis.com/calendar/v3'


class CalendarSyncError(RuntimeError):
    def __init__(self,code):
        self.code=code
        messages={
            'calendar_identity_required':'Codex must provide a stable account identity before Calendar sync can run. Check your Codex sign-in and refresh.',
            'calendar_account_mismatch':'Reconnect Google Calendar for the current Codex account. Existing calendar events will be preserved.',
            'calendar_data_required':'Calendar sync paused. Refresh complete, valid Codex reset details and try again.',
            'calendar_event_conflict':'Calendar sync needs review. Legacy, edited or uncertain events were preserved; review them in Google Calendar. Reconnecting does not remove old events.',
        }
        super().__init__(messages[code])


class CalendarAccountError(CalendarSyncError):pass


class CalendarRequestError(RuntimeError):
    def __init__(self,status=None,reason=None):
        self.status,self.reason=status,reason
        super().__init__('Google Calendar request failed.')


def check_account(snap,account_fingerprint):
    identity=snap.get('account_fingerprint')
    if not valid_identity(identity):raise CalendarAccountError('calendar_identity_required')
    if account_fingerprint!=identity:raise CalendarAccountError('calendar_account_mismatch')


def check_data(snap):
    count,rows=snap.get('count'),snap.get('credits')
    if (snap.get('complete') is not True or not isinstance(count,int) or isinstance(count,bool) or count<0
            or not isinstance(rows,list) or len(rows)!=count
            or any(not isinstance(row,dict) or not isinstance(row.get('id'),str) or not row['id']
                   or not valid_expiry(row.get('expiresAt')) or row.get('status','available')!='available' for row in rows)):
        raise CalendarSyncError('calendar_data_required')
    if len({row['id'] for row in rows})!=count:raise CalendarSyncError('calendar_data_required')
    try:
        for row in rows:row['id'].encode('utf-8')
    except UnicodeEncodeError:raise CalendarSyncError('calendar_data_required') from None


def check_mapping(mapping,account_fingerprint,calendar_id):
    if not isinstance(mapping,dict):raise CalendarSyncError('calendar_event_conflict')
    seen=set()
    for ident,entry in mapping.items():
        if (not isinstance(ident,str) or not ident or not isinstance(entry,dict)
                or not isinstance(entry.get('event_id'),str) or not entry['event_id'] or entry['event_id'] in seen
                or ('expiresAt' in entry and not valid_expiry(entry['expiresAt']))):
            raise CalendarSyncError('calendar_event_conflict')
        seen.add(entry['event_id'])
        if any(key in entry for key in ('owner','account_fingerprint','calendar_id','etag')):
            if (not isinstance(entry.get('owner'),str) or re.fullmatch(r'[0-9a-f]{32,}',entry['owner']) is None
                    or entry.get('account_fingerprint')!=account_fingerprint or entry.get('calendar_id')!=calendar_id
                    or not isinstance(calendar_id,str) or not calendar_id
                    or re.fullmatch(r'[a-v0-9]{5,1024}',entry['event_id']) is None
                    or not valid_expiry(entry.get('expiresAt'))
                    or ('etag' in entry and (not isinstance(entry['etag'],str) or not entry['etag']))):
                raise CalendarSyncError('calendar_event_conflict')
        try:ident.encode('utf-8')
        except UnicodeEncodeError:raise CalendarSyncError('calendar_event_conflict') from None


def markers(ident,entry):
    return {'wuphfSchema':'1','wuphfOwner':entry['owner'],'wuphfAccount':entry['account_fingerprint'],
            'wuphfCredit':hashlib.sha256(b'wuphf-credit-v1\0'+ident.encode()).hexdigest()}


def event_body(ident,entry,expiry,language):
    start=datetime.datetime.fromtimestamp(expiry,datetime.timezone.utc)
    return {'id':entry['event_id'],'status':'confirmed','summary':translate('calendar_summary',language),
            'description':translate('google_event_description',language),'start':{'dateTime':start.isoformat()},
            'end':{'dateTime':(start+datetime.timedelta(minutes=1)).isoformat()},
            'reminders':{'useDefault':False,'overrides':[{'method':'popup','minutes':1440}]},
            'extendedProperties':{'private':markers(ident,entry)}}


def check_event(event,ident,entry,*,saved_etag=False):
    private=event.get('extendedProperties',{}).get('private') if isinstance(event,dict) and isinstance(event.get('extendedProperties',{}),dict) else None
    if (not isinstance(event,dict) or event.get('id')!=entry['event_id'] or event.get('status')!='confirmed'
            or not isinstance(private,dict) or any(private.get(key)!=value for key,value in markers(ident,entry).items())
            or not isinstance(event.get('etag'),str) or not event['etag']
            or (saved_etag and event['etag']!=entry.get('etag'))
            or any(not isinstance(event.get(key,[]),list) or event.get(key) for key in ('attendees','recurrence'))
            or event.get('eventType','default')!='default'):
        raise CalendarSyncError('calendar_event_conflict')
    try:
        times=[]
        for key in ('start','end'):
            value=event.get(key)
            if (not isinstance(value,dict) or 'date' in value or not isinstance(value.get('dateTime'),str)
                    or re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})',value['dateTime']) is None
                    or ('timeZone' in value and (not isinstance(value['timeZone'],str) or not value['timeZone']))):
                raise ValueError
            times.append(datetime.datetime.fromisoformat(value['dateTime'].replace('Z','+00:00')))
        if times[1]<=times[0]:raise ValueError
    except (ValueError,TypeError,OverflowError):raise CalendarSyncError('calendar_event_conflict') from None


def reconcile(snap,mapping,api,save_mapping,*,account_fingerprint=None,now=None):
    check_account(snap,account_fingerprint)
    check_data(snap)
    check_mapping(mapping,account_fingerprint,api.calendar_id)
    mapping=dict(mapping)
    active={row['id']:row for row in snap['credits']}
    now=time.time() if now is None else now
    legacy=False
    try:
        for ident in dict.fromkeys([*mapping,*active]):
            entry=mapping.get(ident);credit=active.get(ident)
            if entry and 'owner' not in entry:
                legacy=True;continue
            reserved=False
            if entry is None:
                if credit['expiresAt']<=now:continue
                entry={'event_id':secrets.token_hex(24),'expiresAt':credit['expiresAt'],'owner':secrets.token_hex(16),
                       'account_fingerprint':account_fingerprint,'calendar_id':api.calendar_id}
                mapping[ident]=entry
                save_mapping(mapping)
                reserved=True
            event=None
            if not reserved:
                try:
                    event=api.get(entry['event_id'])
                    if not isinstance(event,dict):raise CalendarSyncError('calendar_event_conflict')
                except CalendarRequestError as exc:
                    if exc.status!=404 or 'etag' in entry:raise
                    # A missing pending ID is retried only with insert; 404 never authorizes cleanup.
                if event is not None:
                    if not isinstance(event,dict) or event.get('id')!=entry['event_id']:raise CalendarSyncError('calendar_event_conflict')
                    if event.get('status')=='cancelled':
                        if credit is None:
                            del mapping[ident];save_mapping(mapping)
                        continue
                    # shortcut: a completed write with a lost local save needs manual review; never adopt its etag.
                    if 'etag' not in entry:raise CalendarSyncError('calendar_event_conflict')
                    check_event(event,ident,entry,saved_etag=True)
            if event is None:
                if credit is None or credit['expiresAt']<=now:raise CalendarSyncError('calendar_event_conflict')
                body=event_body(ident,entry,credit['expiresAt'],api.language)
                event=api.insert(entry['event_id'],body)
            elif credit is None:
                api.delete(entry['event_id'],etag=entry['etag'])
                del mapping[ident];save_mapping(mapping)
                continue
            else:
                if entry['expiresAt']==credit['expiresAt']:continue
                body=event_body(ident,entry,credit['expiresAt'],api.language)
                event=api.update(entry['event_id'],body,etag=entry['etag'])
            check_event(event,ident,entry)
            mapping[ident]={**entry,'expiresAt':credit['expiresAt'],'etag':event['etag']}
            save_mapping(mapping)
    except CalendarRequestError as exc:
        if exc.status in (404,409,412):raise CalendarSyncError('calendar_event_conflict') from None
        raise
    if legacy:raise CalendarSyncError('calendar_event_conflict')
    return mapping


def token_request(data):
    req=urllib.request.Request('https://oauth2.googleapis.com/token',data=urllib.parse.urlencode(data).encode())
    try:
        with urllib.request.urlopen(req,timeout=20) as response:return json.load(response)
    except Exception:raise RuntimeError('Google authorization failed; reconnect your calendar.') from None


class GoogleCalendar:
    def __init__(self,token,calendar_id,language='en'):self.token,self.calendar_id,self.language=token,calendar_id,language
    def request(self,method,path,payload=None,*,headers=None):
        request=urllib.request.Request(BASE+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,
                                       headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json',**(headers or {})})
        try:
            with urllib.request.urlopen(request,timeout=20) as response:
                data=response.read();return json.loads(data) if data else {}
        except urllib.error.HTTPError as exc:
            reason=None
            try:
                error=json.loads(exc.read()).get('error',{}).get('errors',[])
                if isinstance(error,list) and error and isinstance(error[0],dict) and isinstance(error[0].get('reason'),str):reason=error[0]['reason']
            except (ValueError,TypeError,AttributeError,OSError):pass
            finally:exc.close()
            raise CalendarRequestError(exc.code,reason) from None
        except Exception:raise CalendarRequestError() from None
    def path(self,eid=None):
        return '/calendars/'+urllib.parse.quote(self.calendar_id,safe='')+'/events'+('/'+urllib.parse.quote(eid,safe='') if eid else '')
    def get(self,eid):
        try:return self.request('GET',self.path(eid))
        except CalendarRequestError as exc:
            if exc.status==410 and exc.reason=='deleted':return {'id':eid,'status':'cancelled'}
            raise
    def insert(self,eid,body):return self.request('POST',self.path(),body)
    def update(self,eid,body,*,etag):return self.request('PUT',self.path(eid),body,headers={'If-Match':etag})
    def delete(self,eid,*,etag):
        try:self.request('DELETE',self.path(eid)+'?sendUpdates=none',headers={'If-Match':etag})
        except CalendarRequestError as exc:
            if exc.status!=410 or exc.reason!='deleted':raise


def create_calendar(token,language='en'):
    api=GoogleCalendar(token,'',language)
    data=api.request('POST','/calendars',{'summary':translate('calendar_name',language),'timeZone':'UTC'})
    if not isinstance(data,dict) or not isinstance(data.get('id'),str) or not data['id']:raise RuntimeError('Google Calendar creation failed.')
    return data['id']
