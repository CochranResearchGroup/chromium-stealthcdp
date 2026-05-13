#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/verify-windows-artifact.sh [--artifact PATH] [--smoke-output PATH] [--remote-debugging-address ADDR]

Verifies a promoted or extracted Windows chromium-stealthcdp artifact by
launching chrome.exe through PowerShell and checking navigator.webdriver over
CDP from WSL.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
smoke_output="/tmp/chromium-stealthcdp-windows-smoke.json"
remote_debugging_address="127.0.0.1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --artifact)
      artifact="${2:-}"
      shift 2
      ;;
    --smoke-output)
      smoke_output="${2:-}"
      shift 2
      ;;
    --remote-debugging-address)
      remote_debugging_address="${2:-}"
      shift 2
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

if [[ ! -e "$artifact" ]]; then
  echo "artifact does not exist: $artifact" >&2
  exit 2
fi

artifact="$(realpath "$artifact")"
chrome="$artifact/chrome-win64/chrome.exe"
manifest="$artifact/manifest.json"

if [[ ! -f "$chrome" ]]; then
  echo "chrome.exe not found: $chrome" >&2
  exit 2
fi

if [[ ! -f "$manifest" ]]; then
  echo "manifest not found: $manifest" >&2
  exit 2
fi

"$repo_root/scripts/smoke-windows.sh" \
  --chrome "$chrome" \
  --output "$smoke_output" \
  --remote-debugging-address "$remote_debugging_address"

echo "windows artifact verification passed: $chrome"
echo "manifest: $manifest"
echo "smoke: $smoke_output"
