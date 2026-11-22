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
            config = home / '.config/chromium-stealthcdp/automation.json'
            units = home / '.config/systemd/user'

            def git_or_systemd(*args):
                return 'a' * 40 if args[-2:] == ('rev-parse', 'HEAD') else ''

            with patch.object(Path, 'home', return_value=home), \
                 patch.object(installer, 'run', side_effect=git_or_systemd), \
                 patch.object(installer.shutil, 'which', return_value='/usr/bin/ffmpeg'):
                for args, profile, cpu, memory, timeout in [
                    ([], 'conservative', '200%', '16G', '36h'),
                    (['--build-profile', 'standard'], 'standard', '800%', '32G', '12h'),
                    ([], 'standard', '800%', '32G', '12h'),
                ]:
                    with self.subTest(profile=profile, args=args), \
                         patch.object(sys, 'argv', ['install-automation', '--depot-tools', str(depot), *args]):
                        installer.main()
                        self.assertEqual(json.loads(config.read_text())['build_profile'], profile)
                        service = (units / 'chromium-stealthcdp-update.service').read_text()
                        self.assertIn(f'CPUQuota={cpu}\n', service)
                        self.assertIn(f'MemoryMax={memory}\n', service)
                        self.assertIn('MemorySwapMax=0\n', service)
                        self.assertIn(f'TimeoutStartSec={timeout}\n', service)
                        timer = (units / 'chromium-stealthcdp-update.timer').read_text()
                        self.assertIn('OnCalendar=Sun *-*-* 03:00:00 America/Chicago\n', timer)
                        self.assertIn('Persistent=true\n', timer)
