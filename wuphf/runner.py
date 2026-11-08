import time
from .channels import send
from .core import compare, valid_expiry, valid_identity
from .reminders import message, pending
from .storage import load, save
from .i18n import translate

# Back off from ten minutes to one hour; urgent expiries can shorten the wait.
RETRY_INITIAL=600
RETRY_MAX=3600


def check(snap, settings, state_path, now=None, deliver=send):
    now=time.time() if now is None else now
    state=load(state_path, {'ledger':{}, 'snapshot':None, 'failures':{}})
    state.setdefault('ledger',{});state.setdefault('failures',{})
    state.setdefault('ledger_expiry',{})
    state.setdefault('retry',{})
    state.setdefault('new_queue', [])
    identity=snap.get('account_fingerprint')
    if not valid_identity(identity):identity=None
    if snap.get('complete'):
        if state.get('account_fingerprint')!=identity:
            state['snapshot']=None;state['new_queue']=[]
            state['ledger']={};state['ledger_expiry']={};state['retry']={}
        elif identity is None:
            # Unknown identity cannot establish new-credit continuity across checks.
            state['new_queue']=[]
            current={credit['id']+':'+channel for credit in snap.get('credits') or []
                     if credit.get('status','available')=='available' for channel in settings.get('channels',{})}
            for mapping in (state['ledger'],state['ledger_expiry']):
                for key in list(mapping):
                    if key not in current:mapping.pop(key)
        state['account_fingerprint']=identity
    failed_channels=set()
    for channel in list(state['retry']):
        if channel not in settings.get('channels',{}):del state['retry'][channel]
    for channel in list(state['failures']):
        if channel != 'google' and channel not in settings.get('channels',{}):
            del state['failures'][channel]
    language=settings.get('language','en')
    def expiry_message(credit):return message(credit) if language=='en' else message(credit,language)
    def channel_config(channel):return {**settings['channels'][channel], 'language':language}
    expiries=[c['expiresAt'] for c in snap.get('credits') or []
              if c.get('status','available')=='available' and valid_expiry(c.get('expiresAt')) and c['expiresAt']>now]
    nearest=min(expiries) if expiries else None
    def may_send(channel):
        if channel in failed_channels:return False
        next_attempt=state['retry'].get(channel,{}).get('next_attempt',0)
        return now>=next_attempt or next_attempt-now>RETRY_MAX or (nearest is not None and nearest<=next_attempt)
    def failed(channel):
        failed_channels.add(channel)
        state['failures'][channel]='Delivery failed; check settings and connection.'
        previous=state['retry'].get(channel,{}).get('delay',0)
        delay=min(RETRY_MAX,max(RETRY_INITIAL,previous*2))
        next_attempt=now+delay
        if nearest is not None:next_attempt=min(next_attempt,now+(nearest-now)/2)
        state['retry'][channel]={'delay':delay,'next_attempt':next_attempt}
    def succeeded(channel):
        state['retry'].pop(channel,None)
        state['failures'].pop(channel,None)
    previous=state.get('snapshot')
    changes=compare(previous,snap)
    # Migrate existing ledgers using the last complete snapshot, when available.
    if previous and previous.get('complete'):
        for credit in previous.get('credits') or []:
            for channel in settings.get('channels',{}):
                key=credit['id']+':'+channel
                if key in state['ledger'] and valid_expiry(credit.get('expiresAt')):
                    state['ledger_expiry'].setdefault(key,credit['expiresAt'])
    if changes is not None:
        for credit in snap.get('credits') or []:
            if credit['id'] in changes[0]:
                for channel in settings.get('channels',{}):
                    state['new_queue'].append({'credit':credit,'channel':channel})
    state['snapshot']=snap if snap.get('complete') else None
    if snap.get('complete'):
        active={credit['id']:credit for credit in snap.get('credits') or [] if credit.get('status','available')=='available'}
        refreshed=[]
        for entry in state['new_queue']:
            credit=active.get(entry['credit']['id'])
            if credit is None:continue
            expiry=credit.get('expiresAt')
            if valid_expiry(expiry) and expiry<=now:continue
            refreshed.append({'credit':credit,'channel':entry['channel']})
        state['new_queue']=refreshed
    save(state_path,state)
    for entry in list(state['new_queue']) if snap.get('complete') else []:
        channel=entry['channel']; credit=entry['credit']
        if channel not in settings.get('channels',{}):
            state['new_queue'].remove(entry); continue
        if not may_send(channel):continue
        try:
            deliver(channel, channel_config(channel), translate('reminder_new',language)+' '+(expiry_message(credit) if valid_expiry(credit.get('expiresAt')) else translate('reminder_unknown',language)))
            state['new_queue'].remove(entry)
            if valid_expiry(credit.get('expiresAt')):
                key=credit['id']+':'+channel
                state['ledger'][key]=now;state['ledger_expiry'][key]=credit['expiresAt']
            succeeded(channel)
        except Exception:
            failed(channel)
        save(state_path,state)

    queued={(entry['credit']['id'],entry['channel']) for entry in state['new_queue']}
    effective_ledger=dict(state['ledger'])
    for credit in snap.get('credits') or []:
        expiry=credit.get('expiresAt')
        for channel in settings.get('channels',{}):
            key=credit['id']+':'+channel
            previous_expiry=state['ledger_expiry'].get(key)
            if valid_expiry(expiry) and valid_expiry(previous_expiry) and expiry<previous_expiry:
                effective_ledger.pop(key,None)
    for credit, channel in pending(snap, settings.get('channels',{}), effective_ledger, now,
                                   float(settings.get('advance_days',7))*86400,
                                   float(settings.get('repeat_hours',24))*3600):
        if (credit['id'],channel) in queued or not may_send(channel):continue
        try:
            deliver(channel, channel_config(channel), expiry_message(credit))
            key=credit['id']+':'+channel
            state['ledger'][key]=now;state['ledger_expiry'][key]=credit['expiresAt']
            succeeded(channel)
        except Exception:
            failed(channel)
        save(state_path,state)
    if changes is not None:
        for credit_id in changes[1]:
            for channel in list(state['ledger']):
                if channel.startswith(credit_id+':'):
                    del state['ledger'][channel];state['ledger_expiry'].pop(channel,None)
    state['last_attempt']=now
    if snap.get('complete'):state['last_check']=now
    state['current']=snap
    save(state_path,state)
    return state
