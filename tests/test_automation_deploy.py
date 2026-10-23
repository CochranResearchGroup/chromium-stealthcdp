import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('automation_deploy', Path(__file__).resolve().parents[1] / 'scripts/automation_deploy.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)
REPO = Path(__file__).resolve().parents[1]


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.root = self.home / '.local/share/chromium-stealthcdp'
        self.root.mkdir(parents=True)
        self.config = self.home / '.agent-browser/config.json'
        self.config.parent.mkdir()
        self.original = {'privateSetting': 'preserve', 'service': {'browserCapabilityRegistry': {'browserExecutables': [
            {'id': m.EXECUTABLE_ID, 'executablePath': 'old'}, {'id': 'unrelated', 'executablePath': 'untouched'}]}}}
        m.atomic_json(self.config, self.original)
        self.state = Path(self.temp.name) / 'state'
        self.candidate = Path(self.temp.name) / 'candidate'
        (self.candidate / 'chrome-linux').mkdir(parents=True)
        exe = self.candidate / 'chrome-linux/chrome'
        exe.write_bytes(b'fixture browser')
        smoke = self.candidate / 'smoke.json'
        smoke.write_text(json.dumps({'success': True, 'checks': {'navigatorWebdriver': False}}))
        self.manifest = {'schema': 'chromium-stealthcdp.artifact.v1', 'artifactName': '2+stealthcdp.test',
                         'platform': 'linux', 'chromeVersion': 'Chromium 2', 'chromium': {'dirty': False},
                         'patchset': {'dirty': False, 'patchQueueSha256': 'queue'},
                         'executable': {'relativePath': 'chrome-linux/chrome', 'sha256': m.sha256(exe)},
                         'smoke': {'relativePath': 'smoke.json', 'sha256': m.sha256(smoke)}}
        m.atomic_json(self.candidate / 'manifest.json', self.manifest)
        (self.root / 'old').mkdir()
        (self.root / 'current').symlink_to('old')

    def test_failed_acceptance_restores_config_alias_and_halts(self):
        before = self.config.read_bytes()
        with patch.object(m, 'qualify_agent_browser', side_effect=m.DeploymentError('bad webdriver')):
            with self.assertRaises(m.DeploymentError):
                m.deploy(self.candidate, self.state, REPO, home=self.home)
        self.assertEqual((self.root / 'current').readlink(), Path('old'))
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse((self.home / '.local/bin/chromium-stealthcdp').exists())
        self.assertTrue((self.state / 'deployment-halted.json').exists())
        self.assertFalse((self.root / self.manifest['artifactName'] / m.OWNER_MARKER).exists())
        with self.assertRaisesRegex(m.DeploymentError, 'halted'):
            m.deploy(self.candidate, self.state, REPO, home=self.home)

    def test_installation_refuses_to_consume_disk_reserve(self):
        with patch.object(m.shutil, 'disk_usage', return_value=SimpleNamespace(free=200*1024**3)):
            with self.assertRaisesRegex(m.DeploymentError, 'free-disk reserve'):
                m.deploy(self.candidate, self.state, REPO, home=self.home)
        self.assertEqual((self.root / 'current').readlink(), Path('old'))
        self.assertFalse((self.state / 'deployment-transaction.json').exists())

    def test_success_updates_only_owned_bindings(self):
        with patch.object(m, 'qualify_agent_browser', return_value={'success': True}):
            result = m.deploy(self.candidate, self.state, REPO, home=self.home)
        self.assertEqual(result['status'], 'committed')
        config = json.loads(self.config.read_text())
        self.assertEqual(config['privateSetting'], 'preserve')
        rows = config['service']['browserCapabilityRegistry']['browserExecutables']
        self.assertEqual(rows[1], self.original['service']['browserCapabilityRegistry']['browserExecutables'][1])
        self.assertEqual(rows[0]['patchsetId'], 'queue')
        self.assertEqual(rows[0]['version'], 'Chromium 2')
        self.assertTrue((self.root / self.manifest['artifactName'] / m.OWNER_MARKER).exists())

    def test_interrupted_transaction_rolls_back_before_next_attempt(self):
        before = m._snapshot(self.config)
        m.atomic_json(self.state / 'deployment-transaction.json', {'status': 'prepared', 'before': {str(self.config): before}})
        self.config.write_text('partial new config')
        result = m.recover_deployment(self.state)
        self.assertEqual(result['status'], 'rolled_back')
        self.assertEqual(json.loads(self.config.read_text()), self.original)
        self.assertTrue((self.state / 'deployment-halted.json').exists())

    def test_retention_protects_live_versions_and_unowned_data(self):
        proc = Path(self.temp.name) / 'proc'
        proc.mkdir()
        for i in range(6):
            version = self.root / str(i)
            version.mkdir()
            m.atomic_json(version / m.OWNER_MARKER, {'schema': 'stealthcdp.automation-owned.v1', 'acceptedAt': i})
        (proc / '123').mkdir()
        (proc / '123/exe').symlink_to(self.root / '0/chrome')
        result = m.retain_versions(self.root, proc_root=proc)
        self.assertEqual({Path(x).name for x in result['removed']}, {'1', '2'})
        self.assertTrue((self.root / '0').exists())
        self.assertTrue((self.root / 'old').exists())
        self.assertTrue((self.root / '5').exists())

    def test_wrong_selected_binary_closes_only_unique_disposable_session(self):
        commands = []
        def command(argv, timeout=90):
            commands.append(argv)
            if argv[-2:] == ['get', 'browser-pid']:
                return {'pid': 2147483647}
            return {'closed': True}
        with patch.object(m.subprocess, 'run', return_value=SimpleNamespace(stdout='Chromium 2\n')), \
             patch.object(m, '_command', side_effect=command), \
             patch.object(m, 'sha256', side_effect=[self.manifest['executable']['sha256'], 'wrong']), \
             patch.object(m.os, 'readlink', return_value='/unexpected/chrome'):
            with self.assertRaisesRegex(m.DeploymentError, 'does not match'):
                m.qualify_agent_browser(self.candidate / 'chrome-linux/chrome', self.manifest, config_path=self.config)
        self.assertEqual(commands[-1][-1], 'close')
        self.assertNotIn('--all', commands[-1])
        self.assertIn('--session', commands[-1])
        self.assertEqual(json.loads(self.config.read_text()), self.original)

    def test_retention_refuses_symlink_marked_directories(self):
        outside = Path(self.temp.name) / 'outside'
        outside.mkdir()
        m.atomic_json(outside / m.OWNER_MARKER, {'schema': 'stealthcdp.automation-owned.v1', 'acceptedAt': 0})
        (self.root / 'escape').symlink_to(outside)
        proc = Path(self.temp.name) / 'proc'
        proc.mkdir()
        self.assertEqual(m.retain_versions(self.root, keep=0, proc_root=proc)['removed'], [])
        self.assertTrue(outside.exists())


if __name__ == '__main__':
    unittest.main()
