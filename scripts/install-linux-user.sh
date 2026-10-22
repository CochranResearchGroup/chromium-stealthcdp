#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --artifact) artifact="${2:?artifact path required}"; shift 2 ;;
    -h|--help)
      echo 'Usage: scripts/install-linux-user.sh [--artifact PATH]'
      echo 'Installs a verified artifact, PATH launcher and desktop browser choice for this user.'
      exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

python3 - "$artifact" <<'PY'
import hashlib
import configparser
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid

artifact = Path(sys.argv[1]).resolve(strict=True)
manifest = json.loads((artifact / 'manifest.json').read_text())
assert manifest['schema'] == 'chromium-stealthcdp.artifact.v1', 'unsupported manifest'
assert manifest.get('platform', 'linux') == 'linux', 'Linux artifact required'
name = manifest['artifactName']
assert re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.+_-]*', name), 'invalid artifact name'

def verified_file(root, entry):
    path = (root / entry['relativePath']).resolve(strict=True)
    assert path.is_relative_to(root.resolve()), 'artifact path escapes root'
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert digest == entry['sha256'], f'hash mismatch: {path.name}'
    return path

verified_file(artifact, manifest['executable'])
smoke = json.loads(verified_file(artifact, manifest['smoke']).read_text())
assert smoke['success'] and str(smoke['checks']['navigatorWebdriver']).lower() == 'false'
assert not manifest['chromium']['dirty'] and not manifest['patchset']['dirty']

data = Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share')))
assert data.is_absolute(), 'XDG_DATA_HOME must be absolute'
root = data / 'chromium-stealthcdp'
root.mkdir(mode=0o700, parents=True, exist_ok=True)
version = root / name
launcher = Path.home() / '.local/bin/chromium-stealthcdp'
assert not any(c in str(launcher) for c in '\n\r%"`$\\'), 'unsupported launcher path'
executable = manifest['executable']['relativePath']
launcher_target = root / 'current' / executable
if os.path.lexists(launcher):
    assert launcher.is_symlink() and os.readlink(launcher) == str(launcher_target), \
        f'preserve existing unrelated launcher: {launcher}'

if version.exists():
    assert (version / 'manifest.json').read_bytes() == (artifact / 'manifest.json').read_bytes(), \
        'existing version has different provenance'
    verified_file(version, manifest['executable'])
    verified_file(version, manifest['smoke'])
else:
    temporary = Path(tempfile.mkdtemp(prefix='.install-', dir=root))
    try:
        shutil.copytree(artifact, temporary, dirs_exist_ok=True)
        verified_file(temporary, manifest['executable'])
        os.replace(temporary, version)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

def replace_symlink(path, target):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name('.' + path.name + '.' + uuid.uuid4().hex)
    try:
        temporary.symlink_to(target)
        os.replace(temporary, path)
    finally:
        if temporary.is_symlink():
            temporary.unlink()

replace_symlink(root / 'current', name)
replace_symlink(launcher, str(launcher_target))
desktop = data / 'applications/chromium-stealthcdp.desktop'
desktop.parent.mkdir(parents=True, exist_ok=True)
content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Chromium StealthCDP
Comment=Stable Chromium with private CDP behavior
Exec="{launcher}" %U
TryExec={launcher}
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;application/pdf;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
StartupWMClass=chromium
'''
with tempfile.NamedTemporaryFile(mode='w', dir=desktop.parent, delete=False) as stream:
    stream.write(content)
    temporary = Path(stream.name)
temporary.chmod(0o644)
os.replace(temporary, desktop)
if shutil.which('update-desktop-database') is None:
    # Minimal hosts may lack desktop-file-utils. Register this entry in the
    # per-directory MIME cache without changing any default associations.
    cache_path = desktop.parent / 'mimeinfo.cache'
    cache = configparser.ConfigParser(interpolation=None, strict=False)
    cache.optionxform = str
    cache.read(cache_path)
    if not cache.has_section('MIME Cache'):
        cache.add_section('MIME Cache')
    for mime in ('text/html', 'application/xhtml+xml', 'application/pdf',
                 'x-scheme-handler/http', 'x-scheme-handler/https'):
        entries = cache.get('MIME Cache', mime, fallback='').split(';')
        entries = [entry for entry in entries if entry]
        if desktop.name not in entries:
            entries.append(desktop.name)
        cache.set('MIME Cache', mime, ';'.join(entries) + ';')
    with tempfile.NamedTemporaryFile(mode='w', dir=desktop.parent, delete=False) as stream:
        cache.write(stream, space_around_delimiters=False)
        temporary = Path(stream.name)
    temporary.chmod(0o644)
    os.replace(temporary, cache_path)
print(json.dumps({'version': manifest['chromeVersion'], 'executable': str(launcher),
                  'manifest': str(root / 'current/manifest.json'),
                  'desktopEntry': str(desktop)}, indent=2))
PY

if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database "${XDG_DATA_HOME:-$HOME/.local/share}/applications"
fi
