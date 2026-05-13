#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/diagnose-windows-toolchain.sh

Checks whether this WSL host can package a local Windows Chromium cross-build
toolchain. It does not install or modify Visual Studio.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
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
  echo "PowerShell not found from WSL" >&2
  exit 2
fi

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

script="$tmpdir/diagnose-windows-toolchain.ps1"
cat > "$script" <<'PS1'
$ErrorActionPreference = "Stop"

function FirstPath($Root, $Filter, $Pattern = $null) {
  if (-not (Test-Path -LiteralPath $Root)) {
    return $null
  }
  $items = Get-ChildItem -LiteralPath $Root -Recurse -Filter $Filter -ErrorAction SilentlyContinue
  if ($Pattern) {
    $items = $items | Where-Object { $_.FullName -like $Pattern }
  }
  $items | Select-Object -First 1 -ExpandProperty FullName
}

$vswhere = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vs = $null
if (Test-Path -LiteralPath $vswhere) {
  $vsJson = & $vswhere -prerelease -format json
  if ($vsJson) {
    $vs = $vsJson | ConvertFrom-Json | Select-Object -First 1
  }
}

$programFiles = [Environment]::GetFolderPath("ProgramFiles")
$programFilesX86 = [Environment]::GetFolderPath("ProgramFilesX86")
$vsRoot = if ($vs) { $vs.installationPath } else { Join-Path $programFiles "Microsoft Visual Studio" }
$cl = FirstPath $vsRoot "cl.exe" "*\bin\Hostx64\x64\cl.exe"
$link = FirstPath $vsRoot "link.exe" "*\bin\Hostx64\x64\link.exe"
$vcvars = FirstPath $vsRoot "vcvarsall.bat"
$rc = FirstPath (Join-Path $programFilesX86 "Windows Kits\10") "rc.exe" "*\bin\10.0.26100.0\x64\rc.exe"
$midl = FirstPath (Join-Path $programFilesX86 "Windows Kits\10") "midl.exe" "*\bin\10.0.26100.0\x64\midl.exe"

$result = [ordered]@{
  powershell = $PSVersionTable.PSVersion.ToString()
  visualStudio = if ($vs) {
    [ordered]@{
      displayName = $vs.displayName
      installationPath = $vs.installationPath
      installationVersion = $vs.installationVersion
      isComplete = $vs.isComplete
      isLaunchable = $vs.isLaunchable
    }
  } else { $null }
  tools = [ordered]@{
    cl = $cl
    link = $link
    vcvarsall = $vcvars
    rc = $rc
    midl = $midl
  }
}

$result | ConvertTo-Json -Depth 5

if (-not $cl -or -not $link -or -not $vcvars -or -not $rc -or -not $midl) {
  exit 1
}
PS1

"$powershell_cmd" -NoProfile -ExecutionPolicy Bypass -File "$(wslpath -w "$script")"
