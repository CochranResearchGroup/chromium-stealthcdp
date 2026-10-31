"""Retire verified deployed/superseded intermediates; preserve installed recovery."""
import json
import os
from pathlib import Path
import re
import shutil
import time
from automation_deploy import inspect_live_versions, retain_versions

OWNER = 'chromium-stealthcdp automation v1\n'
RUN_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,179}\Z')
TERMINAL = {'complete', 'failed', 'rolled_back', 'deferred', 'superseded'}


def _safe_path(path, builds):
    """Only ordinary descendants on the owned filesystem, without mounted children."""
    if path == builds or not path.is_relative_to(builds):
        return False
    for parent in (path, *path.parents):
        if parent.is_symlink():
            return False
        if parent == builds:
            break
    if not path.is_dir() or path.stat().st_dev != builds.stat().st_dev:
        return False
    # Mountinfo contains escaped path fields. Include same-device bind mounts.
    for line in Path('/proc/self/mountinfo').read_text().splitlines():
        field = line.split()[4]
        mount = Path(re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), field))
        if (mount == path or mount.is_relative_to(path)
                or (mount.is_relative_to(builds) and path.is_relative_to(mount))):
            return False
    return True


def _in_use(path, builds):
    live = inspect_live_versions(builds)
    if live['unknownPids']:
        return True
    if any(Path(p['executable']).is_relative_to(path) for p in live['processes']):
        return True
    # A compiler can execute outside builds while its cwd/output FD is inside it.
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            if process.stat().st_uid != os.getuid():
                continue
            references = []
            try:
                references.append(os.readlink(process / 'cwd'))
                for fd in (process / 'fd').iterdir():
                    try:
                        references.append(os.readlink(fd))
                    except FileNotFoundError:
                        pass
                for line in (process / 'maps').read_text().splitlines():
                    fields = line.split(None, 5)
                    if len(fields) == 6:
                        references.append(fields[5])
            except PermissionError:
                return True
            if any(Path(p.removesuffix(' (deleted)')).is_relative_to(path) for p in references):
                return True
        except (FileNotFoundError, ProcessLookupError):
            continue
    return False


def _committed(record):
    deployment = record.get('deployment') or {}
    return (record.get('state') == 'complete' and deployment.get('status') == 'committed'
            and deployment.get('acceptance', {}).get('success') is True)


def maintain(state_dir: Path, installed_root: Path, now=None):
    """Called under controller.lock. No source, profiles, or unowned output are retired."""
    state_dir, installed_root = Path(state_dir), Path(installed_root)
    now = time.time() if now is None else now
    result = {'installed': retain_versions(installed_root), 'removed': [], 'skipped': [], 'logsRemoved': 0}
    builds = state_dir / 'builds'
    marker = builds / '.chromium-stealthcdp-automation-owned'
    if (builds.is_symlink() or not marker.is_file() or marker.is_symlink()
            or marker.read_text() != OWNER):
        return result
    live = inspect_live_versions(builds)
    if live['unknownPids']:
        result['deferred'] = 'same-user process identity unavailable'
        return result
    records = []
    for receipt in (state_dir / 'runs').glob('*/run.json'):
        record = json.loads(receipt.read_text())
        identity = record.get('id', '')
        if (receipt.is_symlink() or receipt.parent.is_symlink() or not isinstance(identity, str)
                or not RUN_ID.fullmatch(identity) or identity in ('.', '..') or receipt.parent.name != identity):
            raise ValueError('Unsafe automation run identity')
        records.append((record.get('created_at', 0), record))
    records.sort(key=lambda row: row[0], reverse=True)
    committed = [r for _, r in records if _committed(r)]
    newest = committed[0] if committed else None
    failures = [r for _, r in records if r.get('state') in ('failed', 'rolled_back')]
    latest_failure = failures[0]['id'] if failures else None
    for created, record in records:
        candidate = builds / 'runs' / record['id']
        deployed = _committed(record)
        superseded = (newest is not None and record['id'] != newest['id']
                      and created < newest.get('created_at', 0)
                      and record.get('state') in TERMINAL)
        # Installed releases keep active+rollback binaries independently. Their
        # former compile trees and copied packages are no longer needed to launch.
        if (deployed or superseded) and record['id'] != latest_failure:
            paths = [candidate / 'artifacts', candidate / 'packages',
                     builds / 'checkout/src/out' / f'Automation-{record["id"]}']
            for path in paths:
                if not path.exists() and not path.is_symlink():
                    continue
                if not _safe_path(path, builds):
                    result['skipped'].append({'path': str(path), 'reason': 'unsafe path or mount'})
                    continue
                # Never break an installed selector that still resolves into staging.
                if any((installed_root / alias).exists() and (installed_root / alias).resolve().is_relative_to(path)
                       for alias in ('current', 'previous')) or _in_use(path, builds):
                    result['skipped'].append({'path': str(path), 'reason': 'live or selected reference'})
                    continue
                shutil.rmtree(path)
                result['removed'].append(str(path))
        if record['id'] == latest_failure or record.get('state') not in TERMINAL:
            continue
        evidence = candidate / 'evidence'
        if evidence.is_symlink() or not _safe_path(evidence, builds):
            continue
        for log in evidence.glob('*.log'):
            if log.is_file() and not log.is_symlink() and now - log.stat().st_mtime > 90 * 86400:
                log.unlink()
                result['logsRemoved'] += 1
    return result
