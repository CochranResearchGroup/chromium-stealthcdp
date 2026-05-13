#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/promote-artifact.sh --src-out PATH [--artifact-root PATH] [--smoke-json PATH] [--platform linux|win]

Promotes a built Chromium output directory into a versioned chromium-stealthcdp
runtime artifact. The source build must already pass the matching smoke script.
EOF
}

src_out=""
artifact_root=""
smoke_json=""
platform="linux"

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
    --platform)
      platform="${2:-}"
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

case "$platform" in
  linux)
    smoke_json="${smoke_json:-$repo_root/smoke.json}"
    chrome="$src_out/chrome"
    artifact_runtime_dir="chrome-linux"
    executable_rel="$artifact_runtime_dir/chrome"
    smoke_rel="smoke.json"
    if [[ ! -x "$chrome" ]]; then
      echo "chrome is not executable: $chrome" >&2
      exit 2
    fi
    ;;
  win)
    smoke_json="${smoke_json:-$repo_root/smoke-win.json}"
    chrome="$src_out/chrome.exe"
    artifact_runtime_dir="chrome-win64"
    executable_rel="$artifact_runtime_dir/chrome.exe"
    smoke_rel="smoke-win.json"
    if [[ ! -f "$chrome" ]]; then
      echo "chrome.exe not found: $chrome" >&2
      exit 2
    fi
    ;;
  *)
    echo "unsupported platform: $platform" >&2
    exit 2
    ;;
esac

if [[ ! -f "$smoke_json" ]]; then
  echo "smoke JSON not found: $smoke_json" >&2
  exit 2
fi
smoke_json="$(realpath "$smoke_json")"

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
if [[ "$platform" == "linux" ]]; then
  chrome_version="$("$chrome" --version | sed 's/[[:space:]]*$//')"
else
  chrome_version="$(node -e 'const s=require(process.argv[1]); console.log((s.chromeVersion || "").trim())' "$smoke_json")"
fi
if [[ -z "$chrome_version" ]]; then
  echo "could not determine chrome version" >&2
  exit 1
fi
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

mkdir -p "$dest/$artifact_runtime_dir" "$dest/patches"

if [[ "$platform" == "linux" ]]; then
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

  runtime_dirs=(
    locales
    resources
    MEIPreload
    PrivacySandboxAttestationsPreloaded
    hyphen-data
    IwaKeyDistribution
  )
else
  runtime_files=(
    chrome.exe
    chrome.dll
    chrome_elf.dll
    chrome_100_percent.pak
    chrome_200_percent.pak
    d3dcompiler_47.dll
    dxcompiler.dll
    dxil.dll
    headless_command_resources.pak
    icudtl.dat
    libEGL.dll
    libGLESv2.dll
    resources.pak
    snapshot_blob.bin
    v8_context_snapshot.bin
    vk_swiftshader.dll
    vk_swiftshader_icd.json
    vulkan-1.dll
    msvcp140.dll
    msvcp140_atomic_wait.dll
    vccorlib140.dll
    vcruntime140.dll
    vcruntime140_1.dll
  )

  runtime_dirs=(
    locales
    resources
    MEIPreload
    PrivacySandboxAttestationsPreloaded
    hyphen-data
    IwaKeyDistribution
    swiftshader
  )
fi

for file in "${runtime_files[@]}"; do
  if [[ -e "$src_out/$file" ]]; then
    cp -a "$src_out/$file" "$dest/$artifact_runtime_dir/"
  fi
done

if [[ "$platform" == "win" ]]; then
  shopt -s nullglob
  for manifest in "$src_out"/*.manifest; do
    cp -a "$manifest" "$dest/$artifact_runtime_dir/"
  done
  shopt -u nullglob
fi

for dir in "${runtime_dirs[@]}"; do
  if [[ -d "$src_out/$dir" ]]; then
    cp -a "$src_out/$dir" "$dest/$artifact_runtime_dir/"
  fi
done

cp -a "$repo_root"/patches/*.patch "$dest/patches/"
cp -a "$smoke_json" "$dest/$smoke_rel"

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
PLATFORM="$platform" \
EXECUTABLE_REL="$executable_rel" \
SMOKE_REL="$smoke_rel" \
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
const executableRel = process.env.EXECUTABLE_REL;
const smokeRel = process.env.SMOKE_REL;
const chromePath = path.join(artifactPath, executableRel);

function sha256(file) {
  const hash = crypto.createHash('sha256');
  hash.update(fs.readFileSync(file));
  return hash.digest('hex');
}

const manifest = {
  schema: 'chromium-stealthcdp.artifact.v1',
  artifactName: process.env.ARTIFACT_NAME,
  platform: process.env.PLATFORM,
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
    relativePath: executableRel,
    sha256: sha256(chromePath),
  },
  smoke: {
    relativePath: smokeRel,
    sha256: sha256(path.join(artifactPath, smokeRel)),
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
echo "executable: $artifact_root/current/$executable_rel"
