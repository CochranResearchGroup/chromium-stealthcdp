"""Optional root-owned, read-only process-reference probe. Failure stays ambiguous."""
import json
import math
import os
from pathlib import Path
import stat
import subprocess
import time

PROBE = Path('/usr/local/libexec/chromium-stealthcdp-process-probe')
CONFIG = Path('/etc/chromium-stealthcdp/process-census.json')


def _trusted(path):
    for parent in (path, *path.parents):
        info = parent.lstat()
        if stat.S_ISLNK(info.st_mode) or info.st_uid != 0 or info.st_mode & 0o022:
            return False
    return True


def privileged_references(root):
    """Accept a fresh same-host census only for an explicitly provisioned root."""
    try:
        if not _trusted(PROBE) or not _trusted(CONFIG):
            return None
        result = subprocess.run(['/usr/bin/sudo', '-n', '--', str(PROBE)],
                                capture_output=True, text=True, timeout=30)
        if result.returncode:
            return None
        snapshot = json.loads(result.stdout)
        if not isinstance(snapshot, dict):
            return None
        roots = snapshot['roots']
        unknown = snapshot['unknownPids']
        rows = snapshot['references']
        collected = snapshot['collected_at']
        if (type(snapshot['uid']) is not int or not isinstance(roots, list) or not roots
                or any(not isinstance(p, str) or not Path(p).is_absolute()
                       or '..' in Path(p).parts for p in roots)
                or not isinstance(unknown, list)
                or any(type(pid) is not int or pid <= 0 for pid in unknown)
                or not isinstance(rows, list) or type(collected) not in (int, float)
                or not math.isfinite(collected)):
            return None
        root = str(Path(root).resolve())
        age = time.time() - collected
        if (snapshot['schema'] != 'stealthcdp.process-census.v1'
                or snapshot['uid'] != os.getuid() or root not in snapshot['roots']
                or snapshot['boot_id'] != Path('/proc/sys/kernel/random/boot_id').read_text().strip()
                or not -2 <= age <= 30 or snapshot['unknownPids']):
            return None
        references = []
        for row in rows:
            if (not isinstance(row, dict) or type(row.get('pid')) is not int or row['pid'] <= 0
                    or type(row.get('starttime')) is not int or row['starttime'] <= 0
                    or row.get('kind') not in ('exe', 'cwd', 'fd', 'maps')
                    or not isinstance(row.get('path'), str)):
                return None
            path = Path(row['path'].removesuffix(' (deleted)'))
            if (not path.is_absolute() or '..' in path.parts
                    or not any(path.is_relative_to(p) for p in roots)):
                return None
            if path.is_relative_to(root):
                references.append(dict(row, path=str(path)))
        return {'references': references, 'referenceScanComplete': True,
                'processes': [{'pid': row['pid'], 'executable': row['path'],
                               'version': Path(row['path']).relative_to(root).parts[0],
                               'olderThanActive': False} for row in references
                              if Path(row['path']) != Path(root)],
                'unknownPids': [], 'censusSource': 'root-owned-read-only-probe'}
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired):
        return None
