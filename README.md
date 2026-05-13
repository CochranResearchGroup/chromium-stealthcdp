# chromium-stealthcdp

Patch queue for Chromium customizations related to stealth CDP behavior.

## Layout

- `upstream-revision.txt` records the Chromium base commit this queue is built on.
- `patches/` contains `git format-patch` output exported from `../src`.

## Working Branch

Development happens in the Chromium checkout at `../src` on branch:

```sh
ec/chromium-stealthcdp
```

## Export

From `../src`, export the current patch queue with:

```sh
rm -f ../chromium-stealthcdp/patches/*.patch
git format-patch --binary -o ../chromium-stealthcdp/patches "$(cat ../chromium-stealthcdp/upstream-revision.txt)..HEAD"
```

Then commit the updated patch files in this repository.

## Apply

From another Chromium `src` checkout at the recorded base revision or a compatible
descendant:

```sh
git am /path/to/chromium-stealthcdp/patches/*.patch
```

## Promote A Built Binary

Do not point downstream tools at `src/out/.../chrome` as a release contract.
Promote a smoke-tested build into the local artifact root instead:

```sh
scripts/smoke.sh \
  --chrome ../src/out/Default/chrome \
  --output /tmp/chromium-stealthcdp-smoke-current.json

scripts/promote-artifact.sh \
  --src-out ../src/out/Default \
  --artifact-root ../artifacts/chromium-stealthcdp \
  --smoke-json /tmp/chromium-stealthcdp-smoke-current.json
```

The stable local executable path is then:

```text
../artifacts/chromium-stealthcdp/current/chrome-linux/chrome
```

Each promoted artifact includes `manifest.json`, `smoke.json`, patch copies,
and patch checksums.

## Check Freshness

Before using a promoted binary for long-running agent-browser sessions, verify
that it still matches the current Chromium checkout and patchset repo:

```sh
scripts/check-freshness.sh \
  --src ../src \
  --artifact ../artifacts/chromium-stealthcdp/current
```

Exit code `0` means fresh, `1` means stale, `2` means missing, and `3` means the
manifest or artifact is invalid.

## Build a Debian Package

Package the promoted artifact, not the live Chromium build tree:

```sh
scripts/package-deb.sh \
  --artifact ../artifacts/chromium-stealthcdp/current \
  --output-dir ../artifacts/chromium-stealthcdp/packages
```

The package installs side-by-side under `/opt/chromium-stealthcdp` and exposes:

```text
/usr/bin/chromium-stealthcdp
```

Verify an installed package with:

```sh
scripts/verify-installed.sh
```

## Windows Cross-Build Plan

The Windows lane is tracked in `docs/updater-packager-system.md`. The intended
flow is to cross-build Chromium from WSL with `target_os = "win"`, launch the
resulting `chrome.exe` through PowerShell for smoke verification, promote it as
`chrome-win64/`, and package it first as a `.zip`.

After a Windows build exists, the artifact flow is:

```sh
scripts/smoke-windows.sh \
  --chrome ../src/out/WinStealthCDP/chrome.exe \
  --output /tmp/chromium-stealthcdp-smoke-win.json

scripts/promote-artifact.sh \
  --platform win \
  --src-out ../src/out/WinStealthCDP \
  --artifact-root ../artifacts/chromium-stealthcdp \
  --smoke-json /tmp/chromium-stealthcdp-smoke-win.json

scripts/package-windows-zip.sh \
  --artifact ../artifacts/chromium-stealthcdp/current \
  --output-dir ../artifacts/chromium-stealthcdp/packages
```
