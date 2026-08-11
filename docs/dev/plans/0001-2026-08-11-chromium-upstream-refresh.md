# Plan 0001: Chromium upstream refresh and Facebook line-breaker acceptance

State: OPEN

Date: 2026-08-11

## Objective

Advance the Linux `chromium-stealthcdp` candidate to a freshly pinned Chromium
`main` revision, replay and review the downstream patch queue, prove that the
upstream Blink `LineBreaker` repair is present and effective with DCHECKs
enabled, stage a reproducible candidate outside the shared artifact alias, and
validate the authenticated Facebook posts-search workload in an authorized
disposable browser lane.

## Current State

- The patchset repository began clean at
  `4ef41f136c27346e811e22abbf01b327a82ffcac`, one commit ahead of
  `upstream/main` because the diagnostic handoff is local.
- Chromium source began clean on `ec/chromium-stealthcdp` at
  `24ecda02e97db6fa730a7ccf8747776a4d21e4b9`, based on
  `d421c3af8268e2e6227b7fe4461183e69b64bc61`.
- The queue contains only `0001-Make-navigator.webdriver-non-advertising.patch`.
- At execution time, Chromium `main` was re-resolved and frozen at
  `b84d5f5c55a43d2f7778cfbc1996d3b835296d1c`, version `153.0.8003.0`.
- Chromium source is now on `ec/chromium-stealthcdp-b84d5f5c`; dependencies
  are synchronized and Linux hooks passed. The replayed downstream commit is
  `6e2a5bb35b050375e5748deb72479cf851950064`.
- Upstream commit `de949449a7fc4df4551492407a65fc3d63015c42`, Chromium
  CL 7992797, removes the invalid `BreakText` ordering DCHECK, preserves the
  restore path, and adds
  `external/wpt/css/css-text/crashtests/line-breaker-overflow-crash.html`.
- The DCHECK-enabled Chromium 153 candidate, focused LineBreaker suite, exact
  upstream crash WPT, and repository smoke now pass. The retained Facebook
  profile remains outside this plan's mutation authority.
- The operator subsequently authorized refreshing the shared agent-browser
  workstation payload and installing the validated Linux Chromium candidate
  into the artifact set agent-browser resolves. The platform-neutral `current`
  alias remains protected because it currently owns a Windows artifact.

## Scope

1. Install and wire the selected repo policy bundle.
2. Freeze the execution-time Chromium upstream SHA and preserve starting
   identities.
3. Create a dedicated source update branch and synchronize Chromium
   dependencies without destructive cleanup.
4. Prove the pinned base contains CL 7992797 behavior and its regression test.
5. Replay and range-review only the `navigator.webdriver` downstream patch.
6. Refresh `upstream-revision.txt`, the one-patch queue, and compatibility
   documentation.
7. Build a fresh Linux candidate with `dcheck_always_on=true`.
8. Run the upstream WPT, focused line-breaker tests, and the repository smoke.
9. Stage and hash-verify the candidate outside the shared `current` alias.
10. Install the verified Linux artifact into agent-browser's shared artifact
    set without repointing the platform-neutral alias.
11. Run an access-plan-first authenticated Facebook comparison using the
    installed candidate and an authorized disposable profile.

## Non-Goals

- Do not add a custom line-breaker patch when the pinned upstream already
  contains the accepted Chromium repair.
- Do not broaden the stealth patch into canvas, WebGL, audio, font, locale,
  timezone, device, or other fingerprint spoofing.
- Do not disable DCHECKs globally.
- Do not mutate the retained Facebook profile.
- Do not repoint the shared platform-neutral artifact alias or retry the
  downstream Facebook tick. The operator's later install authorization covers
  only the validated Linux candidate and agent-browser workstation payload.
- Do not repair agent-browser crash propagation or profile-routing defects in
  this Chromium repository.

## Critical Path

The primary agent owns the serialized path:

1. policy and durable plan;
2. frozen upstream and synchronized checkout;
3. source proof and patch replay review;
4. patchset refresh and clean commits;
5. build and source-level validation;
6. candidate staging and provenance verification;
7. disposable authenticated browser acceptance;
8. completion audit and plan closeout.

No parallel agents are required for this maintenance-sized repository.

## Execution Governance

- Plan version: `1`
- State transition: `ready -> active`
- Authority classification: standing authority for policy installation,
  documentation, source update, patch replay, build, tests, candidate staging,
  and disposable validation; operator-granted authority for agent-browser
  workstation refresh and validated Linux candidate installation; explicit
  gate remains for retained-profile use, platform-neutral alias cutover, push,
  publication, or downstream production retry
