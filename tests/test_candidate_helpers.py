"""Real shell/linked-worktree regressions for candidate acceptance helpers."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
import time
import unittest

REPO = Path(__file__).resolve().parents[1]


class CandidateHelperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    @unittest.skipUnless(shutil.which('dpkg-deb'), 'Debian packaging tool required')
    def test_codec_debian_identity_and_evidence_survive_packaging(self):
        artifact=self.root/'artifact';runtime=artifact/'chrome-linux';runtime.mkdir(parents=True)
        exe=runtime/'chrome';exe.write_text('#!/bin/sh\necho "Chromium 157.0.8103.78"\n');exe.chmod(0o755)
        manifest={'schema':'chromium-stealthcdp.artifact.v1','platform':'linux',
                  'chromeVersion':'Chromium 157.0.8103.78','buildRecipeSha256':'a'*64,
                  'artifactName':'157.0.8103.78+stealthcdp.cccccccccccc.build.aaaaaaaaaaaa',
                  'patchset':{'repoSha':'b'*40,'patchQueueSha256':'c'*64},
                  'executable':{'relativePath':'chrome-linux/chrome'}}
        (artifact/'manifest.json').write_text(json.dumps(manifest))
        (artifact/'smoke.json').write_text('{}');(artifact/'patches.sha256').write_text('')
        (artifact/'patches').mkdir();(artifact/'codec-qualification.json').write_text('{"accepted":true}')
        for folder in ('codec-notices','codec-evidence'):
            (artifact/folder).mkdir();(artifact/folder/'retained.txt').write_text('retained '+folder)
        output=self.root/'packages'
        result=subprocess.run(['bash',str(REPO/'scripts/package-deb.sh'),'--artifact',str(artifact),
                               '--output-dir',str(output)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        package=next(output.glob('*.deb'))
        version=subprocess.check_output(['dpkg-deb','-f',str(package),'Version'],text=True).strip()
        self.assertEqual(version,'157.0.8103.78+chromiumq.cccccccccccc.build.aaaaaaaaaaaa-1')
        self.assertEqual(subprocess.check_output(['dpkg-deb','-f',str(package),'Package'],text=True).strip(),'chromiumq')
        extracted=self.root/'extracted';subprocess.run(['dpkg-deb','-x',str(package),str(extracted)],check=True)
        for folder in ('codec-notices','codec-evidence'):
            self.assertEqual((extracted/'opt/chromiumQ'/folder/'retained.txt').read_text(),'retained '+folder)
        self.assertTrue((extracted/'opt/chromiumQ/codec-qualification.json').exists())

    def test_windows_install_uses_chromiumq_root_and_reads_both_manifest_schemas(self):
        tools = self.root / 'tools'
        tools.mkdir()
        app_data = self.root / 'LocalAppData'
        (tools / 'wslpath').write_text('#!/bin/sh\nprintf "%s" "$2"\n')
        (tools / 'powershell.exe').write_text(
            '#!/bin/sh\ncase "$3" in\n'
            '  *LOCALAPPDATA*) printf "%s" "$FIXTURE_APP_DATA" ;;\n'
            '  *) printf "%s" "$3" > "$FIXTURE_COMMAND" ;;\nesac\n'
        )
        for tool in tools.iterdir():
            tool.chmod(0o755)
        legacy = app_data / 'chromium-stealthcdp/existing'
        legacy.mkdir(parents=True)
        (legacy / 'chrome.exe').write_bytes(b'old browser')
        artifact = self.root / 'windows-artifact'
        (artifact / 'chrome-win64').mkdir(parents=True)
        (artifact / 'chrome-win64/chrome.exe').write_bytes(b'candidate browser')
        (artifact / 'patches').mkdir()
        (artifact / 'patches.sha256').touch()
        junction_command = self.root / 'junction-command'
        env = {**os.environ, 'PATH': f'{tools}:{os.environ["PATH"]}',
               'FIXTURE_APP_DATA': str(app_data), 'FIXTURE_COMMAND': str(junction_command)}
        for index, schema in enumerate(('chromium-stealthcdp.artifact.v1', 'chromiumQ.artifact.v1')):
            with self.subTest(schema=schema):
                name = f'158.0.8127.36+chromiumq.fixture{index}'
                (artifact / 'manifest.json').write_text(json.dumps({
                    'schema': schema, 'platform': 'win', 'artifactName': name,
                    'executable': {'relativePath': 'chrome-win64/chrome.exe'},
                }))
                result = subprocess.run([str(REPO / 'scripts/install-windows-user.sh'),
                                         '--artifact', str(artifact)], env=env, text=True,
                                        capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                install = app_data / 'chromiumQ'
                self.assertEqual((install / name / 'chrome.exe').read_bytes(), b'candidate browser')
                installed = json.loads((install / name / 'manifest.json').read_text())
                installed_executable = install / name / installed['executable']['relativePath']
                self.assertTrue(installed_executable.is_file())
                self.assertIn(str(install / 'current'), junction_command.read_text())
                self.assertIn(str(install / name), junction_command.read_text())
                self.assertEqual((legacy / 'chrome.exe').read_bytes(), b'old browser')

    def test_smoke_reaps_children_and_preserves_unrelated_process(self):
        bindir = self.root / 'bin'
        bindir.mkdir()
        node = shutil.which('node')
        (bindir / 'node').write_text(f'''#!/usr/bin/env python3
import os,sys
if len(sys.argv)==3 and sys.argv[1]=='-' and sys.argv[2].isdigit():
 print('{{"value":false}}')
else: os.execv({node!r},[{node!r},*sys.argv[1:]])
''')
        (bindir / 'node').chmod(0o755)
        writer = self.root / 'writer.py'
        writer.write_text('''import os,signal,sys,time
from pathlib import Path
signal.signal(signal.SIGTERM,signal.SIG_IGN)
p=Path(sys.argv[1])/'Default'
Path(sys.argv[2]).write_text(str(os.getpid()))
while True:
 p.mkdir(parents=True,exist_ok=True)
 (p/'still-writing').write_text('owned temporary profile')
 time.sleep(.001)
''')
        chrome = self.root / 'chrome'
        chrome.write_text(f'''#!/usr/bin/env python3
import signal,subprocess,sys,time
from pathlib import Path
if '--version' in sys.argv:
 print('Chromium 157.0.8103.38');sys.exit(0)
p=Path(next(x.split('=',1)[1] for x in sys.argv if x.startswith('--user-data-dir=')))
p.mkdir(parents=True,exist_ok=True)
Path({str(self.root/'profile-path')!r}).write_text(str(p))
subprocess.Popen([sys.executable,{str(writer)!r},str(p),{str(self.root/'child-pid')!r}])
while not Path({str(self.root/'child-pid')!r}).exists():time.sleep(.01)
(p/'DevToolsActivePort').write_text('12345\\n/devtools/browser/fixture\\n')
signal.signal(signal.SIGTERM,lambda *_:sys.exit(0))
while True:time.sleep(.1)
''')
        chrome.chmod(0o755)
        sentinel = subprocess.Popen(['sleep', '60'])
        self.addCleanup(lambda: sentinel.poll() is None and sentinel.kill())
        self.addCleanup(sentinel.wait)
        env = {**os.environ, 'PATH': str(bindir) + ':' + os.environ['PATH']}
        child_pid = None
        try:
            result = subprocess.run(['bash', str(REPO/'scripts/smoke.sh'), '--chrome', str(chrome),
                                     '--output', str(self.root/'smoke.json')], env=env,
                                    text=True, capture_output=True, timeout=15)
            child_pid = int((self.root/'child-pid').read_text())
            proc = Path('/proc') / str(child_pid) / 'stat'
            alive = proc.exists() and proc.read_text().split(') ', 1)[1].split()[0] != 'Z'
            self.assertFalse(alive, 'smoke cleanup left its profile writer alive')
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(Path((self.root/'profile-path').read_text()).parent.exists())
            self.assertIsNone(sentinel.poll(), 'cleanup killed unrelated process')
        finally:
            pidfile = self.root/'child-pid'
            if pidfile.exists():
                try: os.kill(int(pidfile.read_text()), signal.SIGKILL)
                except ProcessLookupError: pass
            sentinel.terminate()
            sentinel.wait()

    def test_freshness_accepts_linked_worktree_and_rejects_nested_path(self):
        src = self.root/'source'
        src.mkdir()
        def git(*args):
            return subprocess.check_output(['git','-C',str(src),'-c','user.name=Fixture',
                '-c','user.email=fixture@localhost','-c','commit.gpgsign=false',*args],text=True).strip()
        git('init','-q')
        (src/'tracked').write_text('source')
        git('add','.')
        git('commit','-q','-m','fixture')
        linked=self.root/'linked'
        git('worktree','add','--detach',str(linked),'HEAD')
        artifact=self.root/'artifact'
        artifact.mkdir()
        (artifact/'chrome').write_text('browser fixture')
        (artifact/'smoke.json').write_text(json.dumps({'success':True,'checks':{'navigatorWebdriver':'false'}}))
        sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
        (artifact/'patches.sha256').write_text(''.join(f'{sha(p)}  {p.name}\n' for p in sorted((REPO/'patches').glob('*.patch'))))
        manifest={'schema':'chromium-stealthcdp.artifact.v1','chromium':{'sourceSha':git('rev-parse','HEAD')},
                  'patchset':{'repoSha':'fixture'},'executable':{'relativePath':'chrome','sha256':sha(artifact/'chrome')},
                  'smoke':{'relativePath':'smoke.json','sha256':sha(artifact/'smoke.json')},
                  'patches':{'sha256List':'patches.sha256'}}
        (artifact/'manifest.json').write_text(json.dumps(manifest))
        result=subprocess.run(['bash',str(REPO/'scripts/check-freshness.sh'),'--src',str(linked),
                               '--artifact',str(artifact)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr+result.stdout)
        (linked/'nested').mkdir()
        nested=subprocess.run(['bash',str(REPO/'scripts/check-freshness.sh'),'--src',str(linked/'nested'),
                               '--artifact',str(artifact)],capture_output=True,text=True)
        self.assertEqual(nested.returncode,2)


if __name__ == '__main__':
    unittest.main()
