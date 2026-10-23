import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import automation_notify as module
from automation_notify import Announcer, message

class NotificationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.config={'state_dir':str(self.root),'slack':{'enabled':True,'workspace':'fixture','recipient':'Ufixture'}}

    def test_success_once_across_restart_and_repeated_outcome(self):
        sender=Mock(return_value={'status':'sent','ok':True,'channel_id':'Dfixture','ts':'123','ts':'123'})
        outcome={'state':'complete','id':'version-queue','target':{'version':'156.0.8078.47'}}
        first=Announcer(self.config,sender)
        first.enqueue(outcome)
        first.flush()
        second=Announcer(self.config,sender)
        second.enqueue(outcome)
        second.flush()
        sender.assert_called_once()

    def test_uncertain_delivery_reuses_same_key_and_original_recipient(self):
        sender=Mock(side_effect=[TimeoutError('uncertain'),{'status':'sent','ok':True,'channel_id':'Dfixture','ts':'123'}])
        notifier=Announcer(self.config,sender)
        path=notifier.enqueue({'state':'failed','id':'version','stage':'build'})
        notifier.flush()
        self.assertFalse(json.loads(Path(path).read_text())['delivered'])
        self.config['slack']['recipient']='someone-else'
        notifier.flush()
        self.assertEqual(sender.call_args_list[0].args[0]['idempotency_key'],sender.call_args_list[1].args[0]['idempotency_key'])
        self.assertEqual(sender.call_args_list[1].args[0]['route']['recipient'],'Ufixture')
        self.assertTrue(json.loads(Path(path).read_text())['delivered'])

    def test_unchanged_does_not_enqueue_or_send(self):
        sender=Mock()
        notifier=Announcer(self.config,sender)
        self.assertIsNone(notifier.enqueue({'state':'unchanged'}))
        notifier.flush()
        sender.assert_not_called()

    def test_failure_message_excludes_raw_errors_and_private_fields(self):
        text=message({'state':'failed','stage':'build','error':'SECRET RAW LOG','config':{'token':'PRIVATE'}})
        self.assertNotIn('SECRET',text)
        self.assertNotIn('PRIVATE',text)

    def test_systemd_timeout_announces_once_without_normal_error_handler(self):
        from automation import atomic_json
        path=self.root/'config.json'
        atomic_json(path,self.config)
        atomic_json(self.root/'invocation.json',{'started_at':100})
        sender=Mock(return_value={'status':'sent','ok':True,'channel_id':'Dfixture','ts':'123'})
        with patch.object(sys,'argv',['notify','--config',str(path),'service-result']), \
             patch.dict(module.os.environ,{'SERVICE_RESULT':'timeout','INVOCATION_ID':'fixture-invocation'}), \
             patch.object(module.Announcer,'send',sender):
            module.main()
            module.main()
        sender.assert_called_once()
        self.assertIn('service-timeout',sender.call_args.args[0]['text'])

    def test_explicit_new_attempt_announces_new_failure(self):
        sender=Mock(return_value={'status':'sent','ok':True,'channel_id':'Dfixture','ts':'123'})
        notifier=Announcer(self.config,sender)
        notifier.enqueue({'state':'failed','id':'same-target','notification_attempt':1})
        notifier.enqueue({'state':'failed','id':'same-target','notification_attempt':2})
        notifier.flush()
        self.assertEqual(sender.call_count,2)

    def test_known_failed_action_does_not_poison_following_notices(self):
        sender=Mock(side_effect=[{'status':'failed','ok':False,'id':9},
                                {'status':'sent','ok':True,'channel_id':'Dfixture','ts':'123'}])
        notifier=Announcer(self.config,sender)
        notifier.enqueue({'state':'failed','id':'one'})
        notifier.enqueue({'state':'complete','id':'two'})
        notifier.flush()
        notifier.flush()
        self.assertEqual(sender.call_count,2)
        receipts=[json.loads(p.read_text()) for p in (self.root/'slack-outbox').glob('*.json')]
        self.assertEqual(sum(bool(r.get('requires_review')) for r in receipts),1)
        self.assertEqual(sum(r['delivered'] for r in receipts),1)

    def test_outage_stops_after_one_attempt_with_remaining_outbox_intact(self):
        sender=Mock(side_effect=RuntimeError('service down'))
        notifier=Announcer(self.config,sender)
        notifier.enqueue({'state':'failed','id':'one'})
        notifier.enqueue({'state':'complete','id':'two'})
        notifier.flush()
        sender.assert_called_once()
        self.assertEqual(len(list((self.root/'slack-outbox').glob('*.json'))),2)

if __name__=='__main__': unittest.main()
