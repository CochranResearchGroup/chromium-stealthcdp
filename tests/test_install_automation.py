"""Verify the generated service and schedule with an isolated home."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
SPEC = importlib.util.spec_from_file_location('install_automation', SCRIPTS / 'install-automation.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def test_weekly_timer_and_selectable_build_profiles(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            depot = home / 'depot_tools'
            depot.mkdir()
            config = home / '.config/chromiumQ/automation.json'
            units = home / '.config/systemd/user'

            def git_or_systemd(*args):
                return 'a' * 40 if args[-2:] == ('rev-parse', 'HEAD') else ''

            with patch.object(Path, 'home', return_value=home), \
                 patch.object(installer, 'run', side_effect=git_or_systemd), \
                 patch.object(installer.shutil, 'which', return_value='/usr/bin/ffmpeg'):
                for args, profile in [
                    ([], 'auto'),
                    (['--build-profile', 'standard'], 'standard'),
                    ([], 'standard'),
                ]:
                    with self.subTest(profile=profile, args=args), \
                         patch.object(sys, 'argv', ['install-automation', '--depot-tools', str(depot), *args]):
                        installer.main()
                        self.assertEqual(json.loads(config.read_text())['build_profile'], profile)
                        dispatcher = (units / 'chromiumQ-update.service').read_text()
                        self.assertIn('automation_trigger.py', dispatcher)
                        self.assertIn('PropagatesStopTo=chromiumQ-build@conservative.service '
                                      'chromiumQ-build@standard.service\n', dispatcher)
                        for name, cpu, memory, timeout in [
                            ('conservative', '200%', '16G', '36h'),
                            ('standard', '800%', '32G', '12h'),
                        ]:
                            service = (units / f'chromiumQ-build@{name}.service').read_text()
                            self.assertIn(f'run --build-profile {name}\n', service)
                            self.assertIn(f'CPUQuota={cpu}\n', service)
                            self.assertIn(f'MemoryMax={memory}\n', service)
                            self.assertIn('MemorySwapMax=0\n', service)
                            self.assertIn(f'TimeoutStartSec={timeout}\n', service)
                        timer = (units / 'chromiumQ-update.timer').read_text()
                        self.assertIn('OnCalendar=Sun *-*-* 03:00:00 America/Chicago\n', timer)
                        self.assertIn('Persistent=true\n', timer)


    def test_migration_preserves_legacy_state_and_switches_one_timer(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            depot = home / 'depot_tools'
            depot.mkdir()
            state = home / 'owned-updater-state'
            state.mkdir()
            (state / 'baseline.json').write_text(json.dumps({
                'version': '157.0.8103.78',
                'publication': {'tag': 'v157.0.8103.78-fixture'},
                'deployment': {
                    'status': 'committed',
                    'acceptance': {'success': True, 'version': 'Chromium 157.0.8103.78'},
                },
            }))
            config = home / '.config/chromium-stealthcdp/automation.json'
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({'state_dir': str(state), 'build_profile': 'conservative',
                                          'approved_queue': 'existing-pinned-queue'}))
            legacy_timer = 'chromium-stealthcdp-update.timer'
            enabled = {legacy_timer}
            def command(*args):
                if args[-2:] == ('rev-parse', 'HEAD'):
                    return 'a' * 40
                if args[:3] == ('systemctl', '--user', 'show'):
                    return 'active' if args[3] in enabled else 'inactive'
                if args[:3] == ('systemctl', '--user', 'disable'):
                    enabled.discard(args[-1])
                if args[:3] == ('systemctl', '--user', 'enable'):
                    self.assertFalse(enabled, 'overlapping updater timers')
                    enabled.add(args[-1])
                return ''
            with patch.object(Path, 'home', return_value=home), \
                 patch.object(installer, 'run', side_effect=command), \
                 patch.object(installer.shutil, 'which', return_value='/usr/bin/ffmpeg'), \
                 patch.object(sys, 'argv', ['install-automation', '--depot-tools', str(depot), '--enable']):
                installer.main()
            self.assertEqual(enabled, {'chromiumQ-update.timer'})
            new = json.loads((home / '.config/chromiumQ/automation.json').read_text())
            self.assertEqual(new['state_dir'], str(state))
            self.assertEqual(new['build_profile'], 'conservative')
            self.assertEqual(new['approved_queue'], 'existing-pinned-queue')
            unit = home / '.config/systemd/user/chromiumQ-build@conservative.service'
            self.assertIn(f'WorkingDirectory={state}\n', unit.read_text())


    def test_updater_baseline_requires_a_published_committed_matching_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            baseline = Path(directory) / 'baseline.json'
            self.assertFalse(installer.baseline_accepted(baseline))
            for status, accepted_version, publication, expected in [
                ('committed', 'Chromium 157', {'tag': 'v157'}, True),
                ('rolled_back', 'Chromium 157', {'tag': 'v157'}, False),
                ('committed', 'Chromium 156', {'tag': 'v157'}, False),
                ('committed', 'Chromium 157', {}, False),
            ]:
                with self.subTest(status=status, accepted_version=accepted_version, publication=publication):
                    baseline.write_text(json.dumps({
                        'version': '157', 'publication': publication,
                        'deployment': {'status': status, 'acceptance': {
                            'success': True, 'version': accepted_version,
                        }},
                    }))
                    self.assertEqual(installer.baseline_accepted(baseline), expected)
            baseline.write_text(json.dumps({'acceptance': {'success': True}}))
            self.assertTrue(installer.baseline_accepted(baseline))

    def test_dispatch_selects_a_bounded_unit_for_each_trigger(self):
        import automation_trigger

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / 'automation.json'
            for mode, memory, expected in [
                ('auto', 32 * 1024**2, 'standard'),
                ('auto', 32 * 1024**2 - 1, 'conservative'),
                ('auto', 16 * 1024**2, 'conservative'),
                ('auto', 16 * 1024**2 - 1, 'conservative'),
                ('conservative', 48 * 1024**2, 'conservative'),
                ('standard', 24 * 1024**2, 'standard'),
            ]:
                config.write_text(json.dumps({'build_profile': mode}))
                with self.subTest(mode=mode, memory=memory), \
                     patch.object(sys, 'argv', ['automation-trigger', '--config', str(config)]), \
                     patch.object(automation_trigger, 'available_memory_kib', return_value=memory), \
                     patch.object(automation_trigger.subprocess, 'call', return_value=0) as start:
                    self.assertEqual(automation_trigger.main(), 0)
                    start.assert_called_once_with(
                        ['systemctl', '--user', 'start', f'chromiumQ-build@{expected}.service'])
