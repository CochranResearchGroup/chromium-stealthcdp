"""Provider-free checks for candidate safety and immutable package resumption."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from automation_pipeline import CandidatePipeline, PipelineConfig, PipelineError, patch_queue_sha256, sha256


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

    def test_packaging_requires_qualified_candidate(self):
        with self.assertRaisesRegex(PipelineError, 'Only qualified'):
            self.pipeline.package({'stage': 'built'})

    def test_resumed_package_must_match_recorded_digest(self):
        asset = self.base / 'browser.tar.zst'
        asset.write_bytes(b'qualified package')
        context = {'stage': 'packaged', 'package_sha256': {str(asset): sha256(asset)}}
        self.assertIs(self.pipeline.package(context), context)
        asset.write_bytes(b'tampered package')
        with self.assertRaisesRegex(PipelineError, 'package changed'):
            self.pipeline.package(context)


if __name__ == '__main__':
    unittest.main()
