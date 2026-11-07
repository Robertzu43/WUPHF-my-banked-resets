import unittest
from wuphf.i18n import catalog, translate, languages
from wuphf.reminders import message

class LanguageTests(unittest.TestCase):
    def test_every_language_has_the_same_translation_keys(self):
        self.assertEqual(set(languages()), {'en','es','de','pt','fr','ja','ko','zh'})
        english=set(catalog('en'))
        for language in languages():
            self.assertEqual(set(catalog(language)),english,language)
            self.assertTrue(all(isinstance(value,str) and value for value in catalog(language).values()),language)
    def test_missing_language_falls_back_to_english(self):
        self.assertEqual(translate('headline','xx'),translate('headline','en'))
    def test_reminder_uses_selected_language(self):
        self.assertIn('caduca',message({'expiresAt':172800},'es').lower())
        self.assertIn('läuft',message({'expiresAt':172800},'de').lower())
        self.assertIn('expires',message({'expiresAt':172800},'xx').lower())
    def test_calendar_export_is_localized_and_utf8_lines_are_folded(self):
        from datetime import datetime, timedelta
        from wuphf.reminders import ics
        credit={'id':'a','status':'available','expiresAt':(datetime.now()+timedelta(days=3)).timestamp()}
        output=ics({'credits':[credit],'complete':True},'ja')
        self.assertIn('Codex の保存済みリセット'.encode(),output.replace(b'\r\n ',b''))
        self.assertTrue(all(len(line)<=75 for line in output.split(b'\r\n')))
    def test_spanish_email_subject_is_localized(self):
        from unittest.mock import patch,MagicMock
        from wuphf.channels import send
        smtp=MagicMock();smtp.send_message.return_value={}
        with patch('wuphf.channels.smtplib.SMTP_SSL') as connect:
            connect.return_value.__enter__.return_value=smtp
            send('email',{'host':'x','username':'x','password':'x','from':'a@example.com','to':'b@example.com','language':'es'},'hola')
        self.assertIn('guardado',str(smtp.send_message.call_args.args[0]['Subject']).lower())
    def test_placeholders_are_identical_across_catalogs(self):
        import string
        formatter=string.Formatter()
        def placeholders(text):return {name for _,name,_,_ in formatter.parse(text) if name}
        for language in languages():
            for key,english in catalog('en').items():
                self.assertEqual(placeholders(catalog(language)[key]),placeholders(english),(language,key))
    def test_notification_uses_selected_language_during_background_check(self):
        import tempfile
        from pathlib import Path
        from wuphf.runner import check
        snap={'count':1,'complete':True,'credits':[{'id':'a','status':'available','expiresAt':1000}]}
        settings={'advance_days':1,'repeat_hours':1,'channels':{'ntfy':{}},'language':'es'};sent=[]
        with tempfile.TemporaryDirectory() as d:
            check(snap,settings,Path(d)/'state.json',now=900,deliver=lambda *a:sent.append(a))
        self.assertEqual(len(sent),1)
        self.assertIn('caduca',sent[0][2].lower())
        self.assertEqual(sent[0][1]['language'],'es')
    def test_google_calendar_event_uses_selected_language(self):
        from unittest.mock import patch
        from wuphf.google import GoogleCalendar
        api=GoogleCalendar('token','calendar','es')
        with patch.object(api,'request',side_effect=[None,{'id':'abc'}]) as request:
            api.put('abc',2000)
        event=request.call_args.args[2]
        self.assertIn('guardado',event['summary'].lower())
        self.assertIn('Codex',event['description'])
    def test_ics_calendar_name_uses_selected_language(self):
        from wuphf.reminders import ics
        output=ics({'credits':[],'complete':True},'es').decode()
        self.assertIn('X-WR-CALNAME:WUPHF · reinicios guardados de Codex',output)
