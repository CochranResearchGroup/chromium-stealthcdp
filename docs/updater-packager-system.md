# Updater And Packager System Plan

Date: 2026-05-12

## Objective

House the Chromium update, patch application, build, artifact promotion, and
`.deb` packaging workflow in this patchset repo. The system must work from a
clean machine with no existing Chromium build tree, while also supporting fast
incremental updates when a checkout already exists.

The output should be a promoted `chromium-stealthcdp` runtime artifact that
agent-browser can consume through a stable executable path, plus an optional
side-by-side Debian package for operational deployment.

## Non-Goals

- Do not replace or overwrite system Chromium or Google Chrome.
- Do not make `out/Default/chrome` the promoted runtime contract.
- Do not hide local DevTools endpoints, process flags, or package identity from
  local machine users.
- Do not add broad fingerprint patches as part of packaging.

## Repository Layout

Add these tracked paths to this repo:

```text
scripts/
  bootstrap-checkout.sh
  update-upstream.sh
  apply-patches.sh
  build.sh
  smoke.sh
  promote-artifact.sh
  package-deb.sh
  verify-installed.sh
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

## Promotion Contract

`scripts/promote-artifact.sh` copies a known-good build out of `out/`.

Promoted layout:

```text
artifacts/chromium-stealthcdp/
  <chromium-version>+stealthcdp.<patchset-short-sha>/
    chrome-linux/
      chrome
      chrome-wrapper
      ...
    manifest.json
    smoke.json
    patches/
      0001-...
```

The promoted executable path should be stable through a symlink:

```text
artifacts/chromium-stealthcdp/current/chrome-linux/chrome
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

## Freshness Checks

Add `scripts/check-freshness.sh`.

It should compare:

- current `src` Chromium SHA
- current patchset repo SHA
- promoted artifact manifest Chromium SHA
- promoted artifact manifest patchset SHA
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
- Add Debian metadata.
- Package the promoted artifact side-by-side under `/opt/chromium-stealthcdp`.
- Verify install, executable path, version, and webdriver smoke.

### Phase 4: Agent-Browser Guardrails

- Update the agent-browser handoff to prefer promoted artifacts.
- Add an agent-browser-side freshness warning or preflight check.
- Keep headed Canva/profile instability tracked in agent-browser, not in this
  Chromium patchset, unless a patched-vs-stock Chromium differential is proven.

## Release Gate

A binary or `.deb` is releasable only when all are true:

- Patch queue applies cleanly to the recorded Chromium revision.
- Build succeeds.
- Smoke returns `navigator.webdriver=false` through CDP.
- Promoted artifact has a complete manifest.
- Source tree and patchset repo are clean after promotion metadata is reviewed.
- For `.deb`, install verification passes without replacing system browsers.
