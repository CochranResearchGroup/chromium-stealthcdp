# Updater And Packager System Plan

Date: 2026-05-12

## Objective

House the Chromium update, patch application, build, artifact promotion, and
`.deb` packaging workflow in this patchset repo. The system must work from a
clean machine with no existing Chromium build tree, while also supporting fast
incremental updates when a checkout already exists.

The output should be a promoted `chromium-stealthcdp` runtime artifact that
agent-browser can consume through a stable executable path, plus an optional
side-by-side Debian package for operational deployment. A Windows lane should
use Chromium's Linux-to-Windows cross-build support from WSL, then launch and
smoke the resulting `.exe` through PowerShell on the Windows host.

## Non-Goals

- Do not replace or overwrite system Chromium or Google Chrome.
- Do not make `out/Default/chrome` the promoted runtime contract.
- Do not hide local DevTools endpoints, process flags, or package identity from
  local machine users.
- Do not add broad fingerprint patches as part of packaging.
- Do not require Wine for Windows validation when the WSL host can run the
  generated `.exe` through PowerShell.

## Repository Layout

Add these tracked paths to this repo:

```text
scripts/
  bootstrap-checkout.sh
  update-upstream.sh
  apply-patches.sh
  build.sh
  smoke.sh
  smoke-windows.ps1
  smoke-windows.sh
  check-freshness.sh
  promote-artifact.sh
  package-deb.sh
  package-windows-zip.sh
  verify-installed.sh
  verify-windows-artifact.sh
packaging/debian/
  control
  postinst
  prerm
  rules
  copyright
templates/
  build-manifest.json.in
  chromium-stealthcdp.desktop.in
artifacts/
  README.md
```

`artifacts/` should document local output locations but should not track large
build products. Release artifacts should live outside git, for example:

```text
/home/ecochran76/workspace.local/chromium/artifacts/chromium-stealthcdp/
```

## Bootstrap Contract

`scripts/bootstrap-checkout.sh` is the entrypoint when no build tree exists.

Inputs:

- `--workspace /path/to/chromium-parent`
- `--revision <chromium_git_sha|main|tag>`
- `--depot-tools /path/to/depot_tools`, optional
- `--no-history`, optional default for fresh bootstraps

Behavior:

1. Ensure `depot_tools` exists, cloning it if an explicit path was not supplied.
2. Create or reuse the Chromium parent directory.
3. Run `fetch --nohooks chromium` or `fetch --nohooks --no-history chromium`
   when no `src/` checkout exists.
4. Enter `src/`, fetch the requested upstream revision, and check it out on a
   deterministic branch:

   ```text
   ec/chromium-stealthcdp/<short-upstream-sha>
   ```

5. Run `gclient sync --with_branch_heads --with_tags` only when needed for that
   checkout state.
6. Run Chromium hooks.
7. Apply this repo's `patches/*.patch` with `git am`.
8. Write a bootstrap state file under the checkout:

   ```text
   .chromium-stealthcdp/state.json
   ```

The bootstrap command must be idempotent. If a checkout exists, it should refuse
to overwrite local changes unless passed an explicit `--force-clean-worktree`
flag.

## Update Contract

`scripts/update-upstream.sh` advances an existing Chromium checkout.

Inputs:

- `--src /path/to/chromium/src`
- `--revision <chromium_git_sha|origin/main|tag>`
- `--branch ec/chromium-stealthcdp`, optional default

Behavior:

1. Verify the working tree is clean.
2. Fetch Chromium upstream.
3. Create an update branch from the requested revision.
4. Apply `patches/*.patch` with `git am`.
5. Run a patch export check:

   ```sh
   git format-patch --binary <upstream>..HEAD
   ```

6. Update `upstream-revision.txt` only after the patch queue applies cleanly and
   the user explicitly asks to refresh the patchset repo.

The update script should not silently mutate tracked patch files. Patch export
is a separate, reviewable step.

## Build Contract

`scripts/build.sh` builds the patched checkout.

Inputs:

- `--src /path/to/chromium/src`
- `--out out/StealthCDP`, default
- `--target chrome`, default
- `--args-file packaging/gn/args.release.gn`, future

Behavior:

1. Verify the patch queue is applied by checking the reverse application of the
   current patch or by inspecting the patch commit range.
2. Generate GN args if the output directory does not exist.
3. Run:

   ```sh
   autoninja -C <out> chrome
   ```

4. Record build metadata in:

   ```text
   <out>/chromium-stealthcdp-build.json
   ```

The build metadata should include:

- Chromium source SHA
- patchset repo SHA
- patch file checksums
- `upstream-revision.txt`
- output directory
- GN args hash and copied args
- build started/finished timestamps
- `chrome --version`

## Windows Cross-Build Contract

The Windows lane should be explicit rather than overloading the Linux output
directory. A fresh checkout needs `target_os = ['win']` in `.gclient` before
`gclient sync`; an existing checkout can add it and resync.

Recommended output directory:

```text
../src/out/WinStealthCDP
```

