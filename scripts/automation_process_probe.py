#!/usr/bin/python3 -I
"""Root-owned, read-only process census for fixed Chromium retention roots.

The CLI accepts no arguments or caller-selected paths. Provision this file and
its configuration as root-owned files; it imports only the standard library.
"""
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

CONFIG = Path('/etc/chromium-stealthcdp/process-census.json')
SCHEMA = 'stealthcdp.process-census.v1'


def _identity(process):
    # comm may contain spaces and parentheses, so parse after its final ')'.
    fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
    return fields[0], int(fields[19])


def _under(path, roots):
    path = Path(path.removesuffix(' (deleted)'))
    return path.is_absolute() and any(path.is_relative_to(root) for root in roots)


def collect(uid, roots, proc_root=Path('/proc')):
    """Inspect every target-uid process; return only references within roots."""
    roots = [Path(root) for root in roots]
    result = {'schema': SCHEMA, 'boot_id': (proc_root / 'sys/kernel/random/boot_id').read_text().strip(),
              'uid': uid, 'roots': [str(root) for root in roots],
              'collected_at': time.time(), 'references': [], 'unknownPids': []}
    for process in proc_root.iterdir():
        if not process.name.isdigit():
            continue
        pid = int(process.name)
        try:
            if process.stat().st_uid != uid:
                continue
        except FileNotFoundError:
            continue
        references, ambiguous = set(), False
        try:
            state, start = _identity(process)
            if state in ('Z', 'X'):
                continue
            try:
                for kind in ('exe', 'cwd'):
                    path = os.readlink(process / kind)
                    if _under(path, roots):
                        references.add((kind, path))
                for fd in (process / 'fd').iterdir():
                    try:
                        path = os.readlink(fd)
                    except FileNotFoundError:
                        # A descriptor can close while the process remains live.
                        continue
                    if _under(path, roots):
                        references.add(('fd', path))
                for line in (process / 'maps').read_text().splitlines():
                    fields = line.split(None, 5)
                    if len(fields) != 6:
                        continue
                    path = re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), fields[5])
                    if _under(path, roots):
                        references.add(('maps', path))
            except (OSError, ValueError):
                ambiguous = True
            # An exited process is harmless; PID reuse or partial visibility is not.
            after_state, after_start = _identity(process)
            if after_state in ('Z', 'X'):
                continue
            if after_start != start or ambiguous:
                result['unknownPids'].append(pid)
                continue
            if references:
                result['references'].extend({'pid': pid, 'starttime': start, 'kind': kind, 'path': path}
                                            for kind, path in sorted(references))
        except (FileNotFoundError, ProcessLookupError):
            # A missing stat after an exe/cwd race proves this process exited.
            continue
        except (OSError, ValueError, IndexError):
            result['unknownPids'].append(pid)
    result['unknownPids'].sort()
    result['references'].sort(key=lambda row: (row['pid'], row['kind'], row['path']))
    return result


def load_config(path=CONFIG):
    # Root ownership of parent directories prevents replacement of a safe file.
    for candidate in (path, *path.parents):
        info = candidate.lstat()
        if info.st_uid != 0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):
            raise ValueError('Process-census configuration must be protected by root')
    config = json.loads(path.read_text())
    uid, roots = config['uid'], config['roots']
    if type(uid) is not int or uid <= 0 or not isinstance(roots, list) or not roots:
        raise ValueError('Invalid fixed process-census scope')
    if any(not isinstance(root, str) or not Path(root).is_absolute()
           or root == '/' or '..' in Path(root).parts for root in roots):
        raise ValueError('Invalid process-census root')
    return uid, roots


def main():
    if len(sys.argv) != 1 or os.geteuid() != 0:
        raise SystemExit('Root process census accepts no arguments')
    uid, roots = load_config()
    print(json.dumps(collect(uid, roots), separators=(',', ':')))


if __name__ == '__main__':
    main()
