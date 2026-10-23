#!/usr/bin/env python3
"""Fail-closed repair drafting admission.

The agreed report-only fallback is active: bounded model access and process
cleanup alone do not prove that a repair worker cannot use other local control
sockets or credentials. This module never launches Codex, merges, publishes,
deploys, or opens a public PR. The controller reports its curated receipt in the
human-review failure issue. A future qualified worker must replace this admission
boundary with independently verified authority isolation, not a boolean switch.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

UNQUALIFIED = ('Repair worker authority isolation is not qualified: no proof that model-generated '
               'commands cannot escape the owned cgroup through local control sockets or access '
               'other effect credentials. Model access and timeout cleanup are separate gates.')


def sanitized_environment(environment=None):
    """Do not pass controller GitHub or unrelated provider credentials to a worker."""
    source = os.environ if environment is None else environment
    return {key: value for key, value in source.items()
            if not any(part in key.upper() for part in ('TOKEN', 'API_KEY', 'SECRET', 'PASSWORD'))
            and key not in ('SSH_AUTH_SOCK', 'DBUS_SESSION_BUS_ADDRESS', 'GIT_ASKPASS',
                            'SSH_ASKPASS', 'GH_CONFIG_DIR', 'GITHUB_CONFIG_DIR')}


def disabled_effect_overrides(config):
    """Enumerate every configured server/plugin; never log their transport/secret values.

    Codex's dotted override parser expects raw server names, rather than quoted
    TOML keys. Dots in a name cannot be safely addressed; fail closed in that case.
    """
    args = ['-c', 'features.apps=false', '-c', 'features.multi_agent=false',
            '-c', 'features.memories=false', '-c', 'sandbox_workspace_write.network_access=false']
    for namespace in ('mcp_servers', 'plugins'):
        for name in sorted(config.get(namespace, {})):
            if '.' in name or '\n' in name or '\r' in name:
                raise ValueError('Cannot safely address configured effect provider name')
            args += ['-c', f'{namespace}.{name}.enabled=false']
    return args


def _atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.lexists(temporary):
            os.unlink(temporary)


def failed_target(run):
    target = run.get('target')
    if not isinstance(target, dict):
        target = {key: run[key] for key in ('version', 'patchQueueSha256', 'upstreamRevision') if key in run}
    # A transient run ID must never make identical failed inputs eligible again.
    target = {key: value for key, value in target.items() if key not in ('runId', 'id', 'createdAt')}
    if not target:
        raise ValueError('A pinned failed target is required for repair admission')
    return target


def draft(run, state_dir, source_repo):
    """Return an idempotent local report without giving a worker effect authority.

    Report-only is not a consumed model attempt. Repeated calls for the same
    pinned target return the same report. No external qualification JSON or
    environment flag can silently enable repair execution.
    """
    target = failed_target(run)
    identity = hashlib.sha256(json.dumps(target, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    directory = Path(state_dir) / 'repair-reports'
    path = directory / (identity + '.json')
    if path.exists():
        existing = json.loads(path.read_text())
        if existing.get('target') != target:
            raise ValueError('Repair report identity collision')
        return existing
    receipt = {'schema': 'chromium-stealthcdp.repair-report.v1', 'target': target,
               'targetIdentity': identity, 'status': 'report_only', 'workerStarted': False,
               'attemptConsumed': False, 'reason': UNQUALIFIED,
               'sourceRepository': str(Path(source_repo).resolve()),
               'createdAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
               'policy': {'maximumAttemptsPerFailedTarget': 1, 'maximumWallSeconds': 1800,
                          'maximumCpuEquivalents': 8, 'maximumMemoryGiB': 32,
                          'installedModelOnly': True, 'humanReviewRequired': True,
                          'workerMergeAuthority': False, 'workerReleaseAuthority': False,
                          'workerDeploymentAuthority': False},
               'nextAction': 'Include this report in the deduplicated failure issue; repair remains human reviewed.'}
    _atomic(path, receipt)
    return receipt
