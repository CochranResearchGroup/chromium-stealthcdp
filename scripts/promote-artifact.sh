#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/promote-artifact.sh --src-out PATH [--artifact-root PATH] [--smoke-json PATH]

Promotes a built Chromium output directory into a versioned chromium-stealthcdp
runtime artifact. The source build must already pass scripts/smoke.sh.
EOF
}

src_out=""
artifact_root=""
smoke_json=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src-out)
      src_out="${2:-}"
      shift 2
      ;;
    --artifact-root)
      artifact_root="${2:-}"
      shift 2
      ;;
    --smoke-json)
      smoke_json="${2:-}"
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

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src_out="${src_out:-$repo_root/../src/out/Default}"
artifact_root="${artifact_root:-$repo_root/../artifacts/chromium-stealthcdp}"
smoke_json="${smoke_json:-$repo_root/smoke.json}"

chrome="$src_out/chrome"
if [[ ! -x "$chrome" ]]; then
  echo "chrome is not executable: $chrome" >&2
  exit 2
fi

if [[ ! -f "$smoke_json" ]]; then
  echo "smoke JSON not found: $smoke_json" >&2
  exit 2
fi

if ! node -e 'const s=require(process.argv[1]); process.exit(s.success ? 0 : 1)' "$smoke_json"; then
  echo "smoke JSON does not report success: $smoke_json" >&2
  exit 1
fi

chromium_src="$(cd "$src_out/../.." && pwd)"
chromium_sha="$(git -C "$chromium_src" rev-parse HEAD)"
patchset_sha="$(git -C "$repo_root" rev-parse HEAD)"
patchset_dirty="$(git -C "$repo_root" status --short)"
chromium_dirty="$(git -C "$chromium_src" status --short --untracked-files=no)"
upstream_revision="$(tr -d '[:space:]' < "$repo_root/upstream-revision.txt")"
chrome_version="$("$chrome" --version | sed 's/[[:space:]]*$//')"
version_number="$(printf '%s\n' "$chrome_version" | awk '{print $2}')"
patch_queue_sha="$(
  cd "$repo_root/patches"
  find . -type f -name '*.patch' -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    | sed 's#  \./#  #' \
    | sha256sum \
    | awk '{print $1}'
)"
patchset_short="${patch_queue_sha:0:12}"
artifact_name="${version_number}+stealthcdp.${patchset_short}"
dest="$artifact_root/$artifact_name"

if [[ -e "$dest" ]]; then
  echo "artifact already exists: $dest" >&2
  exit 1
fi

mkdir -p "$dest/chrome-linux" "$dest/patches"

runtime_files=(
  chrome
  chrome_crashpad_handler
  chrome_100_percent.pak
  chrome_200_percent.pak
  headless_command_resources.pak
  icudtl.dat
  resources.pak
  snapshot_blob.bin
  v8_context_snapshot.bin
  libEGL.so
  libGLESv2.so
  libvk_swiftshader.so
  libVkICD_mock_icd.so
  libVkLayer_khronos_validation.so
  libqt5_shim.so
  libqt6_shim.so
)

for file in "${runtime_files[@]}"; do
  if [[ -e "$src_out/$file" ]]; then
    cp -a "$src_out/$file" "$dest/chrome-linux/"
  fi
done

runtime_dirs=(
  locales
  resources
  MEIPreload
  PrivacySandboxAttestationsPreloaded
  hyphen-data
  IwaKeyDistribution
)

for dir in "${runtime_dirs[@]}"; do
  if [[ -d "$src_out/$dir" ]]; then
    cp -a "$src_out/$dir" "$dest/chrome-linux/"
  fi
done

cp -a "$repo_root"/patches/*.patch "$dest/patches/"
cp -a "$smoke_json" "$dest/smoke.json"

(
  cd "$dest/patches"
  find . -type f -name '*.patch' -print0 \
    | sort -z \
    | xargs -0 sha256sum \
    | sed 's#  \./#  #'
) > "$dest/patches.sha256"

manifest_tmp="$dest/manifest.json.tmp"
ARTIFACT_NAME="$artifact_name" \
ARTIFACT_PATH="$dest" \
CHROME_VERSION="$chrome_version" \
CHROMIUM_SHA="$chromium_sha" \
PATCHSET_SHA="$patchset_sha" \
PATCH_QUEUE_SHA="$patch_queue_sha" \
PATCHSET_DIRTY="$patchset_dirty" \
CHROMIUM_DIRTY="$chromium_dirty" \
UPSTREAM_REVISION="$upstream_revision" \
SRC_OUT="$(realpath "$src_out")" \
PROMOTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
node - "$manifest_tmp" <<'NODE'
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const output = process.argv[2];
const artifactPath = process.env.ARTIFACT_PATH;
const chromePath = path.join(artifactPath, 'chrome-linux', 'chrome');

function sha256(file) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(file));
  return hash.digest('hex');
}

const manifest = {
  schema: 'chromium-stealthcdp.artifact.v1',
  artifactName: process.env.ARTIFACT_NAME,
  promotedAt: process.env.PROMOTED_AT,
  chromeVersion: process.env.CHROME_VERSION,
  chromium: {
    sourceSha: process.env.CHROMIUM_SHA,
    upstreamRevision: process.env.UPSTREAM_REVISION,
    sourceOut: process.env.SRC_OUT,
    dirty: process.env.CHROMIUM_DIRTY.length > 0,
  },
  patchset: {
    repoSha: process.env.PATCHSET_SHA,
    patchQueueSha256: process.env.PATCH_QUEUE_SHA,
    dirty: process.env.PATCHSET_DIRTY.length > 0,
  },
  executable: {
    relativePath: 'chrome-linux/chrome',
    sha256: sha256(chromePath),
  },
  smoke: {
    relativePath: 'smoke.json',
    sha256: sha256(path.join(artifactPath, 'smoke.json')),
  },
  patches: {
    relativePath: 'patches/',
    sha256List: 'patches.sha256',
  },
};

fs.writeFileSync(output, JSON.stringify(manifest, null, 2) + '\n');
NODE
mv "$manifest_tmp" "$dest/manifest.json"

ln -sfn "$artifact_name" "$artifact_root/current"

echo "promoted $dest"
echo "current -> $artifact_name"
echo "executable: $artifact_root/current/chrome-linux/chrome"