Recommended GN args:

```gn
target_os = "win"
target_cpu = "x64"
is_debug = false
symbol_level = 0
is_component_build = false
```

Build command:

```sh
autoninja -C ../src/out/WinStealthCDP chrome
```

The Linux and Windows build lanes should share the same patch queue and
freshness model. A packaging-script-only commit must not force either binary to
be rebuilt; only a Chromium source SHA change or patch queue checksum change
should make artifacts stale.

If `gclient sync` fails in `src/build/vs_toolchain.py update --force` with a
Google Storage 401, this host cannot download Chromium's private packaged
Windows toolchain. The local fallback is to install the Visual Studio C++
components and Windows SDK locally, then package that install with
`depot_tools/win_toolchain/package_from_installed.py`.

Required local components:

```text
Microsoft.VisualStudio.Workload.NativeDesktop
Microsoft.VisualStudio.Component.VC.ATLMFC
Microsoft.VisualStudio.Component.VC.Tools.ARM64
Microsoft.VisualStudio.Component.VC.MFC.ARM64
Windows SDK 10.0.26100.0 with debuggers
```

`scripts/diagnose-windows-toolchain.sh` must find `cl.exe`, `link.exe`,
`vcvarsall.bat`, `rc.exe`, and `midl.exe` before this fallback is ready.

## Smoke Contract

`scripts/smoke.sh` is the promotion gate.

Required checks:

1. `chrome --version` runs.
2. Headless CDP launch succeeds with a temporary profile.
3. CDP `Runtime.evaluate` returns:

   ```text
   navigator.webdriver=false
   ```

4. The browser exits cleanly after the smoke.
5. No lingering patched Chromium processes remain from the smoke.

Optional checks:

- Fixed-port CDP mode.
- Remote debugging pipe mode.
- Agent-browser e2e smoke using `AGENT_BROWSER_EXECUTABLE_PATH`.

The smoke output should be machine-readable JSON plus concise console text.

## Windows Smoke Contract

The Windows smoke should launch `chrome.exe` on the Windows host through
PowerShell, then run the same CDP `navigator.webdriver` assertion from WSL.

Proposed scripts:

```text
scripts/smoke-windows.sh
scripts/smoke-windows.ps1
scripts/verify-windows-artifact.sh
```

`smoke-windows.sh` responsibilities:

1. Accept a WSL path to `chrome.exe`.
2. Convert paths with `wslpath -w`.
3. Create a temporary Windows user-data-dir under `%TEMP%`.
4. Invoke `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
   scripts/smoke-windows.ps1`.
5. Read the `DevToolsActivePort` file through the WSL-mounted Windows temp path.
6. Run the same CDP check used by `scripts/smoke.sh`.
7. Ask PowerShell to terminate only the process it launched.
8. Emit JSON with `platform: "win"` and `navigator.webdriver=false`.

`smoke-windows.ps1` responsibilities:

1. Start the provided `chrome.exe` with:

   ```text
   --headless=new
   --remote-debugging-port=0
   --user-data-dir=<temp-profile>
   --no-first-run
   --disable-default-apps
   ```

2. Return the Windows process id, profile directory, and `DevToolsActivePort`
   path to WSL.
3. Provide a cleanup mode that kills only the recorded process id.

This keeps Windows process ownership clear and avoids scanning for unrelated
Chromium processes.

## Promotion Contract

`scripts/promote-artifact.sh` copies a known-good build out of `out/`.

Promoted layout:

```text
artifacts/chromium-stealthcdp/
  <chromium-version>+stealthcdp.<patch-queue-short-sha>/
    chrome-linux/
      chrome
      chrome-wrapper
      ...
    chrome-win64/
      chrome.exe
      chrome.dll
      ...
    manifest.json
    smoke.json
    patches/
      0001-...
```

The promoted executable path should be stable through a symlink:

```text
artifacts/chromium-stealthcdp/current/chrome-linux/chrome
artifacts/chromium-stealthcdp/current/chrome-win64/chrome.exe
```

The manifest is the source of truth for freshness. Agent-browser should point at
the promoted path, not at `src/out/.../chrome`.

## Debian Package Contract

`scripts/package-deb.sh` packages a promoted artifact, not a live build tree.

Package name:

```text
chromium-stealthcdp
```

Install layout:

```text
/opt/chromium-stealthcdp/
  chrome
  manifest.json
  smoke.json
  patches/
/usr/bin/chromium-stealthcdp -> /opt/chromium-stealthcdp/chrome
```

Version scheme:

```text
<chromium-version>+stealthcdp.<patchset-version>-1
```

Example:

```text
150.0.7835.0+stealthcdp.1-1
```

The package should declare conflicts only with earlier package names owned by
this project. It should not conflict with `chromium`, `chromium-browser`, or
`google-chrome-stable`.

## Windows Package Contract

Start with a `.zip`, not an installer. A zip keeps the Windows lane easy to
build, inspect, and consume from agent-browser without registry or Start Menu
side effects.

