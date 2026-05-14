#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/install-windows-user.sh [--artifact PATH] [--install-root PATH] [--force]

Installs a promoted Windows chromium-stealthcdp artifact into the WSL tenant
owner's Windows LocalAppData tree. The default install root is:

  %LOCALAPPDATA%\chromium-stealthcdp

The script creates or updates a Windows directory junction named `current`.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
install_root=""
force=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --artifact)
      artifact="${2:-}"
      shift 2
      ;;
    --install-root)
      install_root="${2:-}"
      shift 2
      ;;
    --force)
      force=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

powershell_cmd=""
for candidate in \
  powershell.exe \
  pwsh.exe \
  powershell \
  pwsh \
  "/mnt/c/Program Files/PowerShell/7/pwsh.exe" \
  /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe; do
  if command -v "$candidate" >/dev/null 2>&1; then
    powershell_cmd="$candidate"
    break
  elif [[ -x "$candidate" ]]; then
    powershell_cmd="$candidate"
    break
  fi
done
if [[ -z "$powershell_cmd" ]]; then
  echo "required tool not found: powershell.exe or pwsh.exe" >&2
  exit 2
fi

for tool in node wslpath; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "required tool not found: $tool" >&2
    exit 2
  fi
done

if [[ ! -e "$artifact" ]]; then
  echo "artifact does not exist: $artifact" >&2
  exit 2
fi

artifact="$(realpath "$artifact")"
manifest="$artifact/manifest.json"
if [[ ! -f "$manifest" ]]; then
  echo "manifest not found: $manifest" >&2
  exit 2
fi

metadata="$(node - "$manifest" <<'NODE'
const fs = require('fs');
const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (manifest.schema !== 'chromium-stealthcdp.artifact.v1') {
  throw new Error(`unsupported manifest schema: ${manifest.schema}`);
}
if (manifest.platform !== 'win') {
  throw new Error(`install-windows-user requires a win artifact, got: ${manifest.platform}`);
}
if (!manifest.artifactName) {
  throw new Error('manifest does not include artifactName');
}
if (manifest.executable?.relativePath !== 'chrome-win64/chrome.exe') {
  throw new Error(`unexpected executable path: ${manifest.executable?.relativePath}`);
}
console.log(JSON.stringify({ artifactName: manifest.artifactName }));
NODE
)"
artifact_name="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.artifactName)' "$metadata")"

if [[ ! -f "$artifact/chrome-win64/chrome.exe" ]]; then
  echo "artifact does not contain chrome-win64/chrome.exe: $artifact" >&2
  exit 2
fi

if [[ -z "$install_root" ]]; then
  local_app_data="$("$powershell_cmd" -NoProfile -Command '[Console]::Out.Write($env:LOCALAPPDATA)')"
  install_root="$(wslpath -u "$local_app_data")/chromium-stealthcdp"
fi

mkdir -p "$install_root"
install_root="$(realpath "$install_root")"
dest="$install_root/$artifact_name"
current="$install_root/current"

if [[ -e "$dest" ]]; then
  if [[ "$force" == "true" ]]; then
    rm -rf "$dest"
  else
    echo "install destination already exists: $dest" >&2
    echo "rerun with --force to replace it" >&2
    exit 1
  fi
fi

mkdir -p "$dest"
cp -a "$artifact/chrome-win64/." "$dest/"
cp -a "$artifact/manifest.json" "$dest/manifest.json"
if [[ -f "$artifact/smoke-win.json" ]]; then
  cp -a "$artifact/smoke-win.json" "$dest/smoke-win.json"
fi
cp -a "$artifact/patches.sha256" "$dest/patches.sha256"
cp -a "$artifact/patches" "$dest/patches"

dest_win="$(wslpath -w "$dest")"
current_win="$(wslpath -w "$current")"
"$powershell_cmd" -NoProfile -Command "\
  \$dest = '$dest_win'; \
  \$current = '$current_win'; \
  icacls.exe \$dest /grant '*S-1-15-2-1:(OI)(CI)(RX)' '*S-1-15-2-2:(OI)(CI)(RX)' /T /Q | Out-Null; \
  if (Test-Path -LiteralPath \$current) { Remove-Item -LiteralPath \$current -Force }; \
  New-Item -ItemType Junction -Path \$current -Target \$dest | Out-Null"

echo "installed $dest"
echo "current -> $artifact_name"
echo "executable: $current/chrome.exe"
