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

    def test_telegram_discovery_finds_one_private_chat_without_confirming_updates(self):
        import io,json,urllib.parse
        from wuphf import channels
        data={'ok':True,'result':[{'message':{'chat':{'id':12345,'type':'private'}}},{'message':{'chat':{'id':-55,'type':'group'}}}]}
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with patch('wuphf.channels.urllib.request.urlopen',return_value=Response(json.dumps(data).encode())) as http:
            result=getattr(channels,'telegram_chat_id',lambda token:None)('123:secret')
        self.assertEqual(result,'12345')
        req=http.call_args.args[0]
        self.assertTrue(req.full_url.endswith('/getUpdates'))
        self.assertNotIn('offset',urllib.parse.parse_qs((req.data or b'').decode()))

    def test_telegram_discovery_rejects_ambiguous_private_chats(self):
        import io,json
        from wuphf import channels
        data={'ok':True,'result':[{'message':{'chat':{'id':1,'type':'private'}}},{'message':{'chat':{'id':2,'type':'private'}}}]}
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        with patch('wuphf.channels.urllib.request.urlopen',return_value=Response(json.dumps(data).encode())):
            with self.assertRaises(Exception) as error:getattr(channels,'telegram_chat_id',lambda token:None)('123:secret')
        self.assertEqual(str(error.exception),'telegram_ambiguous')

    def test_telegram_discovery_handles_webhook_and_redacts_network_errors(self):
        from urllib.error import HTTPError
        from wuphf import channels
        with patch('wuphf.channels.urllib.request.urlopen',side_effect=HTTPError('https://private-token',409,'Conflict',{},None)):
            with self.assertRaises(Exception) as error:getattr(channels,'telegram_chat_id',lambda token:None)('123:secret')
            self.assertEqual(str(error.exception),'telegram_webhook')
            self.assertNotIn('secret',str(error.exception))
        with patch('wuphf.channels.urllib.request.urlopen',side_effect=OSError('secret token URL')):
            with self.assertRaises(Exception) as error:getattr(channels,'telegram_chat_id',lambda token:None)('123:secret')
            self.assertEqual(str(error.exception),'telegram_unavailable')
            self.assertTrue(error.exception.__suppress_context__)

    def test_telegram_discovery_requires_pending_private_message_and_rejects_truncated_results(self):
        import io,json
        from wuphf.channels import telegram_chat_id
        class Response(io.BytesIO):
            def __enter__(self):return self
            def __exit__(self,*args):self.close()
        for updates,expected in (([],'telegram_no_messages'),([{'message':{'chat':{'id':1,'type':'private'}}}]*100,'telegram_ambiguous')):
            with self.subTest(expected=expected),patch('wuphf.channels.urllib.request.urlopen',return_value=Response(json.dumps({'ok':True,'result':updates}).encode())):
                with self.assertRaises(ChannelError) as error:telegram_chat_id('123:secret')
                self.assertEqual(str(error.exception),expected)

    def test_telegram_discovery_rejects_invalid_token_without_network(self):
        from wuphf.channels import telegram_chat_id
        with patch('wuphf.channels.urllib.request.urlopen') as http:
            with self.assertRaises(ChannelError) as error:telegram_chat_id('bad secret')
            self.assertEqual(str(error.exception),'telegram_invalid')
            http.assert_not_called()
