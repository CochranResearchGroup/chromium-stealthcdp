import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import automation as m

class ControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = {'state_dir': str(self.root / 'state'), 'source_repo': str(self.root / 'source'), 'depot_tools': '/depot', 'installed_root': str(self.root/'nonexistent')}
        (self.root / 'source/patches').mkdir(parents=True)
        (self.root / 'source/patches/one.patch').write_text('approved')
        self.target = {'version': '156.0.8078.47', 'upstream_revision': 'a'*40}

    def fake_command(self, argv, cwd=None, timeout=300):
        if argv[:2] == ['git', 'clone']:
            import shutil
            shutil.copytree(self.root / 'source', Path(argv[-1]))
        return ''

    def github(self):
        from unittest.mock import Mock
        gh = Mock()
        gh.preflight.return_value = {'push': True}
        gh.notify.return_value = {'delivered': True}
        return gh

    def controller(self):
        return m.Controller(self.config, github=self.github(), discover_fn=lambda: dict(self.target))

    def test_unchanged_never_builds_or_publishes(self):
        controller = self.controller()
        m.atomic_json(controller.root / 'baseline.json', {'version': self.target['version'], 'patch_queue_sha256': m.patch_digest(self.root/'source')})
        with patch.object(m, 'command', side_effect=self.fake_command):
            result = controller.run()
        self.assertEqual(result['state'], 'unchanged')
        controller.github.integrate.assert_not_called()
        controller.github.publish.assert_not_called()

    def test_failure_same_target_stops_without_rebuilding(self):
        controller = self.controller()
        target = dict(self.target, approved_patch_queue_sha256=m.patch_digest(self.root/'source'))
        identity = m.target_id(target)
        m.atomic_json(controller.root/'runs'/identity/'run.json', {'id':identity,'state':'failed'})
        with patch.object(m, 'command', side_effect=self.fake_command):
            result=controller.run()
        self.assertEqual(result['state'],'stopped')
        controller.github.publish.assert_not_called()

    def test_resource_shortage_defers_without_pipeline(self):
        controller=self.controller()
        with patch.object(m,'command',side_effect=self.fake_command), patch.object(m,'headroom',return_value={'ready':False}):
            result=controller.run()
        self.assertEqual(result['state'],'deferred')
        controller.github.publish.assert_not_called()

    def test_ambiguous_publication_resumes_readback_not_build(self):
        controller=self.controller()
        target=dict(self.target, approved_patch_queue_sha256=m.patch_digest(self.root/'source'))
        identity=m.target_id(target)
        run={'id':identity,'target':target,'state':'active','stage':'publish','context':{},'integration':{'source_commit':'b'*40}}
        controller.save(run)
        controller.github.publish.side_effect=RuntimeError('remote outcome uncertain')
        with patch.object(m,'command',side_effect=self.fake_command):
            with self.assertRaisesRegex(RuntimeError,'uncertain'):
                controller.run()
        controller.github.integrate.assert_not_called()
        self.assertEqual(m.load(controller.root/'runs'/identity/'run.json')['stage'],'publish')
        controller.github.notify.assert_called_once()


    def test_full_success_then_noop_does_not_repeat_effects(self):
        from unittest.mock import Mock
        context={'artifact':str(self.root/'artifact'),'patchset':str(self.root/'exported'),
                 'patch_queue_sha256':m.patch_digest(self.root/'source')}
        factory=Mock()
        factory.return_value.run.return_value=context
        deploy=Mock(return_value={'status':'committed'})
        gh=self.github()
        gh.integrate.return_value={'source_commit':'b'*40}
        gh.publish.return_value={'tag':'v156-fixture'}
        controller=m.Controller(self.config,github=gh,discover_fn=lambda:dict(self.target),pipeline_factory=factory,deploy_fn=deploy)
        with patch.object(m,'command',side_effect=self.fake_command),patch.object(m,'headroom',return_value={'ready':True}):
            first=controller.run()
            second=controller.run()
        self.assertEqual(first['state'],'complete')
        self.assertEqual(second['state'],'unchanged')
        factory.return_value.run.assert_called_once()
        gh.integrate.assert_called_once()
        gh.publish.assert_called_once()
        deploy.assert_called_once()
        self.assertEqual(first['context']['patchset_repo'],context['patchset'])

    def test_preflight_failure_records_undelivered_after_prior_run(self):
        from unittest.mock import Mock
        config_path=self.root/'config.json'
        m.atomic_json(config_path,self.config)
        m.atomic_json(Path(self.config['state_dir'])/'active.json',{'id':'previous'})
        gh=self.github()
        gh.preflight.side_effect=RuntimeError('auth unavailable')
        gh.notify.side_effect=RuntimeError('auth unavailable')
        with patch.object(m,'GitHub',return_value=gh),patch.object(sys,'argv',['automation','--config',str(config_path),'run']):
            self.assertEqual(m.main(),1)
        self.assertIs(m.load(Path(self.config['state_dir'])/'last-error.json')['notification']['delivered'],False)
        gh.notify.assert_called_once()

    def test_publication_requires_approved_remote_before_any_effect(self):
        with patch.object(m,'command',return_value='/local/clone'):
            with self.assertRaisesRegex(RuntimeError,'remote is outside'):
                m.GitHub().publish({'patchset_repo':str(self.root),'version':'156.0.8078.47','patch_queue_sha256':'c'*64},{'source_commit':'b'*40})

    def test_atomic_state_keeps_exact_values(self):
        path=self.root/'receipt.json'
        m.atomic_json(path,{'state':'active','version':'156.0.8078.47'})
        self.assertEqual(m.load(path)['version'],'156.0.8078.47')
        self.assertEqual(path.stat().st_mode & 0o777,0o600)

    def test_stable_discovery_rejects_unpinned_identity(self):
        with self.assertRaises(ValueError):
            m.discover(lambda:[{'version':'latest','hashes':{'chromium':'bad'}}])

    def test_stable_discovery_retries_transient_once(self):
        from unittest.mock import Mock
        fetch=Mock(side_effect=[TimeoutError(),[{'version':'156.0.8078.47','hashes':{'chromium':'a'*40}}]])
        self.assertEqual(m.discover(fetch)['upstream_revision'],'a'*40)
        self.assertEqual(fetch.call_count,2)

    def test_repository_scope_is_fixed(self):
        with self.assertRaises(ValueError):
            m.GitHub('somewhere/else')

if __name__=='__main__':
    unittest.main()
