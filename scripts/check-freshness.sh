#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/check-freshness.sh [--src PATH] [--artifact PATH] [--installed PATH]

Checks whether a promoted or installed chromium-stealthcdp binary matches the
current Chromium source checkout and this patchset repo.

Exit codes:
  0  fresh
  1  stale
  2  missing artifact or executable
  3  invalid or incomplete manifest/artifact
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$repo_root/../src"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
installed=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src)
      src="${2:-}"
      shift 2
      ;;
    --artifact)
      artifact="${2:-}"
      shift 2
      ;;
    --installed)
      installed="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 3
      ;;
  esac
done

if [[ -n "$installed" ]]; then
  artifact="$installed"
fi

if [[ ! -d "$src/.git" ]]; then
  echo "missing Chromium source checkout: $src" >&2
  exit 2
fi

if [[ ! -e "$artifact" ]]; then
  echo "missing artifact: $artifact" >&2
  exit 2
fi

artifact="$(realpath "$artifact")"
manifest="$artifact/manifest.json"

if [[ ! -f "$manifest" ]]; then
  echo "missing manifest: $manifest" >&2
  exit 2
fi

set +e
check_output="$(REPO_ROOT="$repo_root" SRC_DIR="$src" ARTIFACT_DIR="$artifact" MANIFEST="$manifest" node <<'NODE'
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cp = require('child_process');

function git(dir, args) {
  return cp.execFileSync('git', ['-C', dir, ...args], { encoding: 'utf8' }).trim();
}

function sha256(file) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(file));
  return hash.digest('hex');
}

function fail(code, message, extra = {}) {
  console.log(JSON.stringify({
    schema: 'chromium-stealthcdp.freshness.v1',
    fresh: false,
    code,
    message,
    ...extra,
  }, null, 2));
  process.exit(code);
}

const repoRoot = process.env.REPO_ROOT;
const srcDir = process.env.SRC_DIR;
const artifactDir = process.env.ARTIFACT_DIR;
const manifestPath = process.env.MANIFEST;

let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
} catch (error) {
  fail(3, `invalid manifest JSON: ${error.message}`);
}

const required = [
  ['schema', manifest.schema],
  ['chromium.sourceSha', manifest.chromium && manifest.chromium.sourceSha],
  ['patchset.repoSha', manifest.patchset && manifest.patchset.repoSha],
  ['executable.relativePath', manifest.executable && manifest.executable.relativePath],
  ['executable.sha256', manifest.executable && manifest.executable.sha256],
  ['smoke.relativePath', manifest.smoke && manifest.smoke.relativePath],
  ['smoke.sha256', manifest.smoke && manifest.smoke.sha256],
  ['patches.sha256List', manifest.patches && manifest.patches.sha256List],
];
const missingFields = required.filter(([, value]) => !value).map(([name]) => name);
if (missingFields.length) {
  fail(3, 'manifest is incomplete', { missingFields });
}

if (manifest.schema !== 'chromium-stealthcdp.artifact.v1') {
  fail(3, `unsupported manifest schema: ${manifest.schema}`);
}

const executable = path.join(artifactDir, manifest.executable.relativePath);
const smoke = path.join(artifactDir, manifest.smoke.relativePath);
const patchShaList = path.join(artifactDir, manifest.patches.sha256List);
for (const file of [executable, smoke, patchShaList]) {
  if (!fs.existsSync(file)) {
    fail(2, `artifact file is missing: ${file}`);
  }
}

if (sha256(executable) !== manifest.executable.sha256) {
  fail(3, 'executable checksum does not match manifest', { executable });
}

if (sha256(smoke) !== manifest.smoke.sha256) {
  fail(3, 'smoke checksum does not match manifest', { smoke });
}

let smokeJson;
try {
  smokeJson = JSON.parse(fs.readFileSync(smoke, 'utf8'));
} catch (error) {
  fail(3, `invalid smoke JSON: ${error.message}`);
}
if (!smokeJson.success || String(smokeJson.checks && smokeJson.checks.navigatorWebdriver) !== 'false') {
  fail(3, 'smoke JSON does not prove navigator.webdriver=false', { smoke });
}

const currentChromiumSha = git(srcDir, ['rev-parse', 'HEAD']);
const currentPatchsetSha = git(repoRoot, ['rev-parse', 'HEAD']);
const srcDirty = git(srcDir, ['status', '--short', '--untracked-files=no']);
const patchsetDirty = git(repoRoot, ['status', '--short']);

const mismatches = [];
if (manifest.chromium.sourceSha !== currentChromiumSha) {
  mismatches.push({
    field: 'chromium.sourceSha',
    manifest: manifest.chromium.sourceSha,
    current: currentChromiumSha,
  });
}
if (manifest.patchset.repoSha !== currentPatchsetSha) {
  mismatches.push({
    field: 'patchset.repoSha',
    manifest: manifest.patchset.repoSha,
    current: currentPatchsetSha,
  });
}
if (srcDirty.length > 0) {
  mismatches.push({ field: 'chromium.dirty', manifest: false, current: true });
}
if (patchsetDirty.length > 0) {
  mismatches.push({ field: 'patchset.dirty', manifest: false, current: true });
}

if (mismatches.length) {
  fail(1, 'artifact is stale', {
    artifact: artifactDir,
    manifest: manifestPath,
    mismatches,
  });
}

console.log(JSON.stringify({
  schema: 'chromium-stealthcdp.freshness.v1',
  fresh: true,
  artifact: artifactDir,
  manifest: manifestPath,
  chromeVersion: manifest.chromeVersion,
  chromiumSha: currentChromiumSha,
  patchsetSha: currentPatchsetSha,
  executable,
}, null, 2));
NODE
)"
check_status=$?
set -e

printf '%s\n' "$check_output"
exit "$check_status"
