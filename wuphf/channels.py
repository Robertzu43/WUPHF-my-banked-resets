import json
import re
import smtplib
import ssl
import urllib.parse
import urllib.request
from email.message import EmailMessage


class ChannelError(Exception):
    pass


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
            msg=EmailMessage();msg['Subject']='WUPHF! Codex reset reminder';msg['From']=config['from'];msg['To']=config['to'];msg.set_content(text)
            with smtplib.SMTP_SSL(config['host'],int(config.get('port',465)),timeout=15,context=ssl.create_default_context()) as smtp:
                smtp.login(config['username'],config['password'])
                if smtp.send_message(msg):raise ChannelError('Email provider refused at least one recipient.')
        else:
            raise ChannelError('Unknown notification channel')
    except ChannelError: raise
    except Exception as exc:
        # Do not include exception text: URLs may contain bot tokens.
        raise ChannelError('Notification failed; check the channel settings and connection') from None
