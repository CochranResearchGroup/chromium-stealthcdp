# Handoff: Facebook line-breaker Chromium rebuild

Date: 2026-08-11

## Objective

Produce a new Linux `chromium-stealthcdp` candidate that no longer aborts at
the Blink `LineBreaker` assertion reached by authenticated Facebook posts
search. Preserve the existing `navigator.webdriver` patch, keep DCHECKs active
for validation, smoke-test the result, and stage a reproducible artifact for
agent-browser testing.

This packet authorizes a bounded source patch, clean build, focused tests, and
staged artifact. It does not authorize copying or clearing the retained
Facebook profile, switching a live browser runtime, or replacing the shared
artifact `current` symlink without a separate cutover decision.

## Start here

Repositories and evidence:

- patch queue: `/home/ecochran76/workspace.local/chromium/chromium-stealthcdp`
- Chromium source: `/home/ecochran76/workspace.local/chromium/src`
- agent-browser handoff:
  `/home/ecochran76/workspace.local/agent-browser/docs/dev/notes/2026-08-11-facebook-authenticated-search-blink-crash-handoff.md`
- downstream evidence ledger:
  `/home/ecochran76/workspace.local/last30days-skill/docs/dev/plans/0046-2026-08-11-facebook-retained-browser-runtime-recovery.md`
- renderer stderr:
  `/home/ecochran76/.agent-browser/tmp/chrome-launches/chrome-83786-1786451676608.stderr.log`

Before changing anything, confirm:

```sh
cd /home/ecochran76/workspace.local/chromium/chromium-stealthcdp
git status --short --branch
git rev-parse HEAD
git -C ../src status --short --branch
git -C ../src rev-parse HEAD
cat upstream-revision.txt
```

Expected handoff state:

- patchset branch `main` is clean at `fcf2d964f9070cc9acf7aabbfb2c576f36107bbe`
- patchset tracks `upstream/main`
- Chromium branch is `ec/chromium-stealthcdp`
- Chromium source is clean at
  `24ecda02e97db6fa730a7ccf8747776a4d21e4b9`
- recorded base is
  `d421c3af8268e2e6227b7fe4461183e69b64bc61`

Stop and reconcile rather than overwriting unexpected changes.

## Failure to repair

Two authenticated Facebook `/search/posts/` attempts aborted the renderer at
local times `08:38:32` and `08:42:10` with:

```text
FATAL:third_party/blink/renderer/core/layout/inline/line_breaker.cc:4102
DCHECK failed: item_result->EndOffset() <= item_result_before.EndOffset()
```

The Linux artifact that produced the failure is:

```text
/home/ecochran76/workspace.local/chromium/artifacts/chromium-stealthcdp/150.0.7835.0+stealthcdp.3676a7503929
```

Its pinned identity is:

- Chromium `150.0.7835.0`
- Chromium source SHA
  `24ecda02e97db6fa730a7ccf8747776a4d21e4b9`
- upstream revision
  `d421c3af8268e2e6227b7fe4461183e69b64bc61`
- patchset SHA
  `3676a7503929fc2ff1ce0227c03c48aeaa4b1bae`
- executable SHA256
  `aebeac48273efa3a2767763cf0694cfa8f1be52c91b7fbafff0d4698a993ffce`

The existing custom patch changes only
`third_party/blink/renderer/core/frame/navigator.cc`. It did not introduce the
failing line-breaker code.

The current Linux output was generated with `is_debug=false`, but its
toolchain includes `-DDCHECK_ALWAYS_ON=1`. Generated metadata reports
`is_official_build=false` and `dcheck_always_on=true`. The failure is therefore
fatal in this custom release-like build.

## Source-backed repair direction

The pinned source at
`third_party/blink/renderer/core/layout/inline/line_breaker.cc` calls
`BreakText()` and then asserts:

```cpp
DCHECK_LE(item_result->EndOffset(), item_result_before.EndOffset());
```

The surrounding old code already restores `item_result_before` when the
shorter break attempt does not fit. The assertion aborts before that recovery
can run.

Newer official Chromium source no longer contains this ordering assertion. It
documents that reshaping, especially at very large font sizes, and
float-to-`LayoutUnit` rounding can legitimately make the new `EndOffset()`
larger. It then follows the existing failure path and restores the original
item:

<https://chromium.googlesource.com/chromium/src/third_party/+/96119100e5da49d2272838031187f113b0d231cd/blink/renderer/core/layout/inline/line_breaker.cc>

The exact Chromium change list that introduced that upstream behavior was not
identified during diagnosis. Find and record it before finalizing the patch if
possible.

## Recommended implementation

Use a dedicated Chromium source branch from the current patched source SHA.
Keep `upstream-revision.txt` unchanged if this is a narrow second patch on the
same base.

Add a second patch that backports the upstream handling:

1. Remove only the invalid `DCHECK_LE` at the identified `BreakText()` call.
2. Preserve `item_result->CheckConsistency(true)` under `DCHECK_IS_ON()`.
3. Preserve the existing `HasHyphen()` cleanup and
   `*item_result = std::move(item_result_before)` restoration.
4. Add the upstream explanation for why a larger end offset is possible.
5. Add or port the focused upstream regression if the originating change list
   contains one. If no source-level reproducer is available, record that gap
   explicitly rather than inventing a claim of coverage.

Do not disable DCHECKs globally and do not change `navigator.webdriver` as part
of this patch.

The intended queue after export is:

```text
patches/0001-Make-navigator.webdriver-non-advertising.patch
patches/0002-Handle-line-break-reshaping-offset-growth.patch
```

Use a descriptive subject if the upstream change list provides a canonical
title. Preserve upstream authorship and attribution when backporting an exact
change.

## Patch export and documentation

Commit the new change in `../src`, then regenerate the patch queue from the
recorded base using the repository's canonical export flow:

```sh
cd /home/ecochran76/workspace.local/chromium/src
rm -f ../chromium-stealthcdp/patches/*.patch
git format-patch --binary \
  -o ../chromium-stealthcdp/patches \
  "$(cat ../chromium-stealthcdp/upstream-revision.txt)..HEAD"
```

Review the resulting patches before committing the patchset repo:

```sh
git -C ../chromium-stealthcdp diff --check
git -C ../chromium-stealthcdp diff --stat
git -C ../chromium-stealthcdp diff -- patches/
```

Update `docs/chromium-patch-boundary.md` to record this narrow browser-internal
compatibility exception. The crash cannot be repaired in agent-browser after
Blink has aborted. Keep the existing anti-fingerprinting non-goals intact.

Do not rewrite `docs/minimal-stealthcdp-plan.md` as though the new patch were a
stealth requirement. Reference it as a separately justified compatibility
patch.

## Focused validation

Build in a new output directory so the old `out/Default` state remains
available for comparison:

```sh
cd /home/ecochran76/workspace.local/chromium/chromium-stealthcdp
scripts/build.sh \
  --src ../src \
  --out out/FacebookLineBreakFix \
  --target chrome \
  --gn-args 'is_debug=false dcheck_always_on=true symbol_level=0 blink_symbol_level=0 v8_symbol_level=0 is_component_build=false'
```

After GN generation, verify the candidate really retains DCHECKs:

```sh
cat ../src/out/FacebookLineBreakFix/args.gn
rg -n -m 1 --fixed-strings -- '-DDCHECK_ALWAYS_ON=1' \
  ../src/out/FacebookLineBreakFix/toolchain.ninja
```

Build and run the focused Blink unit target when practical:

```sh
cd /home/ecochran76/workspace.local/chromium/src
autoninja -C out/FacebookLineBreakFix blink_unittests
out/FacebookLineBreakFix/blink_unittests \
  --gtest_filter='LineBreakerTest.*'
```

Run the repository smoke with an ephemeral profile:

```sh
cd /home/ecochran76/workspace.local/chromium/chromium-stealthcdp
scripts/smoke.sh \
  --chrome ../src/out/FacebookLineBreakFix/chrome \
  --output /tmp/chromium-stealthcdp-facebook-line-break-fix-smoke.json
```

Required smoke result:

- Chromium launches successfully
- CDP is reachable
- `navigator.webdriver` is `false`
- smoke JSON has `success: true`

