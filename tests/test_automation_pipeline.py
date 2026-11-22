"""Provider-free checks for candidate safety and immutable package resumption."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from automation_pipeline import CandidatePipeline, PipelineConfig, PipelineError, patch_queue_sha256, sha256, build_recipe_sha256, artifact_name


class PipelineSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / 'repo'
        (self.repo / 'patches').mkdir(parents=True)
        (self.repo / 'patches/0001.patch').write_text('approved patch\n')
        self.root = self.base / 'managed'
        self.config = PipelineConfig(self.repo, self.root, self.base / 'depot')
        self.pipeline = CandidatePipeline(self.config)
        self.target = {'version': '156.0.8078.47', 'run_id': 'test',
                       'patch_queue_sha256': patch_queue_sha256(self.repo / 'patches')}

    def test_operator_source_cannot_be_managed_root(self):
        with self.assertRaises(PipelineError):
            CandidatePipeline(PipelineConfig(self.repo, self.repo / '../src/out', self.base / 'depot'))

    def test_changed_approved_queue_rejected_before_work(self):
        (self.repo / 'patches/0001.patch').write_text('unreviewed change\n')
        with self.assertRaisesRegex(PipelineError, 'Approved patch queue changed'):
            self.pipeline.prepare(self.target)
        self.assertFalse(self.root.exists())

    def test_nonempty_unowned_directory_is_untouched(self):
        self.root.mkdir()
        sentinel = self.root / 'operator-source'
        sentinel.write_text('preserve')
        with self.assertRaisesRegex(PipelineError, 'unowned'):
            self.pipeline.prepare(self.target)
        self.assertEqual(sentinel.read_text(), 'preserve')
        self.assertFalse((self.root / '.chromium-stealthcdp-automation-owned').exists())

    def test_run_path_traversal_is_rejected(self):
        self.target['run_id'] = '../operator'
        with self.assertRaisesRegex(PipelineError, 'Unsafe run'):
            self.pipeline.prepare(self.target)

    def test_interrupted_preparation_does_not_reset_checkout(self):
        self.root.mkdir()
        (self.root / '.chromium-stealthcdp-automation-owned').write_text('chromium-stealthcdp automation v1\n')
        run = self.root / 'runs/test'
        run.mkdir(parents=True)
        (run / 'candidate.json').write_text(json.dumps({**self.target,
            'approved_patch_queue_sha256': self.target['patch_queue_sha256'], 'stage': 'preparing'}))
        with self.assertRaisesRegex(PipelineError, 'explicit repair'):
            self.pipeline.prepare(self.target)

    def test_prepare_preserves_libsync_when_upstream_replaces_gitlink(self):
        self.root.mkdir()
        (self.root / '.chromium-stealthcdp-automation-owned').write_text('chromium-stealthcdp automation v1\n')
        src = self.root / 'checkout/src'
        dependency = src / 'third_party/libsync/src'
        dependency.mkdir(parents=True)

        def git(cwd, *args):
            return subprocess.check_output(
                ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', *args],
                cwd=cwd, stderr=subprocess.STDOUT, text=True).strip()

        git(src, 'init', '-q')
        git(dependency, 'init', '-q')
        (dependency / 'NOTICE').write_text('old dependency')
        git(dependency, 'add', 'NOTICE')
        git(dependency, 'commit', '-qm', 'Dependency')
        git(src, 'add', 'third_party/libsync/src')
        git(src, 'commit', '-qm', 'Gitlink')
        old = git(src, 'rev-parse', 'HEAD')
        saved = self.base / 'old-dependency'
        dependency.rename(saved)
        git(src, 'rm', '--cached', 'third_party/libsync/src')
        dependency.mkdir()
        (dependency / 'NOTICE').write_text('new upstream file')
        git(src, 'add', 'third_party/libsync/src')
        git(src, 'commit', '-qm', 'Vendor dependency')
        git(src, 'tag', self.target['version'])
        git(src, 'remote', 'add', 'origin', str(src))
        git(src, 'checkout', '--detach', old)
        saved.rename(dependency)

        def runner(args, *, cwd, **kwargs):
            if args[:2] == ['gclient', 'sync']:
                self.assertEqual((dependency / 'NOTICE').read_text(), 'new upstream file')
                raise PipelineError('Fixture reached dependency sync')
            return git(cwd, *args[1:])

        with self.assertRaisesRegex(PipelineError, 'Fixture reached dependency sync'):
            CandidatePipeline(self.config, runner=runner).prepare(self.target)
        preserved = list(self.root.glob('runs/test/**/libsync-src/NOTICE'))
        self.assertEqual([path.read_text() for path in preserved], ['old dependency'])
        self.assertTrue((preserved[0].parent / '.git').is_dir())

    def test_fetch_retries_only_identified_transport_failure_once(self):
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            kwargs['log'].write_text('fatal: Could not resolve host upstream.example\n')
            raise PipelineError('transport failure')
        pipeline = CandidatePipeline(self.config, runner=runner)
        context = {'evidence': str(self.base / 'evidence'), 'src': str(self.base / 'source')}
        with self.assertRaises(PipelineError):
            pipeline.fetch(context, ['git', 'fetch', 'origin'])
        self.assertEqual(len(calls), 2)
        with self.assertRaises(PipelineError):
            pipeline.fetch(context, ['git', 'fetch', 'origin'])
        self.assertEqual(len(calls), 3)

    def test_source_or_build_failure_is_not_retried(self):
        calls = []
        def runner(args, **kwargs):
            calls.append(args)
            kwargs['log'].write_text('fatal: ambiguous upstream revision\n')
            raise PipelineError('invalid revision')
        pipeline = CandidatePipeline(self.config, runner=runner)
        context = {'evidence': str(self.base / 'evidence'), 'src': str(self.base / 'source')}
        with self.assertRaises(PipelineError):
            pipeline.fetch(context, ['git', 'fetch', 'origin'])
        self.assertEqual(len(calls), 1)

    def test_qualification_resume_reuses_existing_staged_candidate(self):
        src=self.base/'src'
        out=src/'out/test'
        out.mkdir(parents=True)
        from automation_pipeline import GN_ARGS
        (out/'args.gn').write_text(GN_ARGS)
        evidence=self.base/'run/evidence'
        evidence.mkdir(parents=True)
        artifact=self.base/'run/artifacts'/artifact_name('156.0.8078.47','queue',build_recipe_sha256())
        (artifact/'chrome-linux').mkdir(parents=True)
        (artifact/'chrome-linux/chrome').write_bytes(b'accepted executable')
        (out/'chrome').write_bytes(b'accepted executable')
        manifest={'buildRecipeSha256':build_recipe_sha256(),'chromium':{'upstreamRevision':'base','sourceSha':'source','dirty':False},
                  'patchset':{'patchQueueSha256':'queue','dirty':False},
                  'executable':{'relativePath':'chrome-linux/chrome','sha256':sha256(artifact/'chrome-linux/chrome')}}
        (artifact/'manifest.json').write_text(json.dumps(manifest))
        (artifact.parent/'current').symlink_to(artifact.name)
        context={'build_recipe_sha256':build_recipe_sha256(),'stage':'built','src':str(src),'out':'out/test','version':'156.0.8078.47',
                 'evidence':str(evidence),'run_root':str(self.base/'run'),'patchset':str(self.repo),
                 'upstream_revision':'base','source_sha':'source','patch_queue_sha256':'queue',
                 'required_regressions':['LineBreakerTest.BreakWordWithReusedShapeResult'],
                 'browser_pgo':{},'gn_args_sha256':'args','v8_revision':'v8'}
        (src/'LICENSE').write_text('license')
        (src/'third_party/ffmpeg').mkdir(parents=True)
        for name in ('README.chromium','CREDITS.chromium'):
            (src/'third_party/ffmpeg'/name).write_text('notice')
        def command(ctx,args,**kwargs):
            if str(args[0]).endswith('promote-artifact.sh'):
                raise PipelineError('artifact already exists')
            if '--version' in args:return 'Chromium 156.0.8078.47'
            if str(args[0]).endswith('blink_unittests'):
                (evidence/'line-breaker.xml').write_text('<testsuites><testcase classname="LineBreakerTest" name="BreakWordWithReusedShapeResult"/></testsuites>')
            if str(args[0]).endswith('media_unittests'):
                (evidence/'media.xml').write_text('<testsuites><testcase classname="FFmpegVideoDecoderTest" name="Decode"/></testsuites>')
            if str(args[0]).endswith('smoke.sh'):
                Path(args[-1]).write_text(json.dumps({'success':True,'checks':{'navigatorWebdriver':'false'}}))
            return ''
        with patch.object(self.pipeline,'check_source'),patch.object(self.pipeline,'command',side_effect=command), \
             patch.object(self.pipeline,'codec_acceptance', side_effect=lambda ctx,exe,root: (root.mkdir(parents=True,exist_ok=True),(root/'result.json').write_text('{}'))), \
             patch('automation_deploy.qualify_agent_browser',return_value={'success':True}):
            result=self.pipeline.qualify(context)
        self.assertEqual(result['stage'],'qualified')
        self.assertEqual(Path(result['artifact']),artifact)

    def test_packaging_requires_qualified_candidate(self):
        with self.assertRaisesRegex(PipelineError, 'Only qualified'):
            self.pipeline.package({'stage': 'built'})

    def test_resumed_package_must_match_recorded_digest(self):
        asset = self.base / 'browser.tar.zst'
        asset.write_bytes(b'qualified package')
        context = {'build_recipe_sha256':build_recipe_sha256(),'distribution_qualification':{'success':True,'build_recipe_sha256':build_recipe_sha256()},'stage': 'packaged', 'package_sha256': {str(asset): sha256(asset)}}
        self.assertIs(self.pipeline.package(context), context)
        asset.write_bytes(b'tampered package')
        with self.assertRaisesRegex(PipelineError, 'package changed'):
            self.pipeline.package(context)


if __name__ == '__main__':
    unittest.main()
