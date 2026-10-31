import os
import json
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import automation_process_probe as m


class ProcessProbeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.proc = Path(self.temp.name) / 'proc'
        boot = self.proc / 'sys/kernel/random'
        boot.mkdir(parents=True)
        (boot / 'boot_id').write_text('boot-id')
        self.roots = ['/owned/builds', '/owned/installed']

    def process(self, pid=123, state='S', start=99):
        process = self.proc / str(pid)
        (process / 'fd').mkdir(parents=True)
        fields = [state] + ['0'] * 18 + [str(start)]
        (process / 'stat').write_text(f'{pid} (name with ) parentheses) ' + ' '.join(fields))
        (process / 'exe').symlink_to('/usr/bin/python3')
        (process / 'cwd').symlink_to('/unrelated/private/path')
        (process / 'maps').write_text('')
        return process

    def collect(self):
        return m.collect(os.getuid(), self.roots, self.proc)

    def test_filters_private_paths_and_collects_every_reference_kind(self):
        process = self.process()
        (process / 'exe').unlink()
        (process / 'exe').symlink_to('/owned/installed/v1/chrome')
        (process / 'cwd').unlink()
        (process / 'cwd').symlink_to('/owned/builds/run')
        (process / 'fd/3').symlink_to('/owned/builds/run/out.o (deleted)')
        (process / 'fd/4').symlink_to('/private/secret')
        (process / 'maps').write_text('0-1 r--p 0 00:00 0 /owned/builds/a\\040b.so\n'
                                      '0-1 r--p 0 00:00 0 /private/secret.so\n')
        result = self.collect()
        self.assertEqual(result['unknownPids'], [])
        self.assertEqual(result['boot_id'], 'boot-id')
        self.assertTrue(all(r['starttime'] == 99 for r in result['references']))
        self.assertEqual({r['kind'] for r in result['references']}, {'exe', 'cwd', 'fd', 'maps'})
        self.assertIn('/owned/builds/a b.so', [r['path'] for r in result['references']])
        self.assertNotIn('private', str(result))

    def test_fully_inspected_unrelated_process_returns_no_paths(self):
        self.process()
        self.assertEqual(self.collect()['references'], [])
        self.assertEqual(self.collect()['unknownPids'], [])

    def test_prefix_sibling_is_not_in_owned_root(self):
        process = self.process()
        (process / 'fd/3').symlink_to('/owned/builds-elsewhere/private')
        self.assertEqual(self.collect()['references'], [])

    def test_unreadable_executable_fails_closed(self):
        process = self.process()
        original = os.readlink
        def read(path):
            if path == process / 'exe':
                raise PermissionError('denied')
            return original(path)
        with patch.object(m.os, 'readlink', read):
            self.assertEqual(self.collect()['unknownPids'], [123])

    def test_unreadable_maps_or_fd_fails_closed(self):
        process = self.process()
        original = Path.read_text
        def read(path, *args, **kwargs):
            if path == process / 'maps':
                raise PermissionError('denied')
            return original(path, *args, **kwargs)
        with patch.object(Path, 'read_text', read):
            self.assertEqual(self.collect()['unknownPids'], [123])
        with patch.object(Path, 'iterdir', autospec=True, side_effect=lambda p:
                (_ for _ in ()).throw(PermissionError('denied')) if p == process / 'fd'
                else iter([process])):
            self.assertEqual(self.collect()['unknownPids'], [123])

    def test_live_process_missing_executable_is_unknown(self):
        process = self.process()
        (process / 'exe').unlink()
        self.assertEqual(self.collect()['unknownPids'], [123])

    def test_zombie_and_exited_process_do_not_block(self):
        self.process(state='Z')
        process = self.process(pid=456)
        (process / 'stat').unlink()
        self.assertEqual(self.collect()['unknownPids'], [])

    def test_pid_reuse_fails_closed(self):
        self.process()
        with patch.object(m, '_identity', side_effect=[('S', 99), ('S', 100)]):
            self.assertEqual(self.collect()['unknownPids'], [123])

    def test_other_uid_process_is_excluded(self):
        self.process()
        result = m.collect(os.getuid() + 1, self.roots, self.proc)
        self.assertEqual(result['references'], [])
        self.assertEqual(result['unknownPids'], [])

    def test_cli_rejects_arguments_before_scanning(self):
        with patch.object(sys, 'argv', ['probe', '/arbitrary']), patch.object(m, 'collect') as collect:
            with self.assertRaises(SystemExit):
                m.main()
            collect.assert_not_called()

    def test_cli_requires_root_before_scanning(self):
        with patch.object(sys, 'argv', ['probe']), patch.object(os, 'geteuid', return_value=1000), \
                patch.object(m, 'collect') as collect:
            with self.assertRaises(SystemExit):
                m.main()
            collect.assert_not_called()

    def test_config_rejects_writable_or_nonroot_owned_ancestors(self):
        config = Path('/etc/chromium-stealthcdp/process-census.json')
        for owner, mode in [(1000, 0o755), (0, 0o777)]:
            with self.subTest(owner=owner, mode=mode):
                with patch.object(Path, 'lstat', return_value=SimpleNamespace(
                        st_uid=owner, st_mode=stat.S_IFREG | mode)):
                    with self.assertRaisesRegex(ValueError, 'protected by root'):
                        m.load_config(config)

    def test_config_rejects_root_uid_and_unbounded_paths(self):
        metadata = SimpleNamespace(st_uid=0, st_mode=stat.S_IFREG | 0o644)
        for config in [{'uid': 0, 'roots': self.roots}, {'uid': 1000, 'roots': ['/']},
                       {'uid': 1000, 'roots': ['relative']},
                       {'uid': 1000, 'roots': ['/owned/../private']}]:
            with self.subTest(config=config):
                with patch.object(Path, 'lstat', return_value=metadata), \
                        patch.object(Path, 'read_text', return_value=json.dumps(config)):
                    with self.assertRaises(ValueError):
                        m.load_config()


if __name__ == '__main__':
    unittest.main()