The ordinary smoke does not exercise Facebook or the line-breaker failure. Do
not treat it as end-to-end acceptance.

## Stage the artifact safely

The shared artifact root currently has a cross-platform `current` symlink. At
handoff it resolves to the Windows artifact
`150.0.7835.0+stealthcdp.6b6558b55a1d`. A normal Linux promotion into that root
would silently repoint `current` away from Windows.

Stage the Linux candidate in a separate root first:

```sh
cd /home/ecochran76/workspace.local/chromium/chromium-stealthcdp
scripts/promote-artifact.sh \
  --platform linux \
  --src-out ../src/out/FacebookLineBreakFix \
  --artifact-root ../artifacts/chromium-stealthcdp-candidates/facebook-line-break-fix \
  --smoke-json /tmp/chromium-stealthcdp-facebook-line-break-fix-smoke.json
```

Verify the staged manifest and hashes:

```sh
jq . \
  ../artifacts/chromium-stealthcdp-candidates/facebook-line-break-fix/current/manifest.json
scripts/check-freshness.sh \
  --src ../src \
  --artifact ../artifacts/chromium-stealthcdp-candidates/facebook-line-break-fix/current
```

Acceptance requires `fresh: true`, clean Chromium and patchset identities, and
an executable hash that matches the staged manifest.

Do not update `../artifacts/chromium-stealthcdp/current` during this packet.
The platform-neutral symlink needs an explicit ownership decision or a
follow-up change to introduce platform-specific aliases such as
`current-linux` and `current-win`.

## Agent-browser validation handoff

After source tests, smoke, and staged-manifest verification pass, give
agent-browser the explicit staged executable path. Do not rely on the shared
`current` alias.

The browser validation must use a disposable browser lane. An authenticated
Facebook comparison requires an operator-seeded disposable profile or explicit
authority to copy private profile state. The rebuild packet does not grant
that authority.

Required end-to-end evidence:

- the same authenticated Facebook posts-search workload reaches renderer
  content without the old `line_breaker.cc` abort;
- the candidate still reports `navigator.webdriver === false`;
- Facebook home and a non-Facebook control continue to render;
- a renderer crash, if any, is reported as a typed agent-browser failure rather
  than leaving the tab lifecycle `ready`; and
- the command, caller, requested profile, detected profile, PID, endpoint,
  target ID, and stderr path are retained in the incident evidence.

Only after that validation should an operator decide whether to promote the
candidate into the production Linux alias and retry the downstream Facebook
tick once.

## Acceptance checklist

- [ ] Starting patchset and Chromium identities recorded
- [ ] Originating Chromium change list identified, or attribution gap recorded
- [ ] Narrow second source commit created without global DCHECK changes
- [ ] Patch queue exported from the recorded base
- [ ] Patch boundary documentation updated
- [ ] Patchset and Chromium worktrees clean at build time
- [ ] Candidate build retains `DCHECK_ALWAYS_ON=1`
- [ ] Focused `LineBreakerTest.*` tests pass, or exact test limitation recorded
- [ ] `scripts/smoke.sh` passes with `navigator.webdriver=false`
- [ ] Candidate staged outside the shared platform-neutral `current` alias
- [ ] Staged artifact freshness and manifest hashes pass
- [ ] Disposable agent-browser validation passes
- [ ] No retained profile mutation or live runtime cutover occurred implicitly

## Hard stops

- Do not delete, clear, copy, or migrate the retained Facebook profile.
- Do not disable DCHECKs globally to make the crash disappear.
- Do not overwrite unexpected patchset or Chromium source changes.
- Do not promote a dirty source or dirty patchset artifact.
- Do not repoint the shared `current` symlink without an explicit cutover
  decision.
- Do not claim the Facebook bug fixed from unit tests or the ordinary smoke
  alone.

## Suggested skills

- `diagnosing-bugs` for preserving the source-backed cause and controls
- `tdd` for the focused Blink regression
- `agent-browser` for the disposable browser and final authenticated validation
- `codebase-investigator` if broader Chromium impact analysis becomes necessary

## Handoff state

No Chromium source, patch queue, build output, artifact, browser runtime, or
profile was changed while writing this note. The requested rebuild remains to
be executed by the receiving agent.
