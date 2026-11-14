"""Provider-free regressions for codec recipe identity and fail-closed release gates."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
import automation
import automation_pipeline as pipeline


class CodecContinuityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        (self.repo / 'patches').mkdir(parents=True)
        (self.repo / 'patches/0001.patch').write_text('approved patch\n')
        self.root = self.base / 'managed'
        self.subject = pipeline.CandidatePipeline(
            pipeline.PipelineConfig(self.repo, self.root, self.base / 'depot'))
        self.target = {
            'version': '157.0.8103.78',
            'approved_patch_queue_sha256': pipeline.patch_queue_sha256(self.repo / 'patches'),
        }

    def test_changed_recipe_changes_controller_run_identity(self):
        first = dict(self.target, build_recipe_sha256='a' * 64)
        second = dict(self.target, build_recipe_sha256='b' * 64)
        self.assertNotEqual(automation.target_id(first), automation.target_id(second))
        self.assertEqual(automation.target_id(first), automation.target_id(dict(first)))

    def test_unspecified_recipe_uses_current_recipe_for_run_identity(self):
        current = pipeline.build_recipe_sha256()
        self.assertRegex(current, r'^[0-9a-f]{64}$')
        self.assertEqual(automation.target_id(self.target),
                         automation.target_id(dict(self.target, build_recipe_sha256=current)))

    def test_changed_recipe_has_a_distinct_immutable_artifact_name(self):
        queue = self.target['approved_patch_queue_sha256']
        first = pipeline.artifact_name(self.target['version'], queue, 'a' * 64)
        second = pipeline.artifact_name(self.target['version'], queue, 'b' * 64)
        self.assertNotEqual(first, second)
        self.assertEqual(first, f'157.0.8103.78+stealthcdp.{queue[:12]}.build.aaaaaaaaaaaa')
        self.assertEqual(second, f'157.0.8103.78+stealthcdp.{queue[:12]}.build.bbbbbbbbbbbb')

    def test_resolved_testing_or_codec_mismatch_never_compiles(self):
        expected = {
            'proprietary_codecs': 'true',
            'ffmpeg_branding': '"Chrome"',
            'is_chrome_branded': 'false',
            'is_chrome_for_testing': 'false',
            'is_chrome_for_testing_branded': 'false',
        }
        for bad_key, bad_value in [
            ('is_chrome_for_testing', 'true'),
            ('is_chrome_for_testing_branded', 'true'),
            ('is_chrome_for_testing', 'unknown'),
            ('proprietary_codecs', 'false'),
            ('ffmpeg_branding', '"Chromium"'),
        ]:
            with self.subTest(flag=bad_key, value=bad_value):
                calls = []
                src = self.base / bad_key / bad_value.replace('"', '') / 'src'
                src.mkdir(parents=True)
                context = {
                    'stage': 'prepared', 'src': str(src), 'out': 'out/candidate',
                    'build_recipe_sha256': pipeline.build_recipe_sha256(),
                    'run_root': str(src.parent / 'run'),
                }

                def command(ctx, argv, **kwargs):
                    argv = [str(x) for x in argv]
                    calls.append(argv)
                    if argv[:2] == ['gn', 'args']:
                        key = next(x.split('=', 1)[1] for x in argv if x.startswith('--list='))
                        value = bad_value if key == bad_key else expected[key]
                        return f'{key} = {value}'
                    return ''

                with patch.object(self.subject, 'check_source'), \
                     patch.object(self.subject, 'command', side_effect=command):
                    with self.assertRaises(pipeline.PipelineError):
                        self.subject.build(context)
                self.assertFalse(any(Path(call[0]).name in ('autoninja', 'ninja', 'siso')
                                     for call in calls), calls)
                emitted = (src / context['out'] / 'args.gn').read_text()
                for key, value in expected.items():
                    self.assertIn(f'{key}={value}', emitted.replace(' ', ''))

    def test_failed_distribution_metadata_never_compiles(self):
        src=self.base/'license-src';src.mkdir()
        context={'stage':'prepared','src':str(src),'out':'out/candidate',
                 'build_recipe_sha256':pipeline.build_recipe_sha256(),'run_root':str(self.base/'run')}
        expected={'proprietary_codecs':'true','ffmpeg_branding':'"Chrome"','is_chrome_branded':'false',
                  'is_chrome_for_testing':'false','is_chrome_for_testing_branded':'false'}
        calls=[]
        def command(ctx,argv,**kwargs):
            argv=[str(x) for x in argv];calls.append(argv)
            if argv[:2]==['gn','args']:
                key=next(x.split('=',1)[1] for x in argv if x.startswith('--list='))
                return key+' = '+expected[key]
            if any(x.endswith('licenses.py') for x in argv):
                raise pipeline.PipelineError('missing target metadata')
            return ''
        with patch.object(self.subject,'check_source'),patch.object(self.subject,'command',side_effect=command):
            with self.assertRaisesRegex(pipeline.PipelineError,'missing target metadata'):
                self.subject.build(context)
        self.assertFalse(any(Path(x[0]).name=='autoninja' for x in calls))

    def test_legacy_built_candidate_cannot_resume_without_recipe(self):
        self.root.mkdir()
        (self.root / '.chromium-stealthcdp-automation-owned').write_text(
            'chromium-stealthcdp automation v1\n')
        target = dict(self.target, run_id='legacy-built',
                      build_recipe_sha256=pipeline.build_recipe_sha256())
        run = self.root / 'runs' / target['run_id']
        run.mkdir(parents=True)
        (run / 'candidate.json').write_text(json.dumps({
            'version': target['version'],
            'approved_patch_queue_sha256': target['approved_patch_queue_sha256'],
            'stage': 'built',
        }))
        with patch.object(self.subject, 'check_source') as source_check:
            with self.assertRaisesRegex(pipeline.PipelineError, '[Rr]ecipe'):
                self.subject.prepare(target)
        source_check.assert_not_called()

    def test_unqualified_source_integration_has_no_push_or_pr_effect(self):
        github = automation.GitHub()
        with patch.object(automation, 'command') as command, patch.object(github, 'gh') as gh:
            with self.assertRaisesRegex(RuntimeError, '[Dd]istribution'):
                github.integrate({}, {})
        command.assert_not_called()
        gh.assert_not_called()

    def test_accepted_decoder_receipt_is_reconciled_without_relaunch(self):
        executable=self.base/'accepted-chrome';executable.write_bytes(b'candidate')
        (self.repo/'scripts').mkdir()
        (self.repo/'scripts/codec-acceptance.mjs').write_bytes((SCRIPTS/'codec-acceptance.mjs').read_bytes())
        root=self.base/'accepted';root.mkdir()
        report={'success':True,'profileWritersGone':True,'sha256':pipeline.sha256(executable),
                'harnessSha256':pipeline.sha256(SCRIPTS/'codec-acceptance.mjs'),
                'observed':{'webdriver':False,'h264':{'decoded':True,'frames':10},
                            'webm':{'decoded':True,'frames':10},
                            'aac':{'decoded':True,'samples':44099,'rms':0.088}}}
        (root/'result.json').write_text(json.dumps(report))
        with patch.object(self.subject,'command') as command:
            self.assertEqual(self.subject.codec_acceptance({},executable,root),report)
        command.assert_not_called()

    def test_failed_actual_decoder_report_cannot_qualify_bytes(self):
        executable = self.base/'chrome'
        executable.write_bytes(b'candidate')
        fixture = {'success':True,'profileWritersGone':True,'sha256':pipeline.sha256(executable),
                   'harnessSha256':pipeline.sha256(SCRIPTS/'codec-acceptance.mjs'),
                   'observed':{'webdriver':False,'h264':{'decoded':True,'frames':10},
                               'webm':{'decoded':True,'frames':10},
                               'aac':{'decoded':True,'samples':44099,'rms':0.088}}}
        (self.repo/'scripts').mkdir()
        (self.repo/'scripts/codec-acceptance.mjs').write_bytes((SCRIPTS/'codec-acceptance.mjs').read_bytes())
        for field in ('frames','aac','webdriver','sha'):
            report=json.loads(json.dumps(fixture))
            if field=='frames':report['observed']['h264']['frames']=0
            if field=='aac':report['observed']['aac']['decoded']=False
            if field=='webdriver':report['observed']['webdriver']=True
            if field=='sha':report['sha256']='0'*64
            root=self.base/field;root.mkdir();(root/'result.json').write_text(json.dumps(report))
            with self.subTest(field=field), patch.object(self.subject,'command'):
                with self.assertRaisesRegex(pipeline.PipelineError,'codec acceptance'):
                    self.subject.codec_acceptance({},executable,root)

    def test_local_qualification_merges_without_hosted_action_checks(self):
        recipe=pipeline.build_recipe_sha256();queue=pipeline.patch_queue_sha256(self.repo/'patches')
        artifact=self.base/'artifact';artifact.mkdir();(artifact/'manifest.json').write_text(
            json.dumps({'executable':{'sha256':'c'*64}}))
        context={'patchset_repo':str(self.repo),'artifact':str(artifact),'version':'157.0.8103.78',
                 'upstream_revision':'d'*40,'patch_queue_sha256':queue,'build_recipe_sha256':recipe,
                 'gn_args_sha256':'e'*64,'distribution_qualification':{'success':True,'build_recipe_sha256':recipe}}
        head='a'*40;merge='b'*40;github=automation.GitHub()
        def command(argv,**kwargs):
            if argv[:4]==['git','remote','get-url','origin']:return 'https://github.com/'+automation.REPOSITORY+'.git'
            if argv[:3]==['git','rev-parse','HEAD']:return head
            if argv[:2]==['git','ls-remote']:return head+' refs/heads/fixture'
            if argv[:2]==['git','rev-parse']:return 'patch-tree'
            return ''
        def gh(*argv,**kwargs):
            if argv[:2]==('pr','list'):return json.dumps([{'number':14,'state':'OPEN','headRefOid':head}])
            if argv[:2]==('pr','view'):return json.dumps({'state':'MERGED','headRefOid':head,'mergeCommit':{'oid':merge}})
            return ''
        with patch.object(automation,'command',side_effect=command),patch.object(github,'gh',side_effect=gh) as forge, \
             patch.object(github,'api',return_value={'state':'success'}) as api:
            result=github.integrate(context,{'id':'fixture'})
        self.assertEqual(result['source_commit'],merge)
        self.assertTrue(any(call.args[:2]==('pr','merge') for call in forge.call_args_list))
        self.assertEqual(api.call_count,1)
        self.assertEqual(api.call_args.args[0],'statuses/'+head)

    def test_missing_release_qualification_refuses_before_external_effects(self):
        github = automation.GitHub()
        with patch.object(automation, 'command') as command, \
             patch.object(github, 'gh') as gh, patch.object(github, 'api') as api:
            with self.assertRaisesRegex(RuntimeError, '[Dd]istribution'):
                github.publish({}, {})
        command.assert_not_called()
        gh.assert_not_called()
        api.assert_not_called()

    def test_failed_distribution_qualification_refuses_before_external_effects(self):
        github = automation.GitHub()
        context = {
            'distribution_qualification': {'status': 'failed'},
            'build_recipe_sha256': 'a' * 64,
        }
        with patch.object(automation, 'command') as command, \
             patch.object(github, 'gh') as gh, patch.object(github, 'api') as api:
            with self.assertRaisesRegex(RuntimeError, '[Dd]istribution'):
                github.publish(context, {})
        command.assert_not_called()
        gh.assert_not_called()
        api.assert_not_called()


if __name__ == '__main__':
    unittest.main()
