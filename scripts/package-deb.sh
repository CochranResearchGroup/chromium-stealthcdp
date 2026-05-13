#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/package-deb.sh [--artifact PATH] [--output-dir PATH] [--revision N] [--maintainer TEXT]

Builds a side-by-side Debian package from a promoted chromium-stealthcdp
artifact. This script packages the promoted artifact only; it does not read or
copy from a live Chromium out directory.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact="$repo_root/../artifacts/chromium-stealthcdp/current"
output_dir="$repo_root/../artifacts/chromium-stealthcdp/packages"
revision="1"
package_name="chromium-stealthcdp"
maintainer="Chromium StealthCDP Maintainers <no-reply@example.com>"

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
    --revision)
      revision="${2:-}"
      shift 2
      ;;
    --maintainer)
      maintainer="${2:-}"
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
const artifactName = manifest.artifactName || `${versionNumber}+stealthcdp.${patchsetSha.slice(0, 12)}`;
const executable = manifest.executable && manifest.executable.relativePath;
if (!executable) {
  throw new Error('manifest does not include executable relative path');
}
console.log(JSON.stringify({
  versionNumber,
  artifactName,
  patchsetShort: patchsetSha.slice(0, 12),
  executable,
}));
NODE
)"

version_number="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.versionNumber)' "$metadata")"
patchset_short="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.patchsetShort)' "$metadata")"
executable_rel="$(node -e 'const m=JSON.parse(process.argv[1]); console.log(m.executable)' "$metadata")"
package_version="${version_number}+stealthcdp.${patchset_short}-${revision}"
deb_name="${package_name}_${package_version}_amd64.deb"

if [[ ! -x "$artifact/$executable_rel" ]]; then
  echo "artifact executable is not runnable: $artifact/$executable_rel" >&2
  exit 2
fi

tmpdir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

stage="$tmpdir/${package_name}_${package_version}"
install_root="$stage/opt/chromium-stealthcdp"
mkdir -p "$stage/DEBIAN" "$install_root" "$stage/usr/bin" "$stage/usr/share/doc/$package_name" "$stage/usr/share/man/man1"

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
  if [[ -e "$artifact/chrome-linux/$file" ]]; then
    cp -a "$artifact/chrome-linux/$file" "$install_root/"
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
  if [[ -d "$artifact/chrome-linux/$dir" ]]; then
    cp -a "$artifact/chrome-linux/$dir" "$install_root/"
  fi
done

cp -a "$artifact/manifest.json" "$install_root/manifest.json"
cp -a "$artifact/smoke.json" "$install_root/smoke.json"
cp -a "$artifact/patches.sha256" "$install_root/patches.sha256"
cp -a "$artifact/patches" "$install_root/patches"
ln -s /opt/chromium-stealthcdp/chrome "$stage/usr/bin/chromium-stealthcdp"

cat > "$stage/usr/share/doc/$package_name/README" <<EOF
chromium-stealthcdp

Side-by-side Chromium build with the chromium-stealthcdp patch queue applied.

Executable:
  /usr/bin/chromium-stealthcdp

Manifest:
  /opt/chromium-stealthcdp/manifest.json
EOF

cat > "$stage/usr/share/doc/$package_name/copyright" <<'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: chromium-stealthcdp

Files: *
Copyright: 2026 Chromium StealthCDP local package maintainers
           and Chromium authors and other upstream rightsholders
License: Chromium
 This package is a local redistribution of a Chromium build with the
 chromium-stealthcdp patch queue applied. Chromium source licensing applies to
 the bundled browser files. See the Chromium source tree for complete license
 notices.
EOF

changelog_date="$(date -R)"
cat > "$tmpdir/changelog.Debian" <<EOF
$package_name ($package_version) local; urgency=medium

  * Package promoted chromium-stealthcdp artifact.

 -- $maintainer  $changelog_date
EOF
gzip -9n < "$tmpdir/changelog.Debian" > "$stage/usr/share/doc/$package_name/changelog.Debian.gz"

cat > "$tmpdir/chromium-stealthcdp.1" <<EOF
.TH CHROMIUM-STEALTHCDP 1 "$(date +%Y-%m-%d)" "$package_version" "User Commands"
.SH NAME
chromium-stealthcdp \\- side-by-side Chromium build with the chromium-stealthcdp patch queue
.SH SYNOPSIS
.B chromium-stealthcdp
[\fICHROMIUM OPTIONS\fR]
.SH DESCRIPTION
.B chromium-stealthcdp
launches the packaged Chromium binary installed under
.B /opt/chromium-stealthcdp.
It is intended for agent-browser validation and runtime use without replacing
the system Chromium or Google Chrome installation.
.SH FILES
.TP
.B /opt/chromium-stealthcdp/manifest.json
Build, source, and patchset provenance for the installed artifact.
EOF
gzip -9n < "$tmpdir/chromium-stealthcdp.1" > "$stage/usr/share/man/man1/chromium-stealthcdp.1.gz"

find "$stage" -type d -exec chmod 0755 {} +
find "$stage" -type f -exec chmod 0644 {} +
chmod 0755 "$install_root/chrome"
if [[ -f "$install_root/chrome_crashpad_handler" ]]; then
  chmod 0755 "$install_root/chrome_crashpad_handler"
fi

installed_size="$(du -ks "$stage" | awk '{print $1}')"

cat > "$stage/DEBIAN/control" <<EOF
Package: $package_name
Version: $package_version
Section: web
Priority: optional
Architecture: amd64
Installed-Size: $installed_size
Maintainer: $maintainer
Depends: libc6, libasound2t64 | libasound2, libatk-bridge2.0-0t64 | libatk-bridge2.0-0, libatk1.0-0t64 | libatk1.0-0, libatspi2.0-0, libcairo2, libcups2t64 | libcups2, libdbus-1-3, libdrm2, libexpat1, libgbm1, libgcc-s1, libglib2.0-0t64 | libglib2.0-0, libnspr4, libnss3, libpango-1.0-0, libudev1, libx11-6, libxcb1, libxcomposite1, libxdamage1, libxext6, libxfixes3, libxkbcommon0, libxrandr2
Description: Side-by-side Chromium build for agent-browser stealth CDP
 Chromium build with the chromium-stealthcdp patch queue applied. It installs
 under /opt/chromium-stealthcdp and exposes /usr/bin/chromium-stealthcdp without
 replacing system Chromium or Google Chrome.
EOF

mkdir -p "$output_dir"
dpkg-deb --root-owner-group --build "$stage" "$output_dir/$deb_name" >/dev/null

echo "$output_dir/$deb_name"