- Unmet criteria: all source, build, artifact, and browser acceptance gates
- Ready unit: freeze upstream and update the source checkout after policy audit
- Blocked unit: authenticated Facebook comparison until a disposable profile
  is available and operator-seeded
- Delegation: `not_spawned`; the source pin, dependency sync, patch replay,
  queue export, and build provenance are one coupled critical path. An
  independent evaluator may be used once for the final drift-discovery review.
- Review discovery budget: one broad pass, followed only by closed-world
  verification of accepted blocking findings
- Checkpoint cadence: after each validated execution packet
- Retry bounds: two attempts per work unit, one review/rework cycle, and at
  most two consecutive hardening-only checkpoints

## Execution Packets

### Packet A: policy and planning

- Owner: primary agent
- Write surface: `.codex/`, `AGENTS.md`, `docs/dev/policies/`,
  `docs/dev/plans/`, and `docs/dev/notes/`
- Evidence: selector install record, selected profile/module set, normal and
  active-only planning audits
- Terminal condition: installed policy is wired and this plan passes audit

### Packet B: upstream and patch replay

- Owner: primary agent
- Write surface: `../src`, `upstream-revision.txt`, `patches/`, and patch
  boundary documentation
- Evidence: frozen SHA/version, source proof for CL 7992797, `git range-diff`,
  constrained downstream diff, clean worktrees
- Terminal condition: exactly one reviewed downstream patch remains

### Packet C: build, tests, and artifact

- Owner: primary agent
- Write surface: new `../src/out/<candidate>` output, temporary smoke receipt,
  and dedicated candidate artifact root
- Evidence: GN args, `DCHECK_ALWAYS_ON=1`, WPT and unit results, smoke JSON,
  manifest and SHA-256 verification, unchanged shared alias
- Terminal condition: a clean, fresh, reproducible candidate is staged and its
  verified Linux artifact is available to agent-browser without changing the
  platform-neutral alias

### Packet D: browser acceptance

- Owner: primary agent with operator-seeded authentication when required
- Write surface: disposable browser profile and incident evidence only
- Evidence: requested and detected profile, executable, PID, CDP endpoint,
  target ID, stderr path, Facebook home/search result, non-Facebook control,
  and `navigator.webdriver === false`
- Terminal condition: the authenticated search renders without the old DCHECK,
  or the plan remains OPEN with exact blocking evidence

## Validation Gates

### Source and patch gate

- Frozen upstream version and SHA are recorded.
- The old DCHECK is absent from the pinned source.
- The upstream recovery comment, restoration logic, and crash WPT are present.
- Patch replay is reviewed against the former downstream commit with
  `git range-diff`.
- The only downstream source change is the intended `Navigator::webdriver()`
  behavior.
- `git diff --check` passes and both repos are clean at build time.

### Build and test gate

- A new output directory records `is_debug=false` and
  `dcheck_always_on=true`.
- Generated toolchain content contains `-DDCHECK_ALWAYS_ON=1`.
- The exact upstream line-breaker crash WPT passes without a masking
  expectation.
- All 41 focused `LineBreakerTest.*` tests pass.
- `scripts/smoke.sh` reports `success: true` and
  `navigator.webdriver=false`.

### Artifact gate

- Candidate is staged under a dedicated candidate root.
- The shared `../artifacts/chromium-stealthcdp/current` resolution is unchanged.
- Manifest source SHA, upstream revision, patchset SHA, patch queue checksum,
  executable SHA-256, smoke SHA-256, and clean flags match current state.
- `scripts/check-freshness.sh` reports `fresh: true` and independent checks
  cover manifest fields that helper does not enforce.

### Browser acceptance gate

- Agent-browser preflight selects the explicit candidate and the requested
  disposable profile without identity mismatch.
- Facebook home and a non-Facebook control render.
- The authenticated Facebook posts-search workload reaches renderer content
  without the old `line_breaker.cc` abort.
- Candidate still reports `navigator.webdriver === false`.
- Command, caller labels, requested/detected profile, executable, PID,
  endpoint, target ID, and stderr path are retained.
- Any new renderer crash is reported honestly; Chromium acceptance is not
  inferred from source tests alone.

## Acceptance Criteria

- Policy bundle `v0.1.15` is installed, wired, and audited.
- A current Chromium `main` revision is pinned reproducibly.
- CL 7992797 behavior and its WPT are present in that pinned base.
- The downstream patch queue contains exactly one reviewed webdriver patch.
- DCHECK-enabled focused tests and repository smoke pass.
- A clean candidate artifact passes manifest and freshness verification outside
  the shared alias.