Installed Windows executables must live on the Windows filesystem, not under
the WSL checkout. For a user-scoped install from WSL, use the WSL tenant
owner's LocalAppData tree:

```text
/mnt/c/Users/<windows-user>/AppData/Local/chromium-stealthcdp/
  <chromium-version>+stealthcdp.<patch-queue-short-sha>/
    chrome.exe
    chrome.dll
    manifest.json
    smoke-win.json
    patches/
  current -> <versioned install directory>
```

On the present workstation the tenant owner is `ecoch`, so the stable installed
path is:

```text
/mnt/c/Users/ecoch/AppData/Local/chromium-stealthcdp/current/chrome.exe
```

Proposed script:

```sh
scripts/package-windows-zip.sh \
  --artifact ../artifacts/chromium-stealthcdp/current \
  --output-dir ../artifacts/chromium-stealthcdp/packages

scripts/install-windows-user.sh \
  --artifact ../artifacts/chromium-stealthcdp/current \
  --force
```

Output name:

```text
chromium-stealthcdp_<chromium-version>+stealthcdp.<patch-queue-short-sha>_win64.zip
```

Zip layout:

```text
chromium-stealthcdp/
  chrome.exe
  manifest.json
  smoke-win.json
  patches/
```

Installer work, if needed later, should be a separate phase after the zip path
is proven with agent-browser.

## Freshness Checks

Add `scripts/check-freshness.sh`.

It should compare:

- current `src` Chromium SHA
- current patch queue checksum
- promoted artifact manifest Chromium SHA
- promoted artifact patch queue checksum, or normalized `patches.sha256` for
  artifacts created before that field existed
- installed package manifest, if present

Exit codes:

- `0`: promoted or installed binary matches requested source and patchset.
- `1`: binary is stale.
- `2`: binary is missing.
- `3`: manifest is invalid or incomplete.

## Agent-Browser Integration

Agent-browser should consume either:

```sh
AGENT_BROWSER_EXECUTABLE_PATH=/path/to/artifacts/chromium-stealthcdp/current/chrome-linux/chrome
```

or:

```sh
AGENT_BROWSER_EXECUTABLE_PATH=/usr/bin/chromium-stealthcdp
```

The handoff should recommend a freshness check before long-running managed
browser sessions.

## Implementation Phases

### Phase 1: Manifest And Smoke

- Add manifest template.
- Add `smoke.sh`.
- Add `promote-artifact.sh`.
- Promote the current validated build into a versioned artifact directory.

### Phase 2: Bootstrap And Update

- Add `bootstrap-checkout.sh`.
- Add `update-upstream.sh`.
- Add `apply-patches.sh`.
- Validate a fresh checkout can be created from only this repo plus network
  access to Chromium/depot_tools.

### Phase 3: Debian Packaging

- Add `package-deb.sh`.
- Add package metadata generated from the promoted artifact manifest.
- Package the promoted artifact side-by-side under `/opt/chromium-stealthcdp`.
- Verify install, executable path, version, and webdriver smoke with
  `verify-installed.sh`.

### Phase 4: Agent-Browser Guardrails

- Update the agent-browser handoff to prefer promoted artifacts.
- Add an agent-browser-side freshness warning or preflight check.
- Keep headed Canva/profile instability tracked in agent-browser, not in this
  Chromium patchset, unless a patched-vs-stock Chromium differential is proven.

### Phase 5: Windows Cross-Build And Zip Packaging

- Add `.gclient`/bootstrap support for `target_os = ['win']` with
  `ensure-windows-target.sh`.
- Add `diagnose-windows-toolchain.sh` to prove PowerShell, Visual Studio C++
  tools, and Windows SDK readiness before retrying `gclient sync`.
- Add `build.sh --target-os win --out out/WinStealthCDP`.
- Add `smoke-windows.sh` and `smoke-windows.ps1`.
- Extend `promote-artifact.sh` to copy `chrome-win64/` artifacts.
- Add `package-windows-zip.sh`.
- Add `install-windows-user.sh` so runnable Windows executables are copied to
  `%LOCALAPPDATA%\chromium-stealthcdp` and exposed through a `current` junction.
- Add `verify-windows-artifact.sh`.
- Verify the zip by extracting it, launching `chrome.exe` through PowerShell,
  and asserting `navigator.webdriver=false` over CDP from WSL.

## Release Gate

A binary or `.deb` is releasable only when all are true:

- Patch queue applies cleanly to the recorded Chromium revision.
- Build succeeds.
- Smoke returns `navigator.webdriver=false` through CDP.
- Promoted artifact has a complete manifest.
- Source tree and patchset repo are clean after promotion metadata is reviewed.
- For `.deb`, install verification passes without replacing system browsers.
- For Windows zip releases, PowerShell-launched smoke passes from an extracted
  zip without relying on `src/out/...`.
- For Windows user installs, the smoke must pass from
  `/mnt/c/Users/<windows-user>/AppData/Local/chromium-stealthcdp/current/chrome.exe`.
