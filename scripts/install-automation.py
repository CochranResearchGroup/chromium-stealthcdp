#!/usr/bin/env python3
"""Install a committed immutable controller and a resource-bounded user timer."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from automation_profiles import BUILD_PROFILES

REPO = Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()

def unit_running(unit):
    state = run('systemctl', '--user', 'show', unit, '--property=ActiveState', '--value')
    if state in ('inactive', 'failed'):
        return False
    if state in ('active', 'activating', 'reloading', 'deactivating', 'maintenance', 'refreshing'):
        return True
    raise RuntimeError(f'Cannot establish {unit} activity: {state!r}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depot-tools', required=True, type=Path)
    parser.add_argument('--enable', action='store_true', help='Enable schedule only after baseline adoption')
    parser.add_argument('--build-profile', choices=('auto', *BUILD_PROFILES),
                        help='Select a resource budget (default: auto for new or legacy configuration)')
    args = parser.parse_args()
    if run('git', '-C', REPO, 'status', '--porcelain'):
        raise SystemExit('Commit all controller changes before installing an immutable generation')
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        raise SystemExit('ffmpeg is required for actual H264/AAC qualification')
    sha = run('git', '-C', REPO, 'rev-parse', 'HEAD')
    home = Path.home()
    root = home / '.local/lib/chromiumQ-automation'
    generation = root / 'generations' / sha
    generation.parent.mkdir(parents=True, exist_ok=True)
    if not generation.exists():
        run('git', 'clone', '--no-hardlinks', REPO, generation)
        run('git', '-C', generation, 'checkout', '--detach', sha)
    config = home / '.config/chromiumQ/automation.json'
    legacy_config = home / '.config/chromium-stealthcdp/automation.json'
    source_config = config if config.exists() else legacy_config
    previous_config = json.loads(source_config.read_text()) if source_config.exists() else {}
    default_state = (home / '.local/state/chromium-stealthcdp/automation'
                     if source_config == legacy_config and legacy_config.exists()
                     else home / '.local/state/chromiumQ/automation')
    # Preserve run paths, pinned queues and the shared controller lock on upgrade.
    state = Path(previous_config.get('state_dir', default_state))
    if not state.is_absolute():
        parser.error('state_dir must be absolute')
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    config.parent.mkdir(parents=True, exist_ok=True)
    profile_name = args.build_profile or previous_config.get('build_profile', 'auto')
    if profile_name not in ('auto', *BUILD_PROFILES):
        parser.error(f'unknown build profile: {profile_name}')
    config.write_text(json.dumps({**previous_config, 'schema': 'stealthcdp.automation-config.v1', 'source_repo': str(generation),
                                 'build_profile': profile_name, 'state_dir': str(state), 'depot_tools': str(args.depot_tools.resolve(strict=True)),
                                 'agent_browser': str(home / '.local/bin/agent-browser')}, indent=2) + '\n')
    config.chmod(0o600)
    current = root / 'current'
    temporary = root / '.current-new'
    temporary.unlink(missing_ok=True)
    temporary.symlink_to(generation)
    os.replace(temporary, current)
    # Paths use systemd quoting, not a shell. Escape % specifier in concrete paths.
    def quote(path):
        return '"' + str(path).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'
    units = home / '.config/systemd/user'
    units.mkdir(parents=True, exist_ok=True)
    path = ':'.join([str(home / '.local/bin'), str(args.depot_tools.resolve()), str(Path(ffmpeg).parent), '/usr/local/bin', '/usr/bin', '/bin'])
    (units / 'chromiumQ-update.service').write_text(f'''[Unit]
Description=Select the chromiumQ build profile
PropagatesStopTo=chromiumQ-build@conservative.service chromiumQ-build@standard.service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {quote(current / 'scripts/automation_trigger.py')} --config {quote(config)}
Environment=PYTHONDONTWRITEBYTECODE=1
TimeoutStartSec={max(profile.hours for profile in BUILD_PROFILES.values()) + 1}h
''')
    for name, profile in BUILD_PROFILES.items():
        service = f'''[Unit]
Description=Qualify, publish and deploy chromiumQ Linux Stable
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {quote(current / 'scripts/automation.py')} --config {quote(config)} run --build-profile {name}
Environment="PATH={path}"
ExecStopPost=-/usr/bin/python3 {quote(current / 'scripts/automation_notify.py')} --config {quote(config)} service-result
Environment=PYTHONDONTWRITEBYTECODE=1
WorkingDirectory={quote(state)}
UMask=0077
Nice=10
IOSchedulingClass=idle
CPUQuota={100 * profile.jobs}%
MemoryMax={profile.memory_gib}G
MemorySwapMax=0
TimeoutStartSec={profile.hours}h
TimeoutStopSec=30s
KillMode=control-group
Restart=no
'''
        (units / f'chromiumQ-build@{name}.service').write_text(service)
    (units / 'chromiumQ-update.timer').write_text('''[Unit]
Description=Weekly chromiumQ Stable check

[Timer]
OnCalendar=Sun *-*-* 03:00:00 America/Chicago
Persistent=true
Unit=chromiumQ-update.service

[Install]
WantedBy=timers.target
''')
    launcher = home / '.local/bin/chromiumQ-update'
    launcher.parent.mkdir(parents=True, exist_ok=True)
    # Manual run uses the very same bounded service, rather than bypassing cgroups.
    launcher.write_text('''#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
home=Path.home()
if len(sys.argv)==1 or sys.argv[1:] == ['run']:
    sys.exit(subprocess.call(['systemctl','--user','start','--no-block','chromiumQ-update.service']))
if sys.argv[1:] == ['logs']:
    os.execvp('journalctl',['journalctl','--user','-u','chromiumQ-update.service','-u','chromiumQ-build@*.service','-n','80','--no-pager'])
if sys.argv[1:] == ['status']:
    os.execvp('python3',['python3',str(home/'.local/lib/chromiumQ-automation/current/scripts/automation.py'),'--config',str(home/'.config/chromiumQ/automation.json'),'status'])
raise SystemExit('Usage: chromiumQ-update [run|status|logs]')
''')
    launcher.chmod(0o755)
    run('systemd-analyze', '--user', 'verify', units / 'chromiumQ-update.service', units / 'chromiumQ-update.timer',
        *(units / f'chromiumQ-build@{name}.service' for name in BUILD_PROFILES))
    run('systemctl', '--user', 'daemon-reload')
    if args.enable:
        baseline = state / 'baseline.json'
        if not baseline.exists() or not json.loads(baseline.read_text()).get('acceptance', {}).get('success'):
            raise SystemExit('Adopt and accept published installed baseline before enabling timer')
        legacy_timer = 'chromium-stealthcdp-update.timer'
        legacy_services = ('chromium-stealthcdp-update.service',
                           *(f'chromium-stealthcdp-build@{name}.service' for name in BUILD_PROFILES))
        if any(unit_running(service) for service in legacy_services):
            raise SystemExit('Wait for the legacy updater run to finish before switching timers')
        legacy_enabled = (units / 'timers.target.wants' / legacy_timer).is_symlink()
        legacy_active = unit_running(legacy_timer)
        if legacy_enabled or legacy_active:
            run('systemctl', '--user', 'disable', '--now', legacy_timer)
        try:
            if any(unit_running(service) for service in legacy_services):
                raise SystemExit('Legacy updater started during timer handoff')
            run('systemctl', '--user', 'enable', '--now', 'chromiumQ-update.timer')
        except BaseException:
            run('systemctl', '--user', 'disable', '--now', 'chromiumQ-update.timer')
            if legacy_enabled:
                run('systemctl', '--user', 'enable', legacy_timer)
            if legacy_active:
                run('systemctl', '--user', 'start', legacy_timer)
            raise
    print(json.dumps({'generation': str(generation), 'config': str(config), 'state': str(state), 'build_profile': profile_name, 'timer_enabled': args.enable}, indent=2))

if __name__ == '__main__':
    main()
