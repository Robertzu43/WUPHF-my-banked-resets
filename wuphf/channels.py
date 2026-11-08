import json
import re
import smtplib
import ssl
import urllib.error
import urllib.parse
import urllib.request
from email.message import EmailMessage
from .i18n import translate


class ChannelError(Exception):
    pass


def telegram_chat_id(token,phrase):
    if not isinstance(token,str) or not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+',token):
        raise ChannelError('telegram_invalid')
    if not isinstance(phrase,str) or not phrase:raise ChannelError('telegram_pair_expired')
    request=urllib.request.Request('https://api.telegram.org/bot'+token+'/getUpdates',
                                   data=b'limit=100&timeout=0',method='POST')
    try:
        with urllib.request.urlopen(request,timeout=15) as response:
            body=response.read(1000001)
        if len(body)>1000000:raise ChannelError('telegram_ambiguous')
        data=json.loads(body)
        if not isinstance(data,dict):raise ChannelError('telegram_unavailable')
        if data.get('ok') is not True:
            raise ChannelError('telegram_webhook' if data.get('error_code')==409 else 'telegram_unavailable')
        updates=data.get('result')
        if not isinstance(updates,list):raise ChannelError('telegram_unavailable')
        if len(updates)>=100:raise ChannelError('telegram_ambiguous')
        ids=set()
        for update in updates:
            message=update.get('message') if isinstance(update,dict) else None
            chat=message.get('chat') if isinstance(message,dict) else None
            if isinstance(chat,dict) and chat.get('type')=='private' and message.get('text')==phrase:
                ident=chat.get('id')
                if isinstance(ident,int) and not isinstance(ident,bool) and ident>0:ids.add(str(ident))
        if len(ids)>1:raise ChannelError('telegram_ambiguous')
        if not ids:raise ChannelError('telegram_no_messages')
        return ids.pop()
    except urllib.error.HTTPError as exc:
        raise ChannelError('telegram_webhook' if exc.code==409 else 'telegram_unavailable') from None
    except ChannelError:
        raise
    except Exception:
        raise ChannelError('telegram_unavailable') from None


def send(channel, config, text):
    try:
        if channel == 'ntfy':
            url=config['url'].rstrip('/')
            parsed=urllib.parse.urlsplit(url)
            if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
                raise ChannelError('ntfy server must use an HTTPS URL without embedded credentials')
            topic=config['topic']
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',topic): raise ChannelError('Invalid ntfy topic')
            request=urllib.request.Request(url+'/'+topic, data=text.encode(), method='POST')
            if config.get('token'): request.add_header('Authorization','Bearer '+config['token'])
            with urllib.request.urlopen(request,timeout=15) as response: response.read()
        elif channel == 'telegram':
            token=config['token']
            if not re.fullmatch(r'[0-9]+:[A-Za-z0-9_-]+',token): raise ChannelError('Invalid Telegram bot token')
            payload=urllib.parse.urlencode({'chat_id':config['chat_id'],'text':text}).encode()
            request=urllib.request.Request('https://api.telegram.org/bot'+token+'/sendMessage',data=payload)
            with urllib.request.urlopen(request,timeout=15) as response: result=json.load(response)
            if not result.get('ok'): raise ChannelError('Telegram rejected the message')
        elif channel == 'email':
            msg=EmailMessage();msg['Subject']=translate('email_subject',config.get('language','en'));msg['From']=config['from'];msg['To']=config['to'];msg.set_content(text)
            with smtplib.SMTP_SSL(config['host'],int(config.get('port',465)),timeout=15,context=ssl.create_default_context()) as smtp:
                smtp.login(config['username'],config['password'])
                if smtp.send_message(msg):raise ChannelError('Email provider refused at least one recipient.')
        else:
            raise ChannelError('Unknown notification channel')
    except ChannelError: raise
    except Exception as exc:
        # Do not include exception text: URLs may contain bot tokens.
        raise ChannelError('Notification failed; check the channel settings and connection') from None