- An authorized disposable authenticated Facebook comparison passes all
  browser acceptance checks.
- No retained profile mutation, implicit runtime cutover, shared alias change,
  or downstream tick retry occurred.

## Definition of Done

This plan is `CLOSED` only after every acceptance criterion has current,
source-backed evidence recorded in this document or a linked durable closeout.
If disposable authenticated state is unavailable, the plan remains `OPEN` and
the staged candidate is reported as source-validated but not Facebook-accepted.

## Hard Stops

- Stop on unexpected source or patchset changes.
- Stop on patch replay beyond the intended webdriver surface.
- Stop if the pinned base lacks the upstream line-breaker repair or WPT.
- Stop if DCHECKs are not present in the candidate toolchain.
- Stop artifact staging if either worktree is dirty.
- Stop browser acceptance on profile mismatch, missing authorization, or a
  candidate executable mismatch.
- Stop before any shared alias or live-runtime cutover.

## Evidence Log

- 2026-08-11: Plan opened after selector-driven policy installation.
- 2026-08-11: Upstream repair identified as CL 7992797 / commit
  `de949449a7fc4df4551492407a65fc3d63015c42` with an upstream crash WPT.
- 2026-08-11: The no-launch browser access plan did not honor the unknown
  disposable runtime-profile hint. It selected durable profile
  `stealthcdp-default`, the registered Chromium 150 executable, and an active
  `odollo-carrier-usps` profile lease. That route was rejected. Browser
  acceptance must instead bind the staged executable explicitly to a custom
  temporary user-data directory and retain detected-profile proof.
- 2026-08-11: The operator authorized the agent-browser binary/install path.
  `agent-browser install workstation --apply --json` refreshed the versioned
  workstation payload; follow-up evidence reports payload `state=installed`,
  binary provenance match `true`, dashboard runtime `ready`, convergence
  `converged`, and remote control `ready`. Existing duplicate-profile pressure
  remains explicitly non-blocking and will not be mutated by this plan.
- 2026-08-11: A candidate-specific no-launch plan selected custom disposable
  profile `/tmp/chromium-stealthcdp-facebook-disposable.rVSvSp` and free route
  `guacamole-rdp-a`, but its service launch command did not carry the explicit
  build-output executable. No browser was launched. Browser acceptance is
  deferred until the verified Linux artifact is installed into the manifest
  set agent-browser resolves.
- Checkpoint `P0001-C01`: plan version `1`; state `ready -> active`;
  progress `outcome_progress`; evidence: selector bundle `v0.1.15`, 18 adopted
  modules, wired `AGENTS.md`, and passing normal/active planning audits;
  subagent status `not_spawned` for coupled critical path; authority
  `in-envelope`; review disposition summary `none`; next action: goal-only
  policy audit, then freeze upstream.
- Checkpoint `P0001-C02`: plan version `1`; state `active -> active`;
  progress `outcome_progress`; evidence: execution-time upstream
  `b84d5f5c55a43d2f7778cfbc1996d3b835296d1c` / `153.0.8003.0`, clean
  synchronized checkout after Linux hooks, CL 7992797 recovery logic and WPT
  present, old fatal DCHECK absent, replay commit
  `6e2a5bb35b050375e5748deb72479cf851950064`, exact one-to-one `git range-diff`,
  and only `navigator.cc` changed downstream; subagent status `not_spawned` for
  the coupled critical path; authority `in-envelope`; review disposition
  summary `none`; next action: export and commit the one-patch queue, then
  build from clean identities.
- Checkpoint `P0001-C03`: plan version `1`; state `active -> active`;
  progress `outcome_progress`; evidence: clean Chromium 153 build with
  `dcheck_always_on=true` and `-DDCHECK_ALWAYS_ON=1`; Chrome build 56,867 steps
  in 3h14m34s; test build 10,947 steps in 1h34m29s with zero retries; all 41
  `LineBreakerTest.*` cases passed; upstream
  `line-breaker-overflow-crash.html` ran 1/1 as expected with exit 0 and no
  masking expectation; repository smoke reports `success=true` and
  `navigator.webdriver=false`; executable SHA-256
  `17ba663c71256ae0f842c7f22236ba7d4c091d0d6da5f4378d28ea967b38045c`;
  WPT harness adaptation: current upstream requires `headless_shell` and
  `chromedriver`, and a reversible local port remap avoided occupied Docker
  ports 8081/8444 before the source template was restored clean; subagent
  status `not_spawned`; authority `in-envelope`; review disposition summary
  `none`; next action: commit this checkpoint, stage and verify the dedicated
  artifact, then install the Linux artifact for disposable browser acceptance.
