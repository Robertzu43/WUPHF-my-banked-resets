import unittest
from unittest.mock import patch
from wuphf.channels import send, ChannelError

class ChannelsTests(unittest.TestCase):
    def test_ntfy_requires_https(self):
        with self.assertRaises(ChannelError):
            send('ntfy', {'url':'http://example.com','topic':'private'}, 'test')
    def test_ntfy_transmits_body_without_secret_in_url(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*a): pass
            def read(self): return b'{}'
        with patch('wuphf.channels.urllib.request.urlopen', return_value=Response()) as request:
            send('ntfy', {'url':'https://ntfy.sh','topic':'testtopic','token':'secret'}, 'hello')
            req=request.call_args.args[0]
            self.assertEqual(req.data,b'hello')
            self.assertNotIn('secret', req.full_url)
    def test_rejects_unknown_channel(self):
        with self.assertRaises(ChannelError): send('unknown', {}, 'hi')
    def test_failure_does_not_leak_telegram_token_through_exception_chain(self):
        with patch('wuphf.channels.urllib.request.urlopen', side_effect=OSError('secret token in URL')):
            try: send('telegram',{'token':'123:secret','chat_id':'1'},'test')
            except ChannelError as exc:
                self.assertIsNone(exc.__cause__)
                self.assertTrue(exc.__suppress_context__)
                self.assertNotIn('secret',str(exc))
            else: self.fail('Expected delivery failure')
    def test_telegram_sends_to_configured_chat(self):
        import io,json,urllib.parse
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self,*args): self.close()
        with patch('wuphf.channels.urllib.request.urlopen',return_value=Response(b'{"ok":true}')) as http:
            send('telegram',{'token':'123:abc','chat_id':'456'},'hello')
            body=urllib.parse.parse_qs(http.call_args.args[0].data.decode())
            self.assertEqual(body,{'chat_id':['456'],'text':['hello']})
    def test_email_addresses_and_content_are_sent_over_tls(self):
        from unittest.mock import MagicMock
        smtp=MagicMock();smtp.send_message.return_value={}
        with patch('wuphf.channels.smtplib.SMTP_SSL') as connect:
            connect.return_value.__enter__.return_value=smtp
            send('email',{'host':'smtp.example.com','port':465,'username':'me','password':'secret','from':'a@example.com','to':'b@example.com'},'hello')
            sent=smtp.send_message.call_args.args[0]
            self.assertEqual(sent['To'],'b@example.com')
            self.assertEqual(sent.get_content().strip(),'hello')
    def test_refused_email_recipient_is_a_failure_without_leaking_address(self):
        from unittest.mock import MagicMock
        smtp=MagicMock();smtp.send_message.return_value={'private@example.com':(550,b'refused')}
        with patch('wuphf.channels.smtplib.SMTP_SSL') as connect:
            connect.return_value.__enter__.return_value=smtp
            with self.assertRaises(ChannelError) as error:
                send('email',{'host':'smtp.example.com','port':465,'username':'me','password':'secret','from':'a@example.com','to':'private@example.com'},'hello')
            self.assertNotIn('private@example.com',str(error.exception))
