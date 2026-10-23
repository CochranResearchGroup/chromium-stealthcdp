#!/usr/bin/env python3
"""Workstation-owned, resumable Linux Stable release controller (stdlib only)."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

REPOSITORY = 'CochranResearchGroup/chromium-stealthcdp'
STABLE_URL = 'https://chromiumdash.appspot.com/fetch_releases?channel=Stable&platform=Linux&num=1'
class AwaitingChecks(RuntimeError):
    pass


TERMINAL = {'complete', 'failed', 'rolled_back', 'deferred'}


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    tmp = path.with_name(path.name + '.tmp')
    with tmp.open('w') as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load(path, default=None):
    return json.loads(Path(path).read_text()) if Path(path).exists() else default


def command(args, cwd=None, timeout=300):
    # No shell interpolation; never log credentials or inherited environment.
    result = subprocess.run([str(a) for a in args], cwd=cwd, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{args[0]} {args[1] if len(args)>1 else ""} failed ({result.returncode}): {result.stderr[-2000:]}')
    return result.stdout.strip()


def patch_digest(repo):
    files = sorted((Path(repo) / 'patches').glob('*.patch'))
    if not files:
        raise ValueError('empty patch queue')
    return hashlib.sha256(''.join(f'{digest(p)}  {p.name}\n' for p in files).encode()).hexdigest()


def target_id(target):
    return f'{target["version"]}-{target["approved_patch_queue_sha256"][:16]}'


def discover(fetch=None):
    def request():
        with urllib.request.urlopen(STABLE_URL, timeout=30) as response:
            return json.load(response)
    for attempt in range(2):
        try:
            releases = (fetch or request)()
            break
        except urllib.error.HTTPError as exc:
            if attempt or exc.code not in (408, 429, 500, 502, 503, 504):
                raise
        except (TimeoutError, urllib.error.URLError):
            if attempt:
                raise
    release = releases[0]
    version, revision = release['version'], release['hashes']['chromium']
    if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+', version) or not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('invalid official Stable identity')
    return {'version': version, 'upstream_revision': revision}


def headroom(path, meminfo='/proc/meminfo'):
    memory = dict((k.rstrip(':'), int(v)) for k, v, *_ in
                  (line.split() for line in Path(meminfo).read_text().splitlines()))
    free = shutil.disk_usage(path).free
    # Leave workstation memory outside the enforced service ceiling.
    return {'ready': free >= 200 * 1024**3 and memory['MemAvailable'] >= 32 * 1024**2,
            'free_disk_bytes': free, 'available_memory_bytes': memory['MemAvailable'] * 1024}


class GitHub:
    def __init__(self, repo=REPOSITORY):
        if repo != REPOSITORY:
            raise ValueError('repository outside approved scope')
        self.repo = repo

    def gh(self, *args, cwd=None):
        return command(['gh', *args], cwd=cwd)

    def api(self, route, method='GET', fields=None):
        args = ['api', f'repos/{self.repo}' + (f'/{route}' if route else ''), '--method', method]
        for key, value in (fields or {}).items():
            args += ['-f', f'{key}={value}']
        return json.loads(self.gh(*args))

    def preflight(self):
        info = self.api('')
        if info.get('full_name') != self.repo or not info.get('permissions', {}).get('push'):
            raise RuntimeError('existing gh login lacks target repository push access')
        return {'repository': self.repo, 'push': True}

    def notify(self, identity, stage, receipt_path):
        marker = f'<!-- stealthcdp-failure:{identity} -->'
        issues = json.loads(self.gh('issue', 'list', '--repo', self.repo, '--state', 'all',
                                   '--search', f'"{marker}" in:body', '--json', 'number,body,state', '--limit', '100'))
        matched = [item for item in issues if marker in item['body']]
        body = (f'{marker}\nAutomated Linux Stable update **{identity}** stopped at `{stage}`.\n\n'
                'The installed known-good browser and active sessions are preserved. '
                'Repair drafting is report-only while worker authority isolation is unqualified. '
                'Repairs require human review. Review local receipts before retrying; raw logs remain local.\n')
        bodyfile = Path(receipt_path).parent / 'issue-body.md'
        bodyfile.write_text(body)
        if matched:
            issue = matched[0]['number']
            self.gh('issue', 'edit', str(issue), '--repo', self.repo, '--body-file', str(bodyfile))
            if matched[0]['state'] == 'CLOSED':
                self.gh('issue', 'reopen', str(issue), '--repo', self.repo)
            return {'issue': issue, 'delivered': True}
        url = self.gh('issue', 'create', '--repo', self.repo, '--title', f'StealthCDP update stopped: {identity}',
                      '--body-file', str(bodyfile))
        return {'url': url, 'delivered': True}

    def integrate(self, ctx, run):
        """Reconcile a deterministic source branch/PR; merge through normal protections."""
        repo = Path(ctx['patchset_repo'])
        if command(['git', 'remote', 'get-url', 'origin'], cwd=repo) != f'https://github.com/{self.repo}.git':
            raise RuntimeError('source publication remote is outside approved repository')
        if patch_digest(repo) != ctx['patch_queue_sha256']:
            raise RuntimeError('qualified exported patch queue changed')
        branch = f'automation/stable-{run["id"]}'
        # Only curated qualification evidence belongs in source/public output.
        destination = repo / 'docs/releases' / f'{run["id"]}.json'
        summary = {k: ctx[k] for k in ('version', 'upstream_revision', 'patch_queue_sha256')}
        summary.update(executable_sha256=load(Path(ctx['artifact']) / 'manifest.json')['executable']['sha256'],
                       qualification='passed', retained_regression='LineBreakerTest.*')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(summary, indent=2) + '\n')
        status = command(['git', 'status', '--porcelain'], cwd=repo)
        if status:
            command(['git', 'checkout', '-B', branch], cwd=repo)
            command(['git', 'add', 'upstream-revision.txt', 'patches', 'docs/releases'], cwd=repo)
            command(['git', 'diff', '--cached', '--check'], cwd=repo)
            command(['git', '-c', 'user.name=StealthCDP Automation', '-c', 'user.email=automation@users.noreply.github.com',
                     'commit', '-m', f'Qualify Chromium Stable {ctx["version"]}'], cwd=repo)
        head = command(['git', 'rev-parse', 'HEAD'], cwd=repo)
        remote = command(['git', 'ls-remote', 'origin', f'refs/heads/{branch}'], cwd=repo)
        if remote and remote.split()[0] != head:
            raise RuntimeError('remote routine branch identity differs; no force push')
        if not remote:
            command(['git', 'push', 'origin', f'{head}:refs/heads/{branch}'], cwd=repo)
        prs = json.loads(self.gh('pr', 'list', '--repo', self.repo, '--head', branch, '--state', 'all',
                                '--json', 'number,state,headRefOid,mergeCommit', '--limit', '100'))
        if not prs:
            body = repo.parent / 'routine-pr.md'
            body.write_text(f'Update production Linux Stable to {ctx["version"]}.\n\n'
                            'Clean patch replay, official non-testing build, matching optimization profiles, '
                            'LineBreakerTest suite, CDP smoke, packages and isolated Agent Browser acceptance passed.\n')
            self.gh('pr', 'create', '--repo', self.repo, '--base', 'main', '--head', branch,
                    '--title', f'Chromium Stable {ctx["version"]}', '--body-file', str(body))
            prs = json.loads(self.gh('pr', 'list', '--repo', self.repo, '--head', branch, '--state', 'all',
                                    '--json', 'number,state,headRefOid,mergeCommit'))
        pr = prs[0]
        if pr['headRefOid'] != head:
            raise RuntimeError('routine PR head mismatch')
        if pr['state'] != 'MERGED':
            if pr['state'] != 'OPEN':
                raise RuntimeError('routine PR closed without merging')
            self.api(f'statuses/{head}', 'POST', {'state': 'success', 'context': 'stealthcdp/qualification',
                                               'description': 'Pinned local candidate qualification passed'})
            statuses = self.api(f'commits/{head}/status')
            checks = self.api(f'commits/{head}/check-runs')
            if statuses['state'] != 'success' or any(c['status'] != 'completed' or c['conclusion'] not in
                    ('success', 'neutral', 'skipped') for c in checks['check_runs']):
                raise AwaitingChecks('PR checks pending or failed; preserve candidate for reconciliation')
            self.gh('pr', 'merge', str(pr['number']), '--repo', self.repo, '--merge', '--match-head-commit', head)
        merged = json.loads(self.gh('pr', 'view', str(pr['number']), '--repo', self.repo,
                                   '--json', 'state,mergeCommit,headRefOid'))
        if merged['state'] != 'MERGED' or merged['headRefOid'] != head:
            raise RuntimeError('merge outcome not confirmed')
        sha = merged['mergeCommit']['oid']
        command(['git', 'fetch', 'origin', 'main'], cwd=repo)
        if command(['git', 'rev-parse', f'{sha}:patches'], cwd=repo) != command(['git', 'rev-parse', f'{head}:patches'], cwd=repo):
            raise RuntimeError('merged patch tree mismatch')
        return {'pr': pr['number'], 'source_commit': sha}

    def publish(self, ctx, integrated):
        tag = f'v{ctx["version"]}-stealthcdp.{ctx["patch_queue_sha256"][:12]}'
        repo = Path(ctx['patchset_repo'])
        if command(['git', 'remote', 'get-url', 'origin'], cwd=repo) != f'https://github.com/{self.repo}.git':
            raise RuntimeError('source publication remote is outside approved repository')
        remote = command(['git', 'ls-remote', 'origin', f'refs/tags/{tag}'], cwd=repo)
        if remote and remote.split()[0] != integrated['source_commit']:
            raise RuntimeError('immutable release tag mismatch')
        if not remote:
            command(['git', 'push', 'origin', f'{integrated["source_commit"]}:refs/tags/{tag}'], cwd=repo)
        # Release lookup via listing distinguishes absence from auth/network failure.
        releases = self.api('releases?per_page=100')
        found = next((r for r in releases if r['tag_name'] == tag), None)
        assets = [Path(p) for p in ctx['packages']]
        if any(ctx.get('package_sha256', {}).get(str(p)) != digest(p) for p in assets):
            raise RuntimeError('qualified package identity changed')
        expected = {p.name: digest(p) for p in assets}
        if len(expected) != len(assets):
            raise RuntimeError('duplicate asset names')
        if not found:
            notes = repo.parent / 'release-notes.md'
            notes.write_text(f'Production Linux Stable {ctx["version"]} with the approved StealthCDP patch queue.\n\n'
                             'Official non-testing Chromium build; retained Blink regressions, active CDP '
                             'webdriver=false and isolated Agent Browser acceptance passed.\n')
            self.gh('release', 'create', tag, '--repo', self.repo, '--verify-tag', '--draft',
                    '--title', f'Chromium StealthCDP {ctx["version"]}', '--notes-file', str(notes))
            found = next(r for r in self.api('releases?per_page=100') if r['tag_name'] == tag)
        existing = {a['name']: a for a in found['assets']}
        for asset in assets:
            if asset.name in existing:
                if existing[asset.name].get('digest') != f'sha256:{expected[asset.name]}':
                    raise RuntimeError('published asset differs or lacks server digest; no overwrite')
            else:
                self.gh('release', 'upload', tag, str(asset), '--repo', self.repo)
        readback = next(r for r in self.api('releases?per_page=100') if r['tag_name'] == tag)
        observed = {a['name']: a.get('digest') for a in readback['assets']}
        if any(observed.get(name) != f'sha256:{sha}' for name, sha in expected.items()):
            raise RuntimeError('release asset digest readback failed')
        self.gh('release', 'edit', tag, '--repo', self.repo, '--draft=false', '--latest')
        final = next(r for r in self.api('releases?per_page=100') if r['tag_name'] == tag)
        if final['draft'] or final['prerelease']:
            raise RuntimeError('public release state not confirmed')
        return {'tag': tag, 'url': final['html_url'], 'assets': expected}

    def quarantine(self, tag, reason):
        if not reason.strip():
            raise ValueError('confirmed release defect evidence required')
        release = json.loads(self.gh('release', 'view', tag, '--repo', self.repo, '--json', 'body'))
        notes = f'QUARANTINED: {reason}\n\n' + release['body']
        self.gh('release', 'edit', tag, '--repo', self.repo, '--prerelease', '--latest=false', '--notes', notes)


class Controller:
    def __init__(self, config, github=None, discover_fn=discover, pipeline_factory=None, deploy_fn=None):
        self.config = config
        self.root = Path(config['state_dir'])
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.github = github or GitHub()
        self.discover = discover_fn
        self.pipeline_factory = pipeline_factory
        self.deploy_fn = deploy_fn

    def save(self, run):
        atomic_json(self.root / 'runs' / run['id'] / 'run.json', run)
        atomic_json(self.root / 'active.json', {'id': run['id']})

    def snapshot(self, target):
        dest = self.root / 'runs' / target['run_id'] / 'patchset'
        if not dest.exists():
            command(['git', 'clone', '--no-hardlinks', self.config['source_repo'], dest])
            command(['git', 'remote', 'set-url', 'origin', f'https://github.com/{REPOSITORY}.git'], cwd=dest)
            command(['git', 'fetch', 'origin', 'main'], cwd=dest)
            command(['git', 'checkout', '--detach', 'origin/main'], cwd=dest)
        if patch_digest(dest) != target['approved_patch_queue_sha256']:
            raise RuntimeError('approved patch queue changed after pin')
        return dest

    def report(self, run):
        try:
            run['notification'] = self.github.notify(run['id'], run['stage'], self.root / 'runs' / run['id'] / 'run.json')
        except Exception as exc:
            run['notification'] = {'delivered': False, 'error': str(exc)}
        self.save(run)

    def run(self, requeue=False):
        with (self.root / 'controller.lock').open('a+') as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                atomic_json(self.root / 'pending.json', {'requested_at': time.time()})
                return {'state': 'coalesced'}
            from automation_deploy import recover_deployment
            recover_deployment(self.root / 'deployments')
            if (self.root / 'deployments/deployment-halted.json').exists():
                return {'state': 'stopped', 'reason': 'deployment rollback requires investigation'}
            self.github.preflight()
            from automation_retention import maintain
            installed_root = Path(self.config.get('installed_root', str(Path.home() / '.local/share/chromium-stealthcdp')))
            if installed_root.exists():
                atomic_json(self.root / 'retention.json', maintain(self.root, installed_root))
            # Read approved queue from remote main without mutating the installed code.
            queue_repo = self.root / 'approved-source'
            if not queue_repo.exists():
                command(['git', 'clone', '--no-hardlinks', self.config['source_repo'], queue_repo])
                command(['git', 'remote', 'set-url', 'origin', f'https://github.com/{REPOSITORY}.git'], cwd=queue_repo)
            command(['git', 'fetch', 'origin', 'main'], cwd=queue_repo)
            if command(['git', 'status', '--porcelain'], cwd=queue_repo):
                raise RuntimeError('managed approved source unexpectedly dirty')
            command(['git', 'checkout', '--detach', 'origin/main'], cwd=queue_repo)
            target = self.discover()
            target['approved_patch_queue_sha256'] = patch_digest(queue_repo)
            target['patch_queue_sha256'] = target['approved_patch_queue_sha256']
            target['run_id'] = target_id(target)
            pending = self.root / 'pending.json'
            pending.unlink(missing_ok=True)  # discovery coalesces all waiting triggers to latest
            active = load(self.root / 'active.json', {})
            run = load(self.root / 'runs' / active.get('id', '_') / 'run.json', {})
            if run and run['state'] not in TERMINAL:
                atomic_json(pending, target)
            else:
                run_path = self.root / 'runs' / target['run_id'] / 'run.json'
                prior = load(run_path, {})
                if prior and prior['state'] in ('failed', 'rolled_back') and not requeue:
                    return {'state': 'stopped', 'id': prior['id'], 'reason': 'explicit requeue or changed input required'}
                baseline = load(self.root / 'baseline.json', {})
                if (baseline.get('version'), baseline.get('patch_queue_sha256')) == (target['version'], target['approved_patch_queue_sha256']):
                    result = {'state': 'unchanged', 'target': target, 'checked_at': time.time()}
                    atomic_json(self.root / 'last-check.json', result)
                    return result
                if (self.root / 'deployment-stopped.json').exists():
                    return {'state': 'stopped', 'reason': 'deployment stop requires investigation and explicit recovery'}
                if prior.get('state') == 'complete':
                    return prior
                if requeue and prior:
                    # Preserve failed attempt evidence; retry only by explicit invocation.
                    history = self.root / 'runs' / target['run_id'] / f'previous-{time.time_ns()}.json'
                    atomic_json(history, prior)
                run = dict(prior, state='active') if requeue and prior.get('context') else {
                    'id': target['run_id'], 'target': target, 'state': 'active', 'stage': 'prepare', 'created_at': time.time()}
                self.save(run)
            try:
                if run['stage'] == 'prepare':
                    budget = headroom(self.root)
                    run['headroom'] = budget
                    if not budget['ready']:
                        run['state'] = 'deferred'
                        self.save(run)
                        return run
                    repo = self.snapshot(run['target'])
                    from automation_pipeline import CandidatePipeline, PipelineConfig
                    factory = self.pipeline_factory or CandidatePipeline
                    pipeline = factory(PipelineConfig(repo=repo, managed_root=self.root / 'builds',
                                                       depot_tools=Path(self.config['depot_tools']),
                                                       agent_browser=self.config.get('agent_browser', 'agent-browser')))
                    run['context'] = pipeline.run(run['target'])
                    run['context']['patchset_repo'] = run['context']['patchset']
                    run['stage'] = 'integrate'
                    self.save(run)
                if run['stage'] == 'integrate':
                    run['integration'] = self.github.integrate(run['context'], run)
                    run['stage'] = 'publish'
                    self.save(run)
                if run['stage'] == 'publish':
                    run['publication'] = self.github.publish(run['context'], run['integration'])
                    run['stage'] = 'deploy'
                    self.save(run)
                if run['stage'] == 'deploy':
                    from automation_deploy import deploy
                    run['deployment'] = (self.deploy_fn or deploy)(Path(run['context']['artifact']),
                        self.root / 'deployments', Path(self.config['source_repo']),
                        agent_browser=self.config.get('agent_browser', 'agent-browser'))
                    run['stage'], run['state'] = 'complete', 'complete'
                    atomic_json(self.root / 'baseline.json', {
                        'version': run['target']['version'], 'patch_queue_sha256': run['context']['patch_queue_sha256'],
                        'publication': run['publication'], 'deployment': run['deployment'], 'run_id': run['id']})
                    self.save(run)
                return run
            except AwaitingChecks as exc:
                run['state'], run['waiting_reason'] = 'awaiting_checks', str(exc)
                self.save(run)
                return run
            except Exception as exc:
                run['state'], run['error'] = 'failed', str(exc)
                # A failed installed transaction stops deployments even if rollback succeeds.
                if run['stage'] == 'deploy':
                    atomic_json(self.root / 'deployment-stopped.json', {'id': run['id'], 'error': str(exc)})
                    run['state'] = 'rolled_back' if getattr(exc, 'receipt', {}).get('status') == 'rolled_back' else 'failed'
                self.save(run)
                self.repair_report(run)
                self.report(run)
                setattr(exc, '_stealthcdp_notification', run['notification'])
                raise

    def repair_report(self, run):
        from automation_repair import draft
        receipt = draft(run, self.root, Path(self.config['source_repo']))
        atomic_json(self.root / 'runs' / run['id'] / 'repair.json', receipt)


def adopt(config, artifact):
    from automation_deploy import qualify_agent_browser
    root = Path(config['state_dir'])
    manifest = load(Path(artifact) / 'manifest.json')
    exe = Path(artifact) / manifest['executable']['relativePath']
    if digest(exe) != manifest['executable']['sha256']:
        raise RuntimeError('baseline executable hash mismatch')
    smoke_path = Path(artifact) / manifest['smoke']['relativePath']
    if digest(smoke_path) != manifest['smoke']['sha256']:
        raise RuntimeError('baseline smoke hash mismatch')
    smoke = load(smoke_path)
    if manifest['chromium']['dirty'] or manifest['patchset']['dirty']:
        raise RuntimeError('dirty baseline provenance')
    if not smoke['success'] or str(smoke['checks']['navigatorWebdriver']).lower() != 'false':
        raise RuntimeError('baseline CDP behavior invalid')
    version = manifest['chromeVersion'].removeprefix('Chromium ').strip()
    actual = command([exe, '--version'])
    if actual != f'Chromium {version}':
        raise RuntimeError('baseline version/branding mismatch')
    GitHub().preflight()
    tag = f'v{version}-stealthcdp.{manifest["patchset"]["patchQueueSha256"][:12]}'
    release = GitHub().api(f'releases/tags/{tag}')
    remote_manifest = next((a for a in release['assets'] if a['name'] == 'manifest.json'), None)
    if release['draft'] or release['prerelease'] or not remote_manifest or remote_manifest.get('digest') != f'sha256:{digest(Path(artifact)/"manifest.json")}':
        raise RuntimeError('published baseline manifest mismatch')
    # Installed check is performed by deployment module qualification API.
    acceptance = qualify_agent_browser(exe, manifest, installed=True,
                                       agent_browser=config.get('agent_browser', 'agent-browser'))
    atomic_json(root / 'baseline-acceptance.json', acceptance)
    result = {'version': version, 'patch_queue_sha256': manifest['patchset']['patchQueueSha256'],
              'artifact': str(Path(artifact).resolve()), 'acceptance': acceptance, 'adopted_at': time.time(),
              'publication': {'tag': tag, 'url': release['html_url']}}
    atomic_json(root / 'baseline.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    sub = parser.add_subparsers(dest='action', required=True)
    run = sub.add_parser('run')
    run.add_argument('--requeue', action='store_true')
    sub.add_parser('status')
    baseline = sub.add_parser('adopt')
    baseline.add_argument('--artifact', required=True, type=Path)
    quarantine = sub.add_parser('quarantine')
    quarantine.add_argument('tag')
    quarantine.add_argument('--confirmed-defect', required=True)
    args = parser.parse_args()
    config = load(args.config)
    try:
        if args.action == 'run':
            controller = Controller(config)
            result = controller.run(args.requeue)
            if (controller.root / 'pending.json').exists() and result.get('state') in TERMINAL:
                result = controller.run()
        elif args.action == 'adopt':
            result = adopt(config, args.artifact)
        elif args.action == 'quarantine':
            GitHub().quarantine(args.tag, args.confirmed_defect)
            result = {'quarantined': args.tag}
        else:
            root = Path(config['state_dir'])
            result = {name: load(root / f'{name}.json') for name in ('baseline', 'active', 'pending', 'last-check', 'deployment-stopped')}
        print(json.dumps(result, indent=2))
    except Exception as exc:
        error_path = Path(config['state_dir']) / 'last-error.json'
        error_receipt = {'error': str(exc), 'at': time.time()}
        atomic_json(error_path, error_receipt)
        if hasattr(exc, '_stealthcdp_notification'):
            error_receipt['notification'] = exc._stealthcdp_notification
        else:
            try:
                error_receipt['notification'] = GitHub().notify('controller-check', 'preflight/discovery', error_path)
            except Exception as notification_error:
                error_receipt['notification'] = {'delivered': False, 'error': str(notification_error)}
        atomic_json(error_path, error_receipt)
        print(f'automation stopped: {exc}', file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
