import time
from .channels import send
from .core import compare, valid_expiry
from .reminders import message, pending
from .storage import load, save
from .i18n import translate


def check(snap, settings, state_path, now=None, deliver=send):
    now=time.time() if now is None else now
    state=load(state_path, {'ledger':{}, 'snapshot':None, 'failures':{}})
    state.setdefault('ledger',{});state['failures']={}
    language=settings.get('language','en')
    def expiry_message(credit):return message(credit) if language=='en' else message(credit,language)
    def channel_config(channel):return {**settings['channels'][channel], 'language':language}
    state.setdefault('new_queue', [])
    changes=compare(state.get('snapshot'),snap)
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
        try:
            deliver(channel, channel_config(channel), translate('reminder_new',language)+' '+(expiry_message(credit) if valid_expiry(credit.get('expiresAt')) else translate('reminder_unknown',language)))
            state['new_queue'].remove(entry)
            if valid_expiry(credit.get('expiresAt')):state['ledger'][credit['id']+':'+channel]=now
        except Exception:
            state['failures'][channel]='Delivery failed; check settings and connection.'
        save(state_path,state)

    queued={(entry['credit']['id'],entry['channel']) for entry in state['new_queue']}
    for credit, channel in pending(snap, settings.get('channels',{}), state['ledger'], now,
                                   float(settings.get('advance_days',7))*86400,
                                   float(settings.get('repeat_hours',24))*3600):
        if (credit['id'],channel) in queued:continue
        try:
            deliver(channel, channel_config(channel), expiry_message(credit))
            state['ledger'][credit['id']+':'+channel]=now
        except Exception:
            state['failures'][channel]='Delivery failed; check settings and connection.'
        save(state_path,state)
    if changes is not None:
        for credit_id in changes[1]:
            for channel in list(state['ledger']):
                if channel.startswith(credit_id+':'): del state['ledger'][channel]
    state['last_check']=now
    state['current']=snap
    save(state_path,state)
    return state
