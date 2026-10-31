import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import automation_processes as m


class PrivilegedProbeTests(unittest.TestCase):
    def snapshot(self):
        return {'schema': 'stealthcdp.process-census.v1', 'collected_at': m.time.time(),
                'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'uid': os.getuid(), 'roots': ['/owned'], 'unknownPids': [],
                'references': [{'pid': 42, 'starttime': 1, 'path': '/owned/release/lib.so', 'kind': 'maps'}]}

    def run_probe(self, snapshot):
        with patch.object(m, '_trusted', return_value=True), patch.object(m.subprocess, 'run',
                return_value=SimpleNamespace(returncode=0, stdout=json.dumps(snapshot))) as command:
            result = m.privileged_references('/owned')
        self.assertEqual(command.call_args.args[0], ['/usr/bin/sudo', '-n', '--', str(m.PROBE)])
        return result

    def test_fresh_fixed_scope_reference_is_returned(self):
        result = self.run_probe(self.snapshot())
        self.assertTrue(result['referenceScanComplete'])
        self.assertEqual(result['processes'][0]['version'], 'release')

    def test_unknown_stale_wrong_host_uid_or_scope_never_authorize_cleanup(self):
        for key, value in [('unknownPids', [42]), ('collected_at', 0), ('boot_id', 'wrong'),
                           ('uid', -1), ('roots', ['/unrelated']), ('schema', 'wrong')]:
            with self.subTest(key=key):
                snapshot = self.snapshot()
                snapshot[key] = value
                self.assertIsNone(self.run_probe(snapshot))

    def test_missing_untrusted_or_failed_probe_is_ambiguous(self):
        with patch.object(m, '_trusted', return_value=False), patch.object(m.subprocess, 'run') as command:
            self.assertIsNone(m.privileged_references('/owned'))
            command.assert_not_called()
        with patch.object(m, '_trusted', return_value=True), patch.object(m.subprocess, 'run',
                side_effect=m.subprocess.TimeoutExpired('probe', 30)):
            self.assertIsNone(m.privileged_references('/owned'))

    def test_malformed_snapshot_and_reference_fields_are_ambiguous(self):
        for key, value in [('unknownPids', None), ('unknownPids', False), ('roots', '/owned'),
                           ('references', {}), ('collected_at', float('nan')), ('uid', True)]:
            with self.subTest(key=key, value=value):
                snapshot = self.snapshot()
                snapshot[key] = value
                self.assertIsNone(self.run_probe(snapshot))
        for key, value in [('pid', True), ('pid', 0), ('starttime', None), ('kind', 'unknown'),
                           ('path', '/outside/file'), ('path', '/owned/../outside/file')]:
            with self.subTest(key=key):
                snapshot = self.snapshot()
                snapshot['references'][0][key] = value
                self.assertIsNone(self.run_probe(snapshot))
