"""No provider/process effects: guarded shared-host refresh and rollback ordering."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('refresh_subject', Path(__file__).resolve().parents[1] / 'scripts/automation_deploy.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class RuntimeRefreshTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.root = self.home / '.local/share/chromium-stealthcdp'
        self.selected = self.home / '.local/lib/agent-browser/current/bin/agent-browser'
        self.selected.parent.mkdir(parents=True)
        self.selected.write_text('selected executable')
        self.fragment = self.home / '.config/systemd/user/agent-browser-runtime-host.service'
        self.fragment.parent.mkdir(parents=True)
        self.fragment.write_text('[Service]\nKillMode=process\n')
        self.unit = {'FragmentPath': str(self.fragment), 'LoadState': 'loaded', 'ActiveState': 'active', 'SubState': 'running',
                     'MainPID': '101', 'KillMode': 'process'}
        self.identity = {'pid': 101, 'startTicks': '10', 'executable': str(self.selected.resolve()),
                         'uid': m.os.getuid()}
        self.browser = {'pid': 202, 'startTicks': '20', 'executable': '/installed/old/chrome',
                        'uid': m.os.getuid()}

    def exercise(self, *, mode='process', jobs=None, inventory=None, wrong_host=False, changed_browser=False):
        before = dict(self.unit, KillMode=mode)
        after = dict(self.unit, MainPID='303')
        commands = []
        ready = [False]

        def systemd(argv):
            commands.append(argv)
            if 'restart' in argv:
                ready[0] = True
                return ''
            return after if ready[0] else before

        def identity(pid):
            if pid == 202:
                return dict(self.browser, startTicks='21') if changed_browser and ready[0] else dict(self.browser)
            return dict(self.identity, pid=pid, startTicks=str(pid),
                        executable='/wrong/agent-browser' if wrong_host else str(self.selected.resolve()))

        def command(argv, **kwargs):
            commands.append(argv)
            if inventory is not None:
                return inventory
            count = len(jobs or [])
            return {'count': count, 'matched': count, 'total': count, 'jobs': jobs or []}

        with patch.object(m, '_runtime_real_home', return_value=self.home), \
             patch.object(m, '_runtime_systemd', side_effect=systemd), \
             patch.object(m, '_runtime_process_identity', side_effect=identity), \
             patch.object(m, '_runtime_browser_roots', return_value=[self.browser]), \
             patch.object(m, '_command', side_effect=command):
            result = m.refresh_managed_runtime(self.root, home=self.home, agent_browser=str(self.selected))
        return result, commands

    def test_process_census_accepts_flattened_and_ordinary_root_argv(self):
        for raw in (b'/installed/chrome --user-data-dir=/owned/profile --disable-gpu ',
                    b'/installed/chrome\0--user-data-dir=/owned/profile\0--disable-gpu\0'):
            with self.subTest(raw=raw):
                self.assertTrue(m._runtime_is_browser_root(raw))

    def test_process_census_excludes_children_in_both_argv_forms(self):
        for raw in (b'/installed/chrome --type=renderer --user-data-dir=/owned/profile ',
                    b'/installed/chrome\0--type=gpu-process\0'):
            with self.subTest(raw=raw):
                self.assertFalse(m._runtime_is_browser_root(raw))
        with self.assertRaisesRegex(m.DeploymentError, 'incomplete'):
            m._runtime_is_browser_root(b'/installed/chrome --disable-gpu ')

    def test_foreign_home_is_explicitly_skipped_without_systemd(self):
        with patch.object(m, '_runtime_systemd') as systemd:
            result = m.refresh_managed_runtime(self.root, home=self.home, agent_browser=str(self.selected))
        self.assertEqual(result['state'], 'skipped_isolated_home')
        self.assertFalse(result['restartAttempted'])
        systemd.assert_not_called()

    def test_home_environment_override_cannot_reach_real_systemd(self):
        with patch.dict(m.os.environ, {'HOME': str(self.home)}), \
             patch.object(m, '_runtime_systemd') as systemd:
            result = m.refresh_managed_runtime(self.root, home=self.home)
        self.assertEqual(result['state'], 'skipped_isolated_home')
        systemd.assert_not_called()

    def test_managed_mcp_proof_skips_isolated_home_without_subprocess(self):
        with patch.object(m.subprocess, 'run') as run:
            result = m.qualify_managed_browser(self.root, {}, self.home / 'state',
                                               Path('/fixture-repo'), home=self.home)
        self.assertEqual(result, {'state': 'skipped_isolated_home', 'browserLaunched': False})
        run.assert_not_called()

    def test_success_restarts_only_known_unit_and_preserves_original_browser(self):
        result, commands = self.exercise()
        self.assertEqual(result['state'], 'ready')
        self.assertTrue(result['restartAttempted'])
        self.assertEqual(result['preservedBrowserPids'], [202])
        self.assertEqual([x for x in commands if 'restart' in x],
                         [['--user', 'restart', 'agent-browser-runtime-host.service']])

    def test_wrong_kill_mode_refuses_before_restart(self):
        with self.assertRaisesRegex(m.DeploymentError, 'KillMode') as caught:
            self.exercise(mode='control-group')
        self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_active_jobs_refuse_before_restart(self):
        with self.assertRaisesRegex(m.DeploymentError, 'active service jobs') as caught:
            self.exercise(jobs=[{'id': 'active', 'state': 'running'}])
        self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_complete_terminal_inventory_passes_without_state_filter(self):
        terminal = [{'id': str(i), 'state': state} for i, state in enumerate(
            ('succeeded', 'failed', 'cancelled', 'timed_out'))]
        result, commands = self.exercise(jobs=terminal)
        self.assertEqual(result['state'], 'ready')
        self.assertEqual(result['serviceJobs']['count'], 4)
        queries = [call for call in commands if 'jobs' in call]
        self.assertTrue(queries)
        for call in queries:
            self.assertNotIn('--state', call)
            self.assertEqual(call[call.index('--limit') + 1], '10000')

    def test_filtered_or_truncated_terminal_rows_cannot_mask_active_jobs(self):
        # The observed installed CLI ignored --state and returned a terminal tail.
        # Its count alone cannot prove omitted rows are terminal.
        inventory = {'count': 1, 'matched': 2, 'total': 2,
                     'jobs': [{'id': 'old', 'state': 'succeeded'}]}
        with self.assertRaisesRegex(m.DeploymentError, 'complete service jobs') as caught:
            self.exercise(inventory=inventory)
        self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_nonterminal_or_unknown_job_states_fail_closed(self):
        for state in ('queued', 'running', 'waiting_profile_lease', 'unknown', None):
            with self.subTest(state=state):
                with self.assertRaisesRegex(m.DeploymentError, 'active service jobs') as caught:
                    self.exercise(jobs=[{'id': 'job', 'state': state}])
                self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_missing_or_invalid_snapshot_counts_fail_closed(self):
        for inventory in ({'count': 0, 'jobs': []},
                          {'count': False, 'matched': 0, 'total': 0, 'jobs': []},
                          {'count': 0, 'matched': '0', 'total': 0, 'jobs': []},
                          {'count': 0, 'matched': 0, 'total': 1, 'jobs': []}):
            with self.subTest(inventory=inventory):
                with self.assertRaisesRegex(m.DeploymentError, 'complete service jobs') as caught:
                    self.exercise(inventory=inventory)
                self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_wrong_selected_host_refuses_before_restart(self):
        with self.assertRaisesRegex(m.DeploymentError, 'selected executable') as caught:
            self.exercise(wrong_host=True)
        self.assertFalse(caught.exception.receipt['restartAttempted'])

    def test_browser_identity_change_after_restart_is_not_accepted(self):
        with self.assertRaisesRegex(m.DeploymentError, 'retained browser') as caught:
            self.exercise(changed_browser=True)
        self.assertTrue(caught.exception.receipt['restartAttempted'])


class RefreshDeploymentOrderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / 'home'
        self.root = self.home / '.local/share/chromium-stealthcdp'
        (self.root / 'old').mkdir(parents=True)
        (self.root / 'current').symlink_to('old')
        self.config = self.home / '.agent-browser/config.json'
        self.original = {'service': {'browserCapabilityRegistry': {'browserExecutables': [
            {'id': m.EXECUTABLE_ID, 'executablePath': 'old'}]}}}
        m.atomic_json(self.config, self.original)
        self.candidate = Path(self.temp.name) / 'candidate'
        self.candidate.mkdir()
        self.manifest = {'artifactName': 'new', 'chromeVersion': 'Chromium 157',
                         'executable': {'relativePath': 'chrome-linux/chrome'},
                         'patchset': {'patchQueueSha256': 'queue'}}
        m.atomic_json(self.candidate / 'manifest.json', self.manifest)
        self.state = Path(self.temp.name) / 'state'

    def test_acceptance_failure_restores_files_before_rollback_refresh(self):
        from types import SimpleNamespace
        calls = []

        def installer(*args, **kwargs):
            (self.root / 'current').unlink()
            (self.root / 'current').symlink_to('new')
            return SimpleNamespace(returncode=0)

        def refresh(root, **kwargs):
            calls.append('refresh')
            if len(calls) == 1:
                self.assertEqual((self.root / 'current').readlink(), Path('new'))
                self.assertNotEqual(self.config.read_text(), json.dumps(self.original))
            else:
                self.assertEqual((self.root / 'current').readlink(), Path('old'))
                self.assertEqual(json.loads(self.config.read_text()), self.original)
            receipt = {'state': 'ready', 'restartAttempted': True}
            if kwargs.get('record'):
                kwargs['record'](receipt)
            return receipt

        with patch.object(m.subprocess, 'run', side_effect=installer),              patch.object(m, 'refresh_managed_runtime', side_effect=refresh),              patch.object(m, 'qualify_agent_browser', side_effect=m.DeploymentError('acceptance failed')),              patch.object(m.shutil, 'disk_usage', return_value=SimpleNamespace(free=1024**4)):
            with self.assertRaisesRegex(m.DeploymentError, 'acceptance failed'):
                m.deploy(self.candidate, self.state, Path('/fixture-repo'), home=self.home)
        journal = json.loads((self.state / 'deployment-transaction.json').read_text())
        self.assertEqual(journal['status'], 'rolled_back')
        self.assertEqual(len(calls), 2)
        self.assertEqual(journal['runtimeRefresh']['state'], 'ready')
        self.assertEqual(journal['rollbackRuntimeRefresh']['state'], 'ready')

    def test_forward_order_is_refresh_managed_mcp_then_cli(self):
        from types import SimpleNamespace
        calls = []
        def refresh(*args, **kwargs):
            calls.append('refresh')
            return {'state': 'ready', 'restartAttempted': True}
        def managed(*args, **kwargs):
            calls.append('managed_mcp')
            return {'success': True, 'profileWritersGone': True}
        def cli(*args, **kwargs):
            calls.append('cli')
            return {'success': True}
        with patch.object(m.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
             patch.object(m, 'refresh_managed_runtime', side_effect=refresh), \
             patch.object(m, 'qualify_managed_browser', side_effect=managed), \
             patch.object(m, 'qualify_agent_browser', side_effect=cli), \
             patch.object(m, 'inspect_live_versions', return_value={'processes': []}), \
             patch.object(m.shutil, 'disk_usage', return_value=SimpleNamespace(free=1024**4)):
            result = m.deploy(self.candidate, self.state, Path('/fixture-repo'), home=self.home)
        self.assertEqual(calls, ['refresh', 'managed_mcp', 'cli'])
        self.assertEqual(result['status'], 'committed')
        self.assertTrue(result['managedAcceptance']['profileWritersGone'])

    def test_interrupted_transaction_restores_before_refreshing_old_config(self):
        import json
        before = m._snapshot(self.config)
        self.config.write_text('partial config')
        m.atomic_json(self.state / 'deployment-transaction.json', {
            'status': 'prepared', 'before': {str(self.config): before},
            'runtimeRefreshHome': str(self.home)})

        def refresh(*args, **kwargs):
            self.assertEqual(json.loads(self.config.read_text()), self.original)
            return {'state': 'ready', 'restartAttempted': True}

        with patch.object(m, 'refresh_managed_runtime', side_effect=refresh) as refreshed:
            journal = m.recover_deployment(self.state)
        self.assertEqual(journal['status'], 'rolled_back')
        self.assertEqual(journal['rollbackRuntimeRefresh']['state'], 'ready')
        refreshed.assert_called_once()

    def test_rollback_refresh_failure_stays_halted_and_attributable(self):
        before = m._snapshot(self.config)
        m.atomic_json(self.state / 'deployment-transaction.json', {
            'status': 'prepared', 'before': {str(self.config): before},
            'runtimeRefreshHome': str(self.home)})
        with patch.object(m, 'refresh_managed_runtime', side_effect=m.DeploymentError(
                'host unavailable', {'state': 'failed', 'restartAttempted': False})):
            journal = m.recover_deployment(self.state)
        self.assertEqual(journal['status'], 'rollback_refresh_failed')
        self.assertEqual(journal['rollbackRuntimeRefresh']['state'], 'failed')
        self.assertTrue((self.state / 'deployment-halted.json').exists())


if __name__ == '__main__':
    unittest.main()
