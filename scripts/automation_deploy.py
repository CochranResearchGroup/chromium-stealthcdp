#!/usr/bin/env python3
"""User-only release activation, disposable acceptance, and conservative retention.

The caller serializes deployments. No retained profile or peer process is modified.
"""
from __future__ import annotations
import base64
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import uuid

EXECUTABLE_ID = 'stealthcdp-chromium-wsl-promoted'
OWNER_MARKER = '.automation-owned.json'


class DeploymentError(RuntimeError):
    def __init__(self, message, receipt=None):
        super().__init__(message)
        self.receipt = receipt or {}


def atomic_json(path: Path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.lexists(name):
            os.unlink(name)


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind_config(config, root, manifest):
    """Preserve unrelated user rows and point both managed bindings at one root."""
    config = copy.deepcopy(config)
    service = config.setdefault('service', {})
    service.setdefault('browserBuildManifests', {}).setdefault('stealthcdp_chromium', {})['manifestPath'] = str(root / 'manifest.json')
    registry = service.setdefault('browserCapabilityRegistry', {})
    rows = registry.setdefault('browserExecutables', [])
    matches = [row for row in rows if row.get('id') == EXECUTABLE_ID]
    if len(matches) != 1:
        raise DeploymentError('Require exactly one existing native StealthCDP executable registry row')
    matches[0].update(executablePath=str(root / manifest['executable']['relativePath']),
                      manifestPath=str(root / 'manifest.json'),
                      version=manifest['chromeVersion'],
                      patchsetId=manifest['patchset']['patchQueueSha256'], source='manifest', fresh=True,
                      lastCheckedAt=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    return config


def _command(argv, timeout=90, runtime_env=None):
    env = dict(os.environ)
    for key in ('AGENT_BROWSER_RUNTIME_PROFILE', 'AGENT_BROWSER_PROFILE', 'AGENT_BROWSER_CDP',
                'AGENT_BROWSER_AUTO_CONNECT', 'AGENT_BROWSER_EXECUTABLE_PATH', 'AGENT_BROWSER_CONFIG'):
        env.pop(key, None)
    if runtime_env:
        env.update(runtime_env)
    result = subprocess.run(argv, text=True, capture_output=True, timeout=timeout, env=env)
    if result.returncode:
        try:
            detail = str(json.loads(result.stdout).get('error', ''))
        except ValueError:
            detail = result.stderr[-2000:]
        raise DeploymentError('Agent Browser command failed: ' + ' '.join(argv[-2:]) + ': ' + detail)

    try:
        value = json.loads(result.stdout)
    except ValueError as exc:
        raise DeploymentError('Agent Browser returned non-JSON output') from exc
    if value.get('success') is not True:
        raise DeploymentError('Agent Browser reported failure: ' + str(value.get('error')))
    return value.get('data')


def _owned_tree(pid):
    records = {}
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            fields = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            records[int(process.name)] = (int(fields[1]), fields[19])
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
    owned = {pid}
    while True:
        children = {child for child, (parent, _) in records.items() if parent in owned}
        expanded = owned | children
        if expanded == owned:
            break
        owned = expanded
    return {child: records[child][1] for child in owned if child in records}


def _tree_alive(owned):
    alive = []
    for pid, start in owned.items():
        try:
            fields = Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()
            if fields[19] == start and Path('/proc', str(pid), 'exe').exists():
                alive.append(pid)
        except (FileNotFoundError, ProcessLookupError):
            pass
    return alive


def _stop_private_runtime(runtime_env):
    """Stop only a fresh daemon proving custody of this private socket directory."""
    socket_dir = Path(runtime_env['AGENT_BROWSER_SOCKET_DIR'])
    owned = {}
    for file in socket_dir.glob('*.pid'):
        try:
            pid = int(file.read_text().strip())
            process = Path('/proc') / str(pid)
            environment = (process / 'environ').read_bytes().split(b'\0')
            expected = ('AGENT_BROWSER_SOCKET_DIR=' + str(socket_dir)).encode()
            if process.stat().st_uid != os.getuid() or expected not in environment:
                raise DeploymentError('Private runtime identity could not be proved; no process signalled')
            tree = _owned_tree(pid)
            owned.update(tree)
            if pid in tree and pid in _tree_alive({pid: tree[pid]}):
                os.kill(pid, signal.SIGTERM)
        except (FileNotFoundError, ProcessLookupError):
            continue
    for _ in range(50):
        if not _tree_alive(owned):
            return {'ownedProcessIds': sorted(owned), 'ownedProcessesRemaining': []}
        time.sleep(.1)
    raise DeploymentError('Private qualification runtime did not exit; custody retained')


def qualify_agent_browser(executable: Path, manifest: dict, *, agent_browser='agent-browser',
                          config_path: Path | None = None, installed=False):
    """Prove selected binary and webdriver through active CDP, then close only our session."""
    executable = Path(executable).resolve(strict=True)
    expected = manifest['executable']['sha256']
    if sha256(executable) != expected:
        raise DeploymentError('Executable hash differs from candidate manifest')
    version = subprocess.run([str(executable), '--version'], text=True, capture_output=True, timeout=20, check=True).stdout.strip()
    if version != manifest['chromeVersion']:
        raise DeploymentError('Executable version differs from manifest')
    session = 'stealthcdp-update-' + uuid.uuid4().hex
    config_path = Path(config_path or Path.home() / '.agent-browser/config.json')
    source_config = json.loads(config_path.read_text())
    config = {'service': {key: copy.deepcopy(value) for key, value in source_config.get('service', {}).items()
                          if key in ('browserBuildManifests', 'browserCapabilityRegistry')}}
    with tempfile.TemporaryDirectory(prefix='stealthcdp-ab-') as work:
        test_config = Path(work) / 'config.json'
        if not installed:
            # Candidate acceptance must not alter the installed or shared selection.
            config = bind_config(config, executable.parents[len(Path(manifest['executable']['relativePath']).parts)-1], manifest)
        atomic_json(test_config, config)
        base = [str(agent_browser), '--config', str(test_config), '--session', session, '--json']
        runtime_env = None
        if not installed:
            private_home = Path(work) / 'home'
            private_home.mkdir()
            (Path(work) / 'empty.env').touch()
            runtime_env = {'HOME': str(private_home), 'AGENT_BROWSER_HOME': str(private_home / '.agent-browser'),
                           'AGENT_BROWSER_SOCKET_DIR': str(Path(work) / 'runtime'),
                           'AGENT_BROWSER_RUNTIME_HOST': '1', 'AGENT_BROWSER_IDLE_TIMEOUT_MS': '60000',
                           'AGENT_BROWSER_ENV_FILE': str(Path(work) / 'empty.env')}
        def command(args):
            return _command(args, runtime_env=runtime_env) if runtime_env else _command(args)
        pid = None
        owned = {}
        receipt = {'session': session, 'expectedSha256': expected, 'version': version}
        error = None
        try:
            launch = base + ['--browser-build', 'stealthcdp_chromium', '--browser-host', 'local_headless', '--headed', 'false']
            if not installed:
                launch += ['--executable-path', str(executable)]
            command(launch + ['open', 'about:blank'])
            pid = int(command(base + ['get', 'browser-pid'])['pid'])
            proc_exe = Path('/proc') / str(pid) / 'exe'
            owned = _owned_tree(pid)
            actual = os.readlink(proc_exe)
            actual_hash = sha256(proc_exe)
            receipt.update(pid=pid, executable=actual, executableSha256=actual_hash)
            if actual_hash != expected:
                raise DeploymentError('Fresh selected browser binary does not match qualified artifact')
            observation = command(base + ['eval', 'JSON.stringify({webdriver:navigator.webdriver,userAgent:navigator.userAgent})'])
            # CLI eval wraps its JavaScript return value as data.result.
            if isinstance(observation, dict) and 'result' in observation:
                observation = observation['result']
            if isinstance(observation, str):
                observation = json.loads(observation)
            if not isinstance(observation, dict) or observation.get('webdriver') is not False:
                raise DeploymentError('Active CDP webdriver observation was not false')
            receipt.update(pid=pid, executable=actual, executableSha256=actual_hash,
                           observation=observation, success=True)
        except Exception as exc:
            error = exc
        finally:
            try:
                if pid:
                    owned.update(_owned_tree(pid))
                if runtime_env:
                    receipt['privateRuntimeCleanup'] = _stop_private_runtime(runtime_env)
                    receipt['close'] = {'disposition': 'private_runtime_closed'}
                else:
                    receipt['close'] = command(base + ['close'])
                # close can return before the OS has reaped the owned browser.
                if pid:
                    for _ in range(50):
                        if not _tree_alive(owned):
                            break
                        time.sleep(.1)
                    else:
                        raise DeploymentError('Owned disposable browser descendants remained after close; no peer process was killed')
            except Exception as exc:
                if error is None:
                    error = exc
                receipt['cleanupError'] = str(exc)
        receipt['ownedProcessIds'] = sorted(owned)
        receipt['ownedProcessesRemaining'] = _tree_alive(owned)
        if error:
            raise DeploymentError(str(error), receipt) from error
        return receipt


def _snapshot(path):
    if path.is_symlink():
        return {'kind': 'link', 'target': os.readlink(path)}
    if path.exists():
        if not path.is_file():
            raise DeploymentError('Cannot snapshot non-file activation path: ' + str(path))
        return {'kind': 'file', 'data': base64.b64encode(path.read_bytes()).decode(), 'mode': path.stat().st_mode & 0o777}
    return {'kind': 'absent'}


def _restore(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if value['kind'] == 'absent':
        path.unlink(missing_ok=True)
        return
    temporary = path.with_name('.' + path.name + '.restore-' + uuid.uuid4().hex)
    if value['kind'] == 'link':
        temporary.symlink_to(value['target'])
    else:
        temporary.write_bytes(base64.b64decode(value['data']))
        temporary.chmod(value['mode'])
    os.replace(temporary, path)


def recover_deployment(state_dir: Path):
    """Fail closed after interruption: roll back a prepared, uncommitted transaction."""
    state_dir = Path(state_dir)
    journal = state_dir / 'deployment-transaction.json'
    if not journal.exists():
        return None
    value = json.loads(journal.read_text())
    if value['status'] != 'prepared':
        return value
    for path, snapshot in value['before'].items():
        _restore(Path(path), snapshot)
    value.update(status='rolled_back', reason='interrupted deployment recovered')
    atomic_json(journal, value)
    atomic_json(state_dir / 'deployment-halted.json', value)
    return value


def deploy(candidate: Path, state_dir: Path, repo_root: Path, *, home: Path | None = None,
           agent_browser='agent-browser'):
    home = Path(home or Path.home())
    state_dir = Path(state_dir)
    recover_deployment(state_dir)
    if (state_dir / 'deployment-halted.json').exists():
        raise DeploymentError('Deployment halted; inspect rollback receipt and explicitly clear halt after repair')
    candidate = Path(candidate).resolve(strict=True)
    manifest = json.loads((candidate / 'manifest.json').read_text())
    # Reserve space for the immutable copy as well as the workstation floor.
    required_copy = sum(p.stat().st_size for p in candidate.rglob('*') if p.is_file() and not p.is_symlink())
    disk_parent = home
    if shutil.disk_usage(disk_parent).free < 200 * 1024**3 + required_copy:
        raise DeploymentError('Installation would consume the 200 GiB free-disk reserve')
    data = home / '.local/share'
    root = data / 'chromium-stealthcdp'
    config_path = home / '.agent-browser/config.json'
    config = bind_config(json.loads(config_path.read_text()), root / 'current', manifest)
    paths = [root / 'current', home / '.local/bin/chromium-stealthcdp',
             data / 'applications/chromium-stealthcdp.desktop', data / 'applications/mimeinfo.cache', config_path]
    journal = {'status': 'prepared', 'artifactName': manifest['artifactName'],
               'before': {str(path): _snapshot(path) for path in paths}, 'startedAt': time.time()}
    journal_path = state_dir / 'deployment-transaction.json'
    atomic_json(journal_path, journal)
    try:
        env = dict(os.environ, HOME=str(home), XDG_DATA_HOME=str(data))
        result = subprocess.run([str(Path(repo_root) / 'scripts/install-linux-user.sh'), '--artifact', str(candidate)],
                                env=env, capture_output=True, text=True, timeout=1800)
        if result.returncode:
            raise DeploymentError('User installer failed: ' + result.stderr[-3000:])
        atomic_json(config_path, config)
        acceptance = qualify_agent_browser(root / 'current' / manifest['executable']['relativePath'], manifest,
                                            config_path=config_path, agent_browser=agent_browser, installed=True)
        version = root / manifest['artifactName']
        atomic_json(version / OWNER_MARKER, {'schema': 'stealthcdp.automation-owned.v1', 'acceptedAt': time.time()})
        journal.update(status='committed', acceptance=acceptance, completedAt=time.time(),
                       oldBrowsers=inspect_live_versions(root)['processes'])
        atomic_json(journal_path, journal)
        return journal
    except BaseException as exc:
        # Also cover graceful service termination/KeyboardInterrupt. SIGKILL recovery uses journal.
        for path, snapshot in journal['before'].items():
            _restore(Path(path), snapshot)
        journal.update(status='rolled_back', error=str(exc), completedAt=time.time())
        if isinstance(exc, DeploymentError):
            journal['acceptanceFailure'] = exc.receipt
        atomic_json(journal_path, journal)
        atomic_json(state_dir / 'deployment-halted.json', journal)
        raise DeploymentError('Activation failed and previous selection restored: ' + str(exc), journal) from exc


def inspect_live_versions(root: Path, *, proc_root=Path('/proc')):
    """Read OS executable identity; unreadable processes make destructive retention unsafe."""
    root = Path(root).resolve()
    processes, unknown = [], []
    active = (root / 'current').resolve().name if (root / 'current').exists() else None
    for process in Path(proc_root).iterdir():
        if not process.name.isdigit():
            continue
        try:
            target = os.readlink(process / 'exe').removesuffix(' (deleted)')
        except FileNotFoundError:
            continue
        except PermissionError:
            # Other users cannot use our private owned versions. Same-uid denial is ambiguous.
            try:
                if process.stat().st_uid == os.getuid():
                    unknown.append(int(process.name))
            except FileNotFoundError:
                pass
            continue
        executable = Path(target)
        if executable.is_relative_to(root):
            processes.append({'pid': int(process.name), 'executable': target,
                              'version': executable.relative_to(root).parts[0],
                              'olderThanActive': executable.relative_to(root).parts[0] != active})
    return {'processes': processes, 'unknownPids': unknown}


def retain_versions(root: Path, keep=3, *, dry_run=False, proc_root=Path('/proc')):
    root = Path(root).resolve()
    live = inspect_live_versions(root, proc_root=proc_root)
    if live['unknownPids']:
        return {'removed': [], 'deferred': 'same-user process identity unavailable', **live}
    protected = {row['version'] for row in live['processes']}
    if (root / 'current').exists():
        protected.add((root / 'current').resolve().name)
    versions = []
    for path in root.iterdir():
        if path.is_symlink() or not path.is_dir():
            continue
        marker = path / OWNER_MARKER
        if marker.is_file():
            value = json.loads(marker.read_text())
            if value.get('schema') == 'stealthcdp.automation-owned.v1':
                versions.append((value['acceptedAt'], path))
    versions.sort(reverse=True)
    protected.update(path.name for _, path in versions[:keep])
    removed = []
    for _, path in versions:
        if path.name not in protected:
            # Recheck immediately before removal; the controller serializes activations.
            fresh = inspect_live_versions(root, proc_root=proc_root)
            if fresh['unknownPids'] or any(row['version'] == path.name for row in fresh['processes']):
                continue
            removed.append(str(path))
            if not dry_run:
                shutil.rmtree(path)
    return {'removed': removed, 'dryRun': dry_run, 'protected': sorted(protected), **live}
