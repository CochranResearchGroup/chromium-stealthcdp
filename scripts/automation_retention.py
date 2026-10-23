"""Conservative cleanup of controller-owned candidate output and old logs."""
import json
import os
from pathlib import Path
import shutil
import time
from automation_deploy import inspect_live_versions, retain_versions


def maintain(state_dir: Path, installed_root: Path, now=None):
    state_dir, installed_root = Path(state_dir), Path(installed_root)
    now = time.time() if now is None else now
    result = {'installed': retain_versions(installed_root), 'removed': [], 'logsRemoved': 0}
    builds = state_dir / 'builds'
    marker = builds / '.chromium-stealthcdp-automation-owned'
    if not marker.is_file() or marker.is_symlink() or marker.read_text() != 'chromium-stealthcdp automation v1\n':
        return result
    live = inspect_live_versions(builds)
    if live['unknownPids']:
        result['deferred'] = 'same-user process identity unavailable'
        return result
    records = []
    for receipt in (state_dir / 'runs').glob('*/run.json'):
        record = json.loads(receipt.read_text())
        records.append((record.get('created_at', 0), record))
    records.sort(key=lambda row: row[0], reverse=True)
    good = [r for _, r in records if r.get('state') == 'complete']
    failures = [r for _, r in records if r.get('state') in ('failed', 'rolled_back')]
    protect = {r['id'] for r in good[:3] + failures[:1]}
    protect.update(r['id'] for _, r in records if r.get('state') not in ('complete', 'failed', 'rolled_back', 'deferred'))
    for _, record in records:
        ctx = record.get('context') or {}
        candidate = builds / 'runs' / record['id']
        if record['id'] not in protect:
            paths = [candidate / 'artifacts', candidate / 'packages', builds / 'checkout/src/out' / f'Automation-{record["id"]}']
            for path in paths:
                if path.is_symlink() or not path.exists():
                    continue
                resolved = path.resolve()
                if not resolved.is_relative_to(builds.resolve()):
                    continue
                fresh = inspect_live_versions(builds)
                if fresh['unknownPids'] or any(Path(p['executable']).is_relative_to(resolved) for p in fresh['processes']):
                    continue
                shutil.rmtree(path)
                result['removed'].append(str(path))
        if failures and record['id'] == failures[0]['id']:
            continue
        evidence = candidate / 'evidence'
        if evidence.is_symlink():
            continue
        for log in evidence.glob('*.log'):
            if log.is_file() and not log.is_symlink() and now - log.stat().st_mtime > 90 * 86400:
                log.unlink()
                result['logsRemoved'] += 1
    return result
