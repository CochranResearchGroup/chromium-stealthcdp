import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('automation_repair', Path(__file__).resolve().parents[1] / 'scripts/automation_repair.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class RepairAdmissionTests(unittest.TestCase):
    def test_reports_are_idempotent_per_pinned_target_without_worker_effects(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = {'target': {'version': '156.1', 'patchQueueSha256': 'queue'}, 'id': 'first'}
            first = m.draft(run, tmp, Path(tmp) / 'source')
            run['id'] = 'second'
            second = m.draft(run, tmp, Path(tmp) / 'source')
            self.assertEqual(first, second)
            self.assertEqual(len(list((Path(tmp) / 'repair-reports').glob('*.json'))), 1)
            self.assertFalse(first['workerStarted'])
            self.assertFalse(first['attemptConsumed'])
            self.assertEqual(first['status'], 'report_only')
            self.assertEqual(first['policy']['maximumWallSeconds'], 1800)
            self.assertFalse((Path(tmp) / 'source').exists())

    def test_changed_input_gets_new_report_and_missing_target_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            one = m.draft({'target': {'version': '1', 'patchQueueSha256': 'old'}}, tmp, tmp)
            two = m.draft({'target': {'version': '1', 'patchQueueSha256': 'new'}}, tmp, tmp)
            self.assertNotEqual(one['targetIdentity'], two['targetIdentity'])
            with self.assertRaises(ValueError):
                m.draft({'id': 'transient'}, tmp, tmp)

    def test_no_receipt_or_environment_can_enable_unqualified_worker(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'repair-qualified.json').write_text(json.dumps({'qualified': True}))
            with patch.dict(m.os.environ, {'REPAIR_ENABLED': 'true', 'GH_TOKEN': 'secret'}):
                result = m.draft({'target': {'version': '1'}}, tmp, tmp)
            self.assertEqual(result['status'], 'report_only')
            self.assertNotIn('secret', json.dumps(result))

    def test_credentials_and_control_sockets_not_inherited(self):
        result = m.sanitized_environment({'PATH': '/usr/bin', 'GH_TOKEN': 'a', 'OPENAI_API_KEY': 'b',
                                         'SSH_AUTH_SOCK': '/socket', 'DBUS_SESSION_BUS_ADDRESS': '/bus',
                                         'GIT_ASKPASS': '/helper', 'PASSWORD': 'c'})
        self.assertEqual(result, {'PATH': '/usr/bin'})

    def test_all_configured_effect_providers_explicitly_disabled(self):
        config = {'mcp_servers': {'some-server': {'url': 'private'}}, 'plugins': {'plugin@remote': {'enabled': True}}}
        args = m.disabled_effect_overrides(config)
        self.assertIn('mcp_servers.some-server.enabled=false', args)
        self.assertIn('plugins.plugin@remote.enabled=false', args)
        self.assertNotIn('private', str(args))
        with self.assertRaises(ValueError):
            m.disabled_effect_overrides({'mcp_servers': {'ambiguous.name': {}}})


if __name__ == '__main__':
    unittest.main()
