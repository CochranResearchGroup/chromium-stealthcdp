#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/verify-installed.sh [--chrome PATH] [--manifest PATH] [--smoke-output PATH]

Verifies an installed or extracted chromium-stealthcdp package by checking its
manifest, version command, and navigator.webdriver CDP smoke.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chrome="/usr/bin/chromium-stealthcdp"
manifest="/opt/chromium-stealthcdp/manifest.json"
smoke_output="/tmp/chromium-stealthcdp-installed-smoke.json"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --chrome)
      chrome="${2:-}"
      shift 2
      ;;
    --manifest)
      manifest="${2:-}"
      shift 2
      ;;
    --smoke-output)
      smoke_output="${2:-}"
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

if [[ ! -x "$chrome" ]]; then
  echo "installed chrome is not executable: $chrome" >&2
  exit 2
fi

if [[ ! -f "$manifest" ]]; then
  echo "installed manifest not found: $manifest" >&2
  exit 2
fi

version="$("$chrome" --version | sed 's/[[:space:]]*$//')"
manifest_version="$(node -e 'const m=require(process.argv[1]); console.log(m.chromeVersion || "")' "$manifest")"
if [[ "$version" != "$manifest_version" ]]; then
  echo "version mismatch: chrome reports '$version', manifest reports '$manifest_version'" >&2
  exit 1
fi

"$repo_root/scripts/smoke.sh" --chrome "$chrome" --output "$smoke_output"

echo "installed verification passed: $chrome"
echo "manifest: $manifest"
echo "smoke: $smoke_output"
