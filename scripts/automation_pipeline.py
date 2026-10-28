#!/usr/bin/env python3
"""Fail-closed Linux candidate preparation. No publication or installed activation.

The caller serializes runs and supplies the outer cgroup resource/time limits.
All mutable source, output and evidence live below an explicitly owned root.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
from dataclasses import dataclass
import time
import xml.etree.ElementTree as ET

UPSTREAM = 'https://chromium.googlesource.com/chromium/src.git'
GN_ARGS = '''is_official_build=true
is_debug=false
is_component_build=false
symbol_level=0
blink_symbol_level=0
v8_symbol_level=0
dcheck_always_on=false
is_chrome_for_testing=false
is_chrome_for_testing_branded=false
use_siso=false
'''


class PipelineError(RuntimeError):
    """A candidate cannot advance; preserve its evidence for investigation."""


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def patch_queue_sha256(directory: Path) -> str:
    patches = sorted(directory.glob('*.patch'))
    if not patches:
        raise PipelineError('Approved patch queue is empty')
    return hashlib.sha256(''.join(f'{sha256(p)}  {p.name}\n' for p in patches).encode()).hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    temp.replace(path)


@dataclass(frozen=True)
class PipelineConfig:
    repo: Path
    managed_root: Path
    depot_tools: Path
    agent_browser: str = 'agent-browser'
    jobs: int = 8
    command_timeout: int = 12 * 60 * 60


class CandidatePipeline:
    def __init__(self, config: PipelineConfig, runner=None):
        self.config = config
        self.repo = config.repo.resolve()
        self.root = config.managed_root.resolve()
        forbidden = [self.repo, (self.repo / '../src').resolve()]
        if any(self.root == p or self.root.is_relative_to(p) for p in forbidden):
            raise PipelineError('Managed root must be outside operator repository/source')
        if config.jobs < 1 or config.jobs > 8:
            raise PipelineError('Compilation must use one to eight jobs')
        self.runner = runner
        self.sequence = 0
        self.transient_retries = 0
        self.last_log = None

    def command(self, context, args, *, cwd=None, timeout=None, input_text=None):
        args = [str(a) for a in args]
        self.sequence += 1
        evidence = Path(context['evidence'])
        evidence.mkdir(parents=True, exist_ok=True)
        log = evidence / f'{time.time_ns()}-{self.sequence:03d}-{Path(args[0]).name}.log'
        self.last_log = log
        env = os.environ.copy()
        env['PATH'] = f'{self.config.depot_tools}:{context["src"]}/buildtools/linux64:{env.get("PATH", "")}'
        env['DEPOT_TOOLS_UPDATE'] = '0'
        if self.runner:
            return self.runner(args, cwd=cwd, env=env, timeout=timeout or self.config.command_timeout,
                               input_text=input_text, log=log)
        with log.open('w') as output:
            output.write(json.dumps({'argv': args, 'cwd': str(cwd)}) + '\n')
            output.flush()
            proc = subprocess.Popen(args, cwd=cwd, env=env, stdin=subprocess.PIPE if input_text is not None else subprocess.DEVNULL,
                                    stdout=output, stderr=subprocess.STDOUT, text=True, start_new_session=True)
            try:
                deadline = time.monotonic() + (timeout or self.config.command_timeout)
                first = True
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise subprocess.TimeoutExpired(args, timeout or self.config.command_timeout)
                    if shutil.disk_usage(self.root).free < 200 * 1024**3:
                        raise PipelineError('Free disk dropped below the 200 GiB reserve')
                    try:
                        proc.communicate(input_text if first else None, timeout=min(15, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        first = False
            except BaseException:
                # Only this freshly created process group, never a shared daemon.
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                    proc.wait(timeout=10)
                except (ProcessLookupError, subprocess.TimeoutExpired):
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    proc.wait()
                raise
            if proc.returncode:
                raise PipelineError(f'Command failed ({proc.returncode}); evidence: {log}')
        # Keep full logs on disk; Chromium build output must not be loaded whole.
        with log.open('rb') as captured:
            captured.readline()
            if log.stat().st_size > 1024 * 1024:
                captured.seek(-1024 * 1024, os.SEEK_END)
            return captured.read().decode('utf-8', errors='replace').strip()

    def fetch(self, context, args, **kwargs):
        """One run-wide retry, only for positively identified transport failures."""
        try:
            return self.command(context, args, **kwargs)
        except PipelineError:
            log = self.last_log
            tail = ''
            if log and log.exists():
                with log.open('rb') as stream:
                    stream.seek(max(0, log.stat().st_size - 65536))
                    tail = stream.read().decode('utf-8', errors='replace')
            transient = re.search(r'Could not resolve host|Connection timed out|HTTP (?:error )?50[234]|503 Service Unavailable|Temporary failure in name resolution', tail, re.I)
            if not transient or self.transient_retries >= 1:
                raise
            self.transient_retries += 1
            write_json(Path(context['evidence']) / 'transient-retry.json',
                       {'failed_log': str(log), 'reason': transient.group(0), 'retry': 1})
            return self.command(context, args, **kwargs)

    def save(self, context, stage):
        context['stage'] = stage
        write_json(Path(context['run_root']) / 'candidate.json', context)
        return context

    def prepare(self, target: dict) -> dict:
        version = str(target['version'])
        if not re.fullmatch(r'\d+\.\d+\.\d+\.\d+', version):
            raise PipelineError('Expected exact four-part Stable version')
        run_id = str(target['run_id'])
        if not re.fullmatch(r'[A-Za-z0-9._-]{1,180}', run_id):
            raise PipelineError('Unsafe run identity')
        revision = str(target.get('upstream_revision', ''))
        if revision and not re.fullmatch(r'[a-f0-9]{40}', revision):
            raise PipelineError('Invalid pinned upstream revision')
        queue = patch_queue_sha256(self.repo / 'patches')
        approved = target.get('approved_patch_queue_sha256', target.get('patch_queue_sha256'))
        if queue != approved:
            raise PipelineError('Approved patch queue changed since target selection')
        self.root.mkdir(parents=True, exist_ok=True)
        marker = self.root / '.chromium-stealthcdp-automation-owned'
        if not marker.exists():
            if any(self.root.iterdir()):
                raise PipelineError('Refusing nonempty unowned managed root')
            marker.write_text('chromium-stealthcdp automation v1\n')
        elif marker.is_symlink() or marker.read_text() != 'chromium-stealthcdp automation v1\n':
            raise PipelineError('Invalid managed-root ownership marker')
        run = self.root / 'runs' / run_id
        context = {**target, 'version': version, 'approved_patch_queue_sha256': queue,
                   'run_root': str(run), 'evidence': str(run / 'evidence'),
                   'src': str(self.root / 'checkout' / 'src'), 'out': f'out/Automation-{run_id}',
                   'patchset': str(run / 'patchset')}
        run.mkdir(parents=True, exist_ok=True)
        receipt = run / 'candidate.json'
        if receipt.exists():
            old = json.loads(receipt.read_text())
            if old['version'] != version or old['approved_patch_queue_sha256'] != queue:
                raise PipelineError('Run identity reused for different inputs')
            if old.get('stage') in ('prepared', 'built', 'qualified', 'packaged'):
                self.check_source(old)
                return old
            raise PipelineError('Interrupted source preparation requires explicit repair, not reset')
        self.save(context, 'preparing')
        checkout = self.root / 'checkout'
        src = Path(context['src'])
        checkout.mkdir(exist_ok=True)
        if not src.exists():
            self.command(context, ['git', 'clone', '--no-checkout', '--filter=blob:none', UPSTREAM, src])
        elif self.command(context, ['git', 'status', '--porcelain', '--untracked-files=no'], cwd=src):
            raise PipelineError('Managed source is dirty; refusing reset')
        self.fetch(context, ['git', 'fetch', '--no-tags', 'origin', f'refs/tags/{version}'], cwd=src)
        actual = self.command(context, ['git', 'rev-parse', 'FETCH_HEAD^{commit}'], cwd=src)
        if revision and revision != actual:
            raise PipelineError('Official version tag does not match pinned upstream SHA')
        context['upstream_revision'] = actual
        self.command(context, ['git', 'checkout', '--detach', actual], cwd=src)
        config = "solutions = [{'name':'src','url':" + repr(UPSTREAM) + ",'managed':False,'custom_deps':{},'custom_vars':{'checkout_pgo_profiles':True}}]\ntarget_os = ['linux']\n"
        gclient = checkout / '.gclient'
        if gclient.exists() and gclient.read_text() != config:
            raise PipelineError('Managed gclient configuration drift')
        gclient.write_text(config)
        self.fetch(context, ['gclient', 'sync', '--nohooks', '--revision', f'src@{actual}', '-j', '8'], cwd=checkout)
        self.command(context, ['gclient', 'runhooks'], cwd=checkout)
        self.fetch(context, ['python3', 'tools/update_pgo_profiles.py', '--target=linux', 'update',
                               '--gs-url-base=chromium-optimization-profiles/pgo_profiles'], cwd=src)
        profile = self.command(context, ['python3', 'tools/update_pgo_profiles.py', '--target=linux', 'get_profile_path'], cwd=src)
        # Chromium emits a GN-compatible quoted string, not a bare path.
        profile_path = Path(json.loads(profile) if profile.startswith('"') else profile)
        if not profile_path.is_absolute():
            profile_path = src / profile_path
        if not profile_path.is_file() or not profile_path.stat().st_size:
            raise PipelineError('Browser PGO profile missing')
        v8hook = ['python3', 'v8/tools/builtins-pgo/download_profiles.py']
        self.fetch(context, v8hook + ['download', '--depot-tools', self.config.depot_tools, '--check-v8-revision'], cwd=src)
        self.command(context, v8hook + ['validate', '--depot-tools', self.config.depot_tools, '--check-v8-revision'], cwd=src)
        context['browser_pgo'] = {'path': str(profile_path), 'sha256': sha256(profile_path)}
        context['v8_revision'] = self.command(context, ['git', 'rev-parse', 'HEAD'], cwd=src / 'v8')
        patches = sorted((self.repo / 'patches').glob('*.patch'))
        added_tests = []
        for patch in patches:
            added_tests.extend(re.findall(r'^\+TEST_F\((\w+),\s*(\w+)\)', patch.read_text(), re.M))
        if not added_tests or any(suite != 'LineBreakerTest' for suite, _ in added_tests):
            raise PipelineError('Approved repair queue needs an explicit supported regression qualification')
        context['required_regressions'] = [f'{suite}.{name}' for suite, name in added_tests]
        self.command(context, ['git', '-c', 'user.name=Chromium StealthCDP Automation', '-c',
                               'user.email=automation@users.noreply.github.com', 'am', *patches], cwd=src)
        self.command(context, ['git', 'diff', '--check', actual, 'HEAD'], cwd=src)
        context['source_sha'] = self.command(context, ['git', 'rev-parse', 'HEAD'], cwd=src)
        fields = dict(line.split('=', 1) for line in (src / 'chrome/VERSION').read_text().splitlines())
        if '.'.join(fields[k] for k in ('MAJOR', 'MINOR', 'BUILD', 'PATCH')) != version:
            raise PipelineError('Source VERSION does not match Stable target')
        snapshot = Path(context['patchset'])
        self.command(context, ['git', 'clone', '--no-hardlinks', self.repo, snapshot])
        self.command(context, ['git', 'remote', 'set-url', 'origin',
                               'https://github.com/CochranResearchGroup/chromium-stealthcdp.git'], cwd=snapshot)
        exported = snapshot / 'patches'
        for patch in exported.glob('*.patch'):
            patch.unlink()
        self.command(context, ['git', 'format-patch', '--binary', '--output-directory', exported, f'{actual}..HEAD'], cwd=src)
        if len(list(exported.glob('*.patch'))) != len(patches):
            raise PipelineError('Unexpected patch replay commit count')
        for old, new in zip(patches, sorted(exported.glob('*.patch'))):
            left = self.command(context, ['git', 'patch-id', '--stable'], input_text=old.read_text()).split()[0]
            right = self.command(context, ['git', 'patch-id', '--stable'], input_text=new.read_text()).split()[0]
            if left != right:
                raise PipelineError('Replayed patch differs; requires human-reviewed repair')
        old_base = (self.repo / 'upstream-revision.txt').read_text().strip()
        # Reconstruct the approved old range from its immutable upstream base.
        # Patch-mail From hashes need not exist in any upstream repository.
        if not re.fullmatch(r'[a-f0-9]{40}', old_base):
            raise PipelineError('Approved queue lacks immutable reference base')
        self.fetch(context, ['git', 'fetch', '--no-tags', 'origin', old_base], cwd=src)
        reference = Path(context['run_root']) / 'reference-source'
        self.command(context, ['git', 'worktree', 'add', '--detach', reference, old_base], cwd=src)
        self.command(context, ['git', '-c', 'user.name=Chromium StealthCDP Automation', '-c',
                               'user.email=automation@users.noreply.github.com', 'am', *patches], cwd=reference)
        old_head = self.command(context, ['git', 'rev-parse', 'HEAD'], cwd=reference)
        comparison = self.command(context, ['git', 'range-diff', '--no-color', f'{old_base}..{old_head}',
                                             f'{actual}..HEAD'], cwd=src)
        summaries = [line for line in comparison.splitlines() if re.match(r'^\s*\d+:', line)]
        if len(summaries) != len(patches) or any(' = ' not in line for line in summaries):
            raise PipelineError('Range-diff is not equivalent to approved queue')
        (Path(context['evidence']) / 'range-diff.txt').write_text(comparison + '\n')
        self.command(context, ['git', 'worktree', 'remove', reference], cwd=src)
        context['replay_comparison'] = 'range-diff and ordered stable patch-id equality'
        context['previous_upstream_revision'] = old_base
        (snapshot / 'upstream-revision.txt').write_text(actual + '\n')
        context['exported_patches'] = str(exported)
        context['patch_queue_sha256'] = patch_queue_sha256(exported)
        self.command(context, ['git', '-C', snapshot, 'add', 'patches', 'upstream-revision.txt'])
        self.command(context, ['git', '-C', snapshot, '-c', 'user.name=Chromium StealthCDP Automation',
                               '-c', 'user.email=automation@users.noreply.github.com', 'commit', '-m', f'Qualify Chromium Stable {version}'])
        return self.save(context, 'prepared')

    def check_source(self, context):
        src = Path(context['src'])
        if self.command(context, ['git', 'rev-parse', 'HEAD'], cwd=src) != context['source_sha']:
            raise PipelineError('Managed source identity changed')
        if self.command(context, ['git', 'status', '--porcelain', '--untracked-files=no'], cwd=src):
            raise PipelineError('Managed source has tracked changes')
        if patch_queue_sha256(Path(context['exported_patches'])) != context['patch_queue_sha256']:
            raise PipelineError('Exported patch queue changed')

    def build(self, context):
        if context['stage'] in ('built', 'qualified', 'packaged'):
            return context
        self.check_source(context)
        src = Path(context['src'])
        out = src / context['out']
        out.mkdir(parents=True, exist_ok=True)
        args = out / 'args.gn'
        if args.exists() and args.read_text() != GN_ARGS:
            raise PipelineError('Candidate GN configuration drift')
        args.write_text(GN_ARGS)
        self.command(context, ['gn', 'gen', context['out']], cwd=src)
        self.command(context, ['autoninja', '-C', context['out'], '-j', str(self.config.jobs), 'chrome', 'blink_unittests'], cwd=src)
        context['gn_args_sha256'] = sha256(args)
        return self.save(context, 'built')

    def qualify(self, context):
        if context['stage'] in ('qualified', 'packaged'):
            return context
        if context['stage'] != 'built':
            raise PipelineError('Candidate must build before qualification')
        self.check_source(context)
        src = Path(context['src'])
        out = src / context['out']
        if (out / 'args.gn').read_text() != GN_ARGS:
            raise PipelineError('Build configuration changed')
        version = self.command(context, [out / 'chrome', '--version'], timeout=30)
        if version != f'Chromium {context["version"]}':
            raise PipelineError('Binary has wrong version or testing branding')
        evidence = Path(context['evidence'])
        xml = evidence / 'line-breaker.xml'
        self.command(context, [out / 'blink_unittests', '--gtest_filter=LineBreakerTest.*',
                               '--test-launcher-jobs=1', f'--gtest_output=xml:{xml}', '--no-sandbox'], cwd=src)
        tests = list(ET.parse(xml).getroot().iter('testcase'))
        names = {f'{t.attrib.get("classname")}.{t.attrib.get("name")}' for t in tests}
        required = set(context['required_regressions']) | {'LineBreakerTest.BreakWordWithReusedShapeResult'}
        if not tests or not required.issubset(names):
            raise PipelineError('Retained repair regression was not exercised')
        if any(t.find('failure') is not None or t.find('skipped') is not None or t.attrib.get('status') == 'notrun' for t in tests):
            raise PipelineError('Focused regression suite failed or skipped tests')
        smoke = evidence / 'smoke.json'
        self.command(context, [self.repo / 'scripts/smoke.sh', '--chrome', out / 'chrome', '--output', smoke], timeout=90)
        smoke_data = json.loads(smoke.read_text())
        if smoke_data.get('success') is not True or smoke_data.get('checks', {}).get('navigatorWebdriver') != 'false':
            raise PipelineError('Active-CDP webdriver qualification failed')
        stage = Path(context['run_root']) / 'artifacts'
        artifact = stage / f'{context["version"]}+stealthcdp.{context["patch_queue_sha256"][:12]}'
        if artifact.is_symlink():
            raise PipelineError('Staged candidate must be an owned directory, not a symlink')
        if not artifact.exists():
            self.command(context, [Path(context['patchset']) / 'scripts/promote-artifact.sh', '--src-out', out,
                                   '--artifact-root', stage, '--smoke-json', smoke])
        # An interrupted qualification may have already promoted this immutable
        # candidate. Reconcile its provenance below, never overwrite/rebuild it.
        artifact = artifact.resolve(strict=True)
        context['artifact'] = str(artifact)
        manifest = json.loads((artifact / 'manifest.json').read_text())
        if (manifest['chromium']['upstreamRevision'] != context['upstream_revision'] or
            manifest['chromium']['sourceSha'] != context['source_sha'] or
            manifest['patchset']['patchQueueSha256'] != context['patch_queue_sha256'] or
            manifest['chromium']['dirty'] or manifest['patchset']['dirty'] or
            sha256(out / 'chrome') != manifest['executable']['sha256'] or
            sha256(artifact / manifest['executable']['relativePath']) != manifest['executable']['sha256']):
            raise PipelineError('Staged provenance mismatch')
        self.command(context, [self.repo / 'scripts/smoke.sh', '--chrome', artifact / manifest['executable']['relativePath'],
                               '--output', evidence / 'staged-smoke.json'], timeout=90)
        from automation_deploy import qualify_agent_browser
        acceptance = qualify_agent_browser(artifact / manifest['executable']['relativePath'], manifest,
                                           agent_browser=self.config.agent_browser, installed=False)
        write_json(evidence / 'agent-browser-candidate.json', acceptance)
        context['qualification'] = {'line_breaker_tests': len(tests), 'browser_pgo': context['browser_pgo'],
                                    'gn_args_sha256': context['gn_args_sha256'], 'v8_revision': context['v8_revision']}
        return self.save(context, 'qualified')

    def package(self, context):
        if context['stage'] == 'packaged':
            for filename, digest in context['package_sha256'].items():
                if sha256(Path(filename)) != digest:
                    raise PipelineError('Existing package changed')
            return context
        if context['stage'] != 'qualified':
            raise PipelineError('Only qualified candidates may package')
        artifact = Path(context['artifact'])
        packages = Path(context['run_root']) / 'packages'
        packages.mkdir(exist_ok=True)
        self.command(context, [self.repo / 'scripts/package-deb.sh', '--artifact', artifact, '--output-dir', packages])
        debs = list(packages.glob('*.deb'))
        if len(debs) != 1:
            raise PipelineError('Expected one Debian artifact')
        extracted = packages / 'deb-verification'
        self.command(context, ['dpkg-deb', '--extract', debs[0], extracted])
        manifest = json.loads((artifact / 'manifest.json').read_text())
        if sha256(extracted / 'opt/chromium-stealthcdp/chrome') != manifest['executable']['sha256']:
            raise PipelineError('Debian executable differs from accepted artifact')
        # Remove only this newly extracted disposable verification directory.
        shutil.rmtree(extracted)
        archive = packages / f'chromium-stealthcdp_{artifact.name}_linux-x86_64.tar.zst'
        self.command(context, ['tar', '--zstd', '-cf', archive, '-C', artifact.parent, artifact.name])
        self.command(context, ['tar', '--zstd', '--compare', '--file', archive, '-C', artifact.parent, artifact.name])
        for name in ('manifest.json', 'smoke.json', 'patches.sha256'):
            shutil.copy2(artifact / name, packages / name)
        shutil.copy2(self.repo / 'scripts/install-linux-user.sh', packages / 'install-linux-user.sh')
        assets = [archive, debs[0], *[packages / n for n in ('manifest.json', 'smoke.json', 'patches.sha256', 'install-linux-user.sh')]]
        sums = packages / 'SHA256SUMS'
        sums.write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in assets))
        context['packages'] = [str(p) for p in assets + [sums]]
        context['package_sha256'] = {str(p): sha256(p) for p in assets + [sums]}
        return self.save(context, 'packaged')

    def run(self, target):
        context = self.prepare(target)
        context = self.build(context)
        context = self.qualify(context)
        return self.package(context)
