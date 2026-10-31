import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import automation_retention as m


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name) / 'state'
        self.builds = self.state / 'builds'
        self.builds.mkdir(parents=True)
        (self.builds / '.chromium-stealthcdp-automation-owned').write_text(m.OWNER)
        self.installed = Path(self.temp.name) / 'installed'
        self.installed.mkdir()
        self.addCleanup(patch.stopall)
        patch.object(m, 'inspect_live_versions', return_value={'processes': [], 'unknownPids': []}).start()
        patch.object(m, '_in_use', return_value=False).start()

    def record(self, identity, state, created=1, committed=False):
        path = self.state / 'runs' / identity
        path.mkdir(parents=True)
        record = {'id': identity, 'created_at': created, 'state': state}
        if committed:
            record['deployment'] = {'status': 'committed', 'acceptance': {'success': True}}
        (path / 'run.json').write_text(json.dumps(record))
        paths = [self.builds / 'runs' / identity / 'artifacts',
                 self.builds / 'runs' / identity / 'packages',
                 self.builds / 'checkout/src/out' / ('Automation-' + identity)]
        for p in paths:
            p.mkdir(parents=True)
            (p / 'payload').write_text('generated')
        return paths

    def test_committed_build_removed_without_removing_installed_rollback_or_receipts(self):
        paths = self.record('deployed', 'complete', committed=True)
        for n in ['current-release', 'previous-release', 'third-release']:
            (self.installed / n).mkdir()
        (self.installed / 'current').symlink_to('current-release')
        result = m.maintain(self.state, self.installed)
        self.assertEqual(set(result['removed']), {str(p) for p in paths})
        self.assertTrue((self.installed / 'previous-release').is_dir())
        self.assertTrue((self.state / 'runs/deployed/run.json').is_file())

    def test_superseded_terminal_output_removed_but_latest_failure_and_active_kept(self):
        old = self.record('old', 'failed', 1)
        latest_failure = self.record('failure', 'failed', 2)
        deferred = self.record('superseded', 'deferred', 1)
        active = self.record('active', 'active', 1)
        newest = self.record('newest', 'complete', 3, committed=True)
        m.maintain(self.state, self.installed)
        self.assertTrue(all(not p.exists() for p in old + deferred + newest))
        self.assertTrue(all(p.exists() for p in latest_failure + active))

    def test_unverified_complete_and_current_deferred_are_preserved(self):
        paths = self.record('no-proof', 'complete') + self.record('latest', 'deferred', 4)
        m.maintain(self.state, self.installed)
        self.assertTrue(all(p.exists() for p in paths))

    def test_live_reference_protects_output(self):
        paths = self.record('live', 'complete', committed=True)
        with patch.object(m, '_in_use', return_value=True):
            result = m.maintain(self.state, self.installed)
        self.assertEqual(result['removed'], [])
        self.assertTrue(all(p.exists() for p in paths))

    def test_ambiguous_process_census_defers_every_build_deletion(self):
        paths = self.record('live', 'complete', committed=True)
        with patch.object(m, 'inspect_live_versions', return_value={'processes': [], 'unknownPids': [123]}):
            result = m.maintain(self.state, self.installed)
        self.assertIn('deferred', result)
        self.assertTrue(all(p.exists() for p in paths))

    def test_installed_selector_into_staging_protects_target(self):
        paths = self.record('selected', 'complete', committed=True)
        (self.installed / 'current').symlink_to(paths[0])
        result = m.maintain(self.state, self.installed)
        self.assertTrue(paths[0].is_dir())
        self.assertNotIn(str(paths[0]), result['removed'])

    def test_symlinked_parent_never_reaches_operator_tree(self):
        paths = self.record('linked', 'complete', committed=True)
        import shutil
        candidate = paths[0].parent
        shutil.rmtree(candidate)
        outside = Path(self.temp.name) / 'operator'
        outside.mkdir()
        (outside / 'artifacts').mkdir()
        candidate.symlink_to(outside)
        m.maintain(self.state, self.installed)
        self.assertTrue((outside / 'artifacts').is_dir())

    def test_nested_mount_is_not_a_cleanup_candidate(self):
        paths = self.record('mounted', 'complete', committed=True)
        original = Path.read_text
        def read(path, *args, **kwargs):
            if str(path) == '/proc/self/mountinfo':
                return f'1 0 8:48 / {paths[0]}/bind rw - ext4 /dev/sdd rw\n'
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            result = m.maintain(self.state, self.installed)
        self.assertTrue(paths[0].is_dir())
        self.assertNotIn(str(paths[0]), result['removed'])

    def test_ancestor_bind_mount_cannot_redirect_owned_output(self):
        paths = self.record('mounted-parent', 'complete', committed=True)
        original = Path.read_text
        for mount in [self.builds, paths[0].parent, self.builds/'checkout']:
            with self.subTest(mount=mount):
                def read(path, *args, **kwargs):
                    if str(path) == '/proc/self/mountinfo':
                        return f'1 0 8:48 / {mount} rw - ext4 /dev/sdd rw\n'
                    return original(path, *args, **kwargs)
                target = paths[2] if mount == self.builds/'checkout' else paths[0]
                with patch.object(Path, 'read_text', read):
                    self.assertFalse(m._safe_path(target, self.builds))
                self.assertTrue(target.is_dir())

    def test_malformed_identity_rejected_without_deletion(self):
        paths = self.record('ordinary', 'complete', committed=True)
        receipt = self.state / 'runs/ordinary/run.json'
        record = json.loads(receipt.read_text())
        record['id'] = '../../operator'
        receipt.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            m.maintain(self.state, self.installed)
        self.assertTrue(all(p.exists() for p in paths))

    def test_unowned_build_root_never_removed(self):
        paths = self.record('unowned', 'complete', committed=True)
        (self.builds / '.chromium-stealthcdp-automation-owned').unlink()
        m.maintain(self.state, self.installed)
        self.assertTrue(all(p.exists() for p in paths))

    def test_real_process_cwd_reference_is_protected(self):
        import os
        directory = self.builds / 'working'
        directory.mkdir()
        before = Path.cwd()
        try:
            os.chdir(directory)
            # Use the real implementation despite the general test safety mock.
            patch.stopall()
            with patch.object(m, 'inspect_live_versions', return_value={'processes': [], 'unknownPids': []}):
                self.assertTrue(m._in_use(directory, self.builds))
        finally:
            os.chdir(before)

if __name__ == '__main__':
    unittest.main()
