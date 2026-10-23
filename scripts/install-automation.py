#!/usr/bin/env python3
"""Install a committed immutable controller and a resource-bounded user timer."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

REPO = Path(__file__).resolve().parents[1]

def run(*args):
    return subprocess.check_output([str(x) for x in args], text=True).strip()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--depot-tools', required=True, type=Path)
    parser.add_argument('--enable', action='store_true', help='Enable schedule only after baseline adoption')
    args = parser.parse_args()
    if run('git', '-C', REPO, 'status', '--porcelain'):
        raise SystemExit('Commit all controller changes before installing an immutable generation')
    sha = run('git', '-C', REPO, 'rev-parse', 'HEAD')
    home = Path.home()
    root = home / '.local/lib/chromium-stealthcdp-automation'
    generation = root / 'generations' / sha
    generation.parent.mkdir(parents=True, exist_ok=True)
    if not generation.exists():
        run('git', 'clone', '--no-hardlinks', REPO, generation)
        run('git', '-C', generation, 'checkout', '--detach', sha)
    state = home / '.local/state/chromium-stealthcdp/automation'
    state.mkdir(parents=True, exist_ok=True, mode=0o700)
    config = home / '.config/chromium-stealthcdp/automation.json'
    config.parent.mkdir(parents=True, exist_ok=True)
    previous_config = json.loads(config.read_text()) if config.exists() else {}
    config.write_text(json.dumps({**previous_config, 'schema': 'stealthcdp.automation-config.v1', 'source_repo': str(generation),
                                 'state_dir': str(state), 'depot_tools': str(args.depot_tools.resolve(strict=True)),
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
    path = ':'.join([str(home / '.local/bin'), str(args.depot_tools.resolve()), '/usr/local/bin', '/usr/bin', '/bin'])
    service = f'''[Unit]
Description=Qualify, publish and deploy Chromium StealthCDP Linux Stable
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 {quote(current / 'scripts/automation.py')} --config {quote(config)} run
Environment="PATH={path}"
ExecStopPost=-/usr/bin/python3 {quote(current / 'scripts/automation_notify.py')} --config {quote(config)} service-result
Environment=PYTHONDONTWRITEBYTECODE=1
WorkingDirectory=%h/.local/state/chromium-stealthcdp/automation
UMask=0077
Nice=10
IOSchedulingClass=idle
CPUQuota=800%
MemoryMax=32G
MemorySwapMax=0
TimeoutStartSec=12h
TimeoutStopSec=30s
KillMode=control-group
Restart=no
'''
    (units / 'chromium-stealthcdp-update.service').write_text(service)
    (units / 'chromium-stealthcdp-update.timer').write_text('''[Unit]
Description=Daily Chromium StealthCDP Stable check

[Timer]
OnCalendar=*-*-* 03:00:00 America/Chicago
Persistent=true
Unit=chromium-stealthcdp-update.service

[Install]
WantedBy=timers.target
''')
    launcher = home / '.local/bin/chromium-stealthcdp-update'
    launcher.parent.mkdir(parents=True, exist_ok=True)
    # Manual run uses the very same bounded service, rather than bypassing cgroups.
    launcher.write_text('''#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
home=Path.home()
if len(sys.argv)==1 or sys.argv[1:] == ['run']:
    sys.exit(subprocess.call(['systemctl','--user','start','--no-block','chromium-stealthcdp-update.service']))
if sys.argv[1:] == ['logs']:
    os.execvp('journalctl',['journalctl','--user','-u','chromium-stealthcdp-update.service','-n','80','--no-pager'])
if sys.argv[1:] == ['status']:
    os.execvp('python3',['python3',str(home/'.local/lib/chromium-stealthcdp-automation/current/scripts/automation.py'),'--config',str(home/'.config/chromium-stealthcdp/automation.json'),'status'])
raise SystemExit('Usage: chromium-stealthcdp-update [run|status|logs]')
''')
    launcher.chmod(0o755)
    run('systemd-analyze', '--user', 'verify', units / 'chromium-stealthcdp-update.service', units / 'chromium-stealthcdp-update.timer')
    run('systemctl', '--user', 'daemon-reload')
    if args.enable:
        baseline = state / 'baseline.json'
        if not baseline.exists() or not json.loads(baseline.read_text()).get('acceptance', {}).get('success'):
            raise SystemExit('Adopt and accept published installed baseline before enabling timer')
        run('systemctl', '--user', 'enable', '--now', 'chromium-stealthcdp-update.timer')
    print(json.dumps({'generation': str(generation), 'config': str(config), 'state': str(state), 'timer_enabled': args.enable}, indent=2))

if __name__ == '__main__':
    main()
