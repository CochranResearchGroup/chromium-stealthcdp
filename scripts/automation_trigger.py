#!/usr/bin/env python3
"""Start the bounded service selected for the current trigger."""
import argparse
import json
from pathlib import Path
import subprocess

from automation_profiles import BUILD_PROFILES, available_memory_kib, select_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    args = parser.parse_args()
    mode = json.loads(args.config.read_text()).get('build_profile', 'auto')
    if mode not in ('auto', *BUILD_PROFILES):
        parser.error(f'unknown build profile: {mode}')
    available = available_memory_kib(Path('/proc/meminfo'))
    profile = select_profile(mode, available)
    print(f'Build profile {profile} selected with {available} KiB available', flush=True)
    return subprocess.call(['systemctl', '--user', 'start', f'chromium-stealthcdp-build@{profile}.service'])


if __name__ == '__main__':
    raise SystemExit(main())
