# Plan 0002: Production-stable Chromium build with developer-port masking

State: OPEN

Date: 2026-09-12

## Objective

Build and stage a fresh Linux `chromium-stealthcdp` candidate from the current
production Stable Chromium release, while preserving the downstream behavior
that keeps `navigator.webdriver` non-advertising when a developer/CDP port is
used.

## Current State

- The patchset repository began clean on `main` at
  `7a3ac43348ec3913504b8417ca2c276f4dd47ed1`.
- Chromium source began clean on `ec/chromium-stealthcdp-b84d5f5c` at
  `778b60e96df92414e75d0fb241b108ba1da452db`.
- The existing source base is Chromium `153.0.8003.0` from `main`, so it is a
  development snapshot rather than a production Stable release.
- Google's 2026-09-08 Stable desktop announcement identifies Linux Stable as
  `153.0.8010.36`. The corresponding Chromium tag resolves to upstream commit
  `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`.
- Patch 0001 forces `Navigator::webdriver()` to return `false`. The repository
  smoke launches with `--remote-debugging-port=0` and verifies that behavior,
  which is the requested developer-port masking contract for this build.
- Patch 0002 is a prior Blink crash repair. It will be replayed only if the
  stable source does not already contain an equivalent fix and the patch still
  applies cleanly and passes its focused regression test.

## Scope

1. Fetch and verify the exact Linux Stable tag and upstream commit.
2. Create a dedicated Chromium source branch from the pinned Stable commit.
3. Synchronize dependencies and hooks without destructive cleanup.
4. Replay and review the downstream masking patch.
5. Reconcile the Blink repair against Stable: retain it only when still needed.
6. Refresh the pinned revision and exported patch queue in this repository.
7. Build `chrome` in a new official-style release output directory without
   forcing diagnostic DCHECKs into the runtime.
8. Run focused tests for every retained source repair and run repository smoke.
9. Stage a reproducible candidate under a dedicated candidate artifact root.
10. Verify manifest, hashes, clean identities, and developer-port masking.

## Non-Goals

- Do not broaden masking into canvas, WebGL, audio, font, locale, timezone,
  device, command-line, socket, or other fingerprint spoofing.
- Do not conceal the listening TCP port from the local operating system or
  remove CDP functionality; the contract is the browser-visible
  `navigator.webdriver` signal while CDP is active.
- Do not mutate or reuse retained browser profiles.
- Do not install the candidate, repoint the shared platform-neutral `current`
  alias, publish, push, or run downstream production workloads.
- Do not carry patch 0002 merely for queue continuity if Stable already fixes
  the defect.

## Execution Graph

The primary agent owns the serialized critical path:

`pin Stable -> sync source -> reconcile patches -> export queue -> build -> tests -> smoke -> stage -> verify`

No subagent is spawned: the source checkout, patch queue, and build provenance
form one coupled write surface, and repository instructions say not to delegate
this exploration. One independent final evaluator is not available under the
current no-subagent execution constraint; validation is therefore primary-run
and evidence-bound.

## Execution Governance

- Plan version: `2`
- State transition: `ready -> active`
- Authority classification: standing authority for source refresh, patch
  replay/reconciliation, repo documentation, build, tests, smoke, and staging
  under a dedicated candidate root
- Unmet criteria: Stable pin, clean replay, build, focused validation, smoke,
  staged artifact, and freshness verification
- Ready unit: fetch and synchronize the exact Stable source revision
- Blocked units: installation, shared-alias cutover, publication, push, retained
  profile use, or downstream production execution
- Delegation: `not_spawned`; one coupled critical path and an explicit
  repository instruction to answer exploration directly
- Review discovery budget: one primary drift pass; any remediation verification
  is closed-world against accepted blocking findings
- Checkpoint cadence: after each validated packet
- Retry bounds: two attempts per work unit, one review/rework cycle, and at
  most two consecutive hardening-only checkpoints

## Validation Gates

### Source and queue

- Tag `153.0.8010.36` resolves to
  `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c` and `chrome/VERSION` agrees.
- The masking patch is the only intentional browser-automation behavior change.
- Any retained Blink repair has current source evidence and a passing focused
  regression test.
- `git range-diff`, the pinned-base diff, and `git diff --check` pass.

### Build and runtime

- A new output directory records `is_official_build=true`, `is_debug=false`,
  `is_component_build=false`, `symbol_level=0`, and
  `dcheck_always_on=false`.
- Chromium reports version `153.0.8010.36`.
- `scripts/smoke.sh` reports `success: true`, CDP reachable through an
  ephemeral developer port, and `navigator.webdriver=false`.

### Artifact

- The candidate is staged under a dedicated candidate root, not the shared
  artifact root.
- Manifest source SHA, upstream revision, patchset SHA, patch queue checksum,
  executable SHA-256, smoke SHA-256, and clean flags match current state.
- `scripts/check-freshness.sh` reports `fresh: true`.
- The shared platform-neutral `../artifacts/chromium-stealthcdp/current` target
  is unchanged.

## Acceptance Criteria

- The build is based exactly on current Linux Stable Chromium
  `153.0.8010.36`, not Chromium `main`, Beta, Dev, Canary, or Early Stable for
  another platform.
- The reviewed masking patch remains enabled and is proven under an active CDP
  developer port.
- Every retained downstream repair passes focused validation.
- The optimized official-style release browser builds and passes repository
  smoke; the retained Blink repair passes its focused regression test.
- A clean, hash-bound candidate is staged without installation or shared-alias
  cutover.

## Definition of Done

This plan is `CLOSED` only when every acceptance criterion has current evidence
recorded here. A source-only refresh or an unfinished build leaves it `OPEN`
with the exact next action or blocker.

## Hard Stops

- Stop on unexpected dirty state in either repository.
- Stop if the official tag resolves to a different commit or version.
- Stop on an unresolved patch conflict or unexplained downstream diff.
- Stop if DCHECKs are absent from the generated build configuration.
- Stop artifact staging if either tracked worktree is dirty.
- Stop before installation, shared-alias cutover, retained-profile use,
  publication, push, or downstream production execution.

## Evidence Log

- 2026-09-12: Plan opened from clean patchset and source identities. Official
  Stable release and Chromium tag evidence selected Linux `153.0.8010.36` at
  `507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c`.
- 2026-09-12: Plan version 2 clarified that the requested production-grade
  runtime uses `is_official_build=true` and does not force DCHECKs. This is a
  production successor to the earlier diagnostic candidate; focused tests
  continue to validate the retained Blink repair.
- Checkpoint `P0002-C01`: plan version `1`; state `ready -> active`; progress
  `outcome_progress`; evidence: clean starting identities, current Stable
  release selection, and explicit masking contract; subagent status
  `not_spawned`; authority `in-envelope`; review disposition summary `none`;
  next action: verify the fetched tag, branch from Stable, and sync dependencies.
- Checkpoint `P0002-C02`: plan version `2`; state `active -> active`; progress
  `outcome_progress`; evidence: exact Stable tag verified, dependencies synced,
  Linux hooks passed, both patches replayed one-to-one at `243db717de` and
  `d417aadf10`, and exported queue committed as `3ecc6b8`; subagent status
  `not_spawned`; authority `in-envelope`; review disposition summary `none`;
  next action: generate the official-style production build and compile.
