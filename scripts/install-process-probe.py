#!/usr/bin/python3 -I
"""Provision an optional root-owned read-only probe; invoke explicitly as root."""
import argparse
import json
import os
from pathlib import Path
import pwd
import stat
import subprocess
import tempfile


def install(path, data, mode):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)
    for parent in (path.parent, *path.parent.parents):
        info = parent.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
            raise RuntimeError('Installation ancestors must be protected by root')
    if path.is_symlink():
        raise RuntimeError('Refuse symlink installation path')
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            os.fchmod(stream.fileno(), mode)
            os.fchown(stream.fileno(), 0, 0)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', required=True)
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit('Run this installer explicitly as root')
    account = pwd.getpwnam(args.user)
    if account.pw_uid == 0 or not args.user.replace('_', '').replace('-', '').isalnum():
        raise SystemExit('Require a named non-root account')
    home = Path(account.pw_dir)
    config = {'uid': account.pw_uid, 'roots': [
        str(home / '.local/state/chromium-stealthcdp/automation/builds'),
        str(home / '.local/share/chromium-stealthcdp')]}
    probe = Path('/usr/local/libexec/chromium-stealthcdp-process-probe')
    config_path = Path('/etc/chromium-stealthcdp/process-census.json')
    rule = f'{args.user} ALL=(root) NOPASSWD: {probe} ""\n'
    # Validate the exact no-arguments rule before installing privilege policy.
    with tempfile.NamedTemporaryFile(mode='w') as stream:
        stream.write(rule)
        stream.flush()
        subprocess.run(['/usr/sbin/visudo', '-cf', stream.name], check=True)
    install(config_path, (json.dumps(config, indent=2) + '\n').encode(), 0o644)
    install(probe, Path(__file__).with_name('automation_process_probe.py').read_bytes(), 0o755)
    install(Path('/etc/sudoers.d/chromium-stealthcdp-process-probe'), rule.encode(), 0o440)
    print(json.dumps({'probe': str(probe), 'config': str(config_path), 'uid': account.pw_uid}))


if __name__ == '__main__':
    main()
