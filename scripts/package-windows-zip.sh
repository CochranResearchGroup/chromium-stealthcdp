#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/package-windows-zip.sh [--artifact PATH] [--output-dir PATH]

Builds a side-by-side Windows zip package from a promoted
chromium-stealthcdp artifact. The artifact must contain chrome-win64/chrome.exe.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
output_dir="$repo_root/../artifacts/chromium-stealthcdp/packages"
package_name="chromium-stealthcdp"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --artifact)
      artifact="${2:-}"
      shift 2
      ;;
    --output-dir)
      output_dir="${2:-}"
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

if ! command -v zip >/dev/null 2>&1; then
  echo "required tool not found: zip" >&2
  exit 2
fi

if [[ ! -e "$artifact" ]]; then
  echo "artifact does not exist: $artifact" >&2
  exit 2
fi

artifact="$(realpath "$artifact")"
manifest="$artifact/manifest.json"
if [[ ! -f "$manifest" ]]; then
  echo "artifact manifest does not exist: $manifest" >&2
  exit 2
fi

metadata="$(node - "$manifest" <<'NODE'
const fs = require('fs');
const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
if (manifest.schema !== 'chromium-stealthcdp.artifact.v1') {
  throw new Error(`unsupported manifest schema: ${manifest.schema}`);
}
const chromeVersion = manifest.chromeVersion || '';
const versionNumber = chromeVersion.replace(/^Chromium\s+/, '').trim();
if (!versionNumber) {
  throw new Error('manifest does not include a Chromium version');
}
const patchsetSha = manifest.patchset && manifest.patchset.repoSha;
if (!patchsetSha) {
  throw new Error('manifest does not include patchset repo SHA');
}
const patchQueueSha = manifest.patchset && manifest.patchset.patchQueueSha256;
const packageIdentitySha = patchQueueSha || patchsetSha;
console.log(JSON.stringify({
  versionNumber,
  patchsetShort: packageIdentitySha.slice(0, 12),
}));
NODE
)"

version_number="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.versionNumber)' "$metadata")"
patchset_short="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.patchsetShort)' "$metadata")"
zip_name="${package_name}_${version_number}+stealthcdp.${patchset_short}_win64.zip"

if [[ ! -f "$artifact/chrome-win64/chrome.exe" ]]; then
  echo "artifact does not contain chrome-win64/chrome.exe: $artifact" >&2
  exit 2
fi

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

stage="$tmpdir/$package_name"
mkdir -p "$stage"

cp -a "$artifact/chrome-win64/." "$stage/"
cp -a "$artifact/manifest.json" "$stage/manifest.json"
if [[ -f "$artifact/smoke-win.json" ]]; then
  cp -a "$artifact/smoke-win.json" "$stage/smoke-win.json"
elif [[ -f "$artifact/smoke.json" ]]; then
  cp -a "$artifact/smoke.json" "$stage/smoke.json"
fi
cp -a "$artifact/patches.sha256" "$stage/patches.sha256"
cp -a "$artifact/patches" "$stage/patches"

mkdir -p "$output_dir"
(
  cd "$tmpdir"
  zip -qr "$output_dir/$zip_name" "$package_name"
)

echo "$output_dir/$zip_name"
