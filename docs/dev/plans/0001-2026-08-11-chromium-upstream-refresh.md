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
- The queue now contains the original webdriver patch plus the narrow
  `0002-Fix-stale-shape-result-during-line-overflow.patch` follow-on repair.
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
- The follow-on Blink repair is committed in Chromium source as
  `778b60e96df92414e75d0fb241b108ba1da452db`. A deterministic regression test
  proves the stale-shape invariant fails without the repair (`60 vs. 3`) and
  passes with the shape cleared after the result range is widened. All 42
  `LineBreakerTest.*` cases and the exact committed Chrome build pass.
- Repaired candidate `153.0.8003.0+stealthcdp.02d1c35532eb` is staged under
  the dedicated `linebreaker-778b60e96d` candidate root. Freshness and an
  independent staged-binary smoke pass; the shared platform-neutral `current`
  alias remains on the prior Windows artifact.
- The operator subsequently authorized refreshing the shared agent-browser
  workstation payload and installing the validated Linux Chromium candidate
  into the artifact set agent-browser resolves. The platform-neutral `current`
  alias remains protected because it currently owns a Windows artifact.
- The dedicated candidate is fresh and independently hash-verified, and the
  same Linux artifact is registered as agent-browser's
  `stealthcdp_chromium` executable. Route reconciliation superseded timeout
  `r807103`: a new disposable browser is now operator-visible on Route B and
  renders both the non-Facebook control and Facebook home. That disposable
  profile remained unauthenticated after three live readbacks.
- The operator then authorized one bounded retry through the already
  authenticated retained `last30days-facebook` profile without profile-data
  mutation. Exact access planning, `/proc` identity, and capability preflight
  bound PID 39672 to the installed Chromium 153 artifact. The filtered search
  replaced the former `line_breaker.cc:4102` failure with a new renderer FATAL
  at `inline_item_result.cc:55`: `Length() ==
  shape_result->NumCharacters()` failed `222 vs. 3`. The failed target was
  released while the retained browser survived, and browser acceptance remains
  blocked on this new shaped-text consistency defect.

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

- Do not weaken or replace the pinned upstream line-breaker repair; carry only
  the narrow follow-on stale-shape repair proven necessary by the authenticated
  workload.
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

- Plan version: `6`
- State transition: `active -> blocked_unit`
- Authority classification: standing authority for policy installation,
  documentation, source update, patch replay, build, tests, candidate staging,
  and disposable validation; operator-granted authority for agent-browser
  workstation refresh and validated Linux candidate installation; explicit
  gate remains for retained-profile use, platform-neutral alias cutover, push,
  publication, or downstream production retry
- Unmet criteria: authenticated Facebook browser acceptance without a renderer
  abort
- Ready unit: after explicit authorization, install the exact verified Linux
  candidate into agent-browser's manifest set without changing the
  platform-neutral alias
- Blocked unit: any further authenticated Facebook posts-search comparison
  until the installation, retained-profile, and crash-propagation gates are
  explicitly resolved
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
- All 42 focused `LineBreakerTest.*` tests pass.
- `scripts/smoke.sh` reports `success: true` and
  `navigator.webdriver=false`.

### Artifact gate

- Candidate is staged under a dedicated candidate root.
- The shared `../artifacts/chromium-stealthcdp/current` resolution is unchanged.
- Manifest source SHA, upstream revision, patchset SHA, patch queue checksum,
  executable SHA-256, smoke SHA-256, and clean flags match current state.
- `scripts/check-freshness.sh` reports `fresh: true` and independent checks
  cover manifest fields that helper does not enforce.
- The verified Linux artifact is copied into the shared artifact set and both
  `service.browserBuildManifests.stealthcdp_chromium` and executable ID
  `stealthcdp-chromium-wsl-promoted` resolve it; the platform-neutral `current`
  alias remains unchanged.

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
- The downstream patch queue contains the reviewed webdriver patch and the
  narrow reviewed LineBreaker follow-on repair.
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
- 2026-08-11: Candidate
  `153.0.8003.0+stealthcdp.86aec912997e` was staged at
  `../artifacts/chromium-stealthcdp-candidates/upstream-153-b84d5f5c/current`.
  Freshness reports `fresh=true`; source, upstream, queue, executable, smoke,
  and patch hashes independently match; both dirty flags are false. Shared
  `../artifacts/chromium-stealthcdp/current` remained on the prior Windows
  artifact `150.0.7835.0+stealthcdp.6b6558b55a1d`.
- 2026-08-11: The verified Linux artifact was copied into
  `../artifacts/chromium-stealthcdp/` and the two explicit agent-browser WSL
  bindings were updated. Install doctor then selected Chromium `153.0.8003.0`,
  executable SHA-256 `17ba663c71256ae0f842c7f22236ba7d4c091d0d6da5f4378d28ea967b38045c`,
  with valid manifest and passing webdriver smoke. Agent-browser 0.28.0
  workstation provenance is ready at binary SHA-256
  `5d76d49db1dd70ef87b541eca6dd7e27fdf965d5feea7e3709e911ed22ff2cad`;
  remote control reconverged to `ready`.
- 2026-08-11: Browser launch did not occur. Capability preflight selected the
  Chromium 153 executable, but the disposable custom profile had no registry
  compatibility row. More importantly, authoritative route-pool and explicit
  inline `guacamole-rdp-a` dry runs failed before route assignment with
  `Operation timed out`. Final job `r807103` has `state=failed`,
  `routePoolEntryId=guacamole-rdp-a`, and no display allocation or remote-view
  route. The disposable directory was never launched, retained profiles were
  not touched, and no Facebook renderer result is claimed.
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
- Checkpoint `P0001-C04`: plan version `1`; state `active -> active`;
  progress `outcome_progress`; evidence: dedicated artifact
  `153.0.8003.0+stealthcdp.86aec912997e`, `fresh=true`, executable SHA-256
  `17ba663c71256ae0f842c7f22236ba7d4c091d0d6da5f4378d28ea967b38045c`,
  smoke SHA-256
  `9634a2fd335a207ce81cf003873cb426972544cfd12edfd94401ef8c39668c5f`,
  patch SHA-256
  `a5725ea7da291871232f58a4143ece211d3d3d1359708ad94212cba38f47238e`,
  queue SHA-256
  `86aec912997eb9193045706555e1099c200abc4c95a7807a2388f8214cd9f69c`,
  clean source and patchset identities, unchanged platform-neutral alias, and
  verified agent-browser selection of the installed Linux copy; subagent
  status `not_spawned`; authority `operator-authorized-install`; review
  disposition summary `none`; next action: disposable remote-view preflight.
- Checkpoint `P0001-C05`: plan version `1`; state `active -> blocked_unit`;
  progress `blocked`; evidence: remote-view doctor `ready`, candidate executable
  selected, disposable path isolated, but repeated authoritative route dry
  plans failed before launch; final service job `r807103` timed out with
  `guacamole-rdp-a` requested and no assigned display/route; subagent status
  `not_spawned`; authority `retained-profile-denied`; review disposition
  summary `none`; next action: repair or reconverge agent-browser route
  acquisition, then repeat the no-launch proof and operator-seed the disposable
  profile if authentication is required. Plan remains `OPEN`.
- 2026-08-11: Retained route state was reconciled against the two-entry pool
  emitted by the current remote-view doctor. Reconciliation repaired 277
  orphaned display-allocation readiness records without releasing active Route
  A. The dedicated no-launch preflight then selected released allocation
  `display:shared_display:11` plus available `guacamole-rdp-b`; display access,
  login, permissions, RDP TCP, route URL, and the idle Route B desktop passed.
- 2026-08-11: Disposable runtime profile
  `chromium-153-facebook-acceptance-20260811` launched on Route B with
  `operatorVisible.state=ready`, display `:11`, target
  `CFC705E540668856E1BBF0C385CE3EFA`, and PID `20044`. `/proc/20044/exe`
  resolves to the installed
  `153.0.8003.0+stealthcdp.86aec912997e/chrome-linux/chrome`, whose live
  SHA-256 is
  `17ba663c71256ae0f842c7f22236ba7d4c091d0d6da5f4378d28ea967b38045c`
  and version is Chromium `153.0.8003.0`. The same tab rendered
  `https://example.com/` and `https://www.facebook.com/` with
  `navigator.webdriver === false`. Facebook presented the login form, so no
  authenticated posts search has been claimed. The browser remains open for
  operator seeding at the Route B Guacamole handoff.
- Checkpoint `P0001-C06`: plan version `1`; state `blocked_unit -> active`;
  progress `outcome_progress`; evidence: authoritative route reconciliation,
  deterministic Route B dry run, operator-visible installed Chromium 153
  launch, exact live executable hash and PID, non-Facebook control,
  Facebook home render, and `navigator.webdriver=false`; subagent status
  `not_spawned`; authority `disposable-profile-only`; review disposition
  summary `none`; next action: operator logs into Facebook in the open
  disposable Route B browser, then the primary agent runs the required posts
  search and records renderer/crash evidence. Plan remains `OPEN`.
- 2026-08-11: Two later live readbacks retained PID `20044`, Facebook title and
  URL, target `CFF7BC178ED9787A7C7D884C63B77BB3`, and
  `navigator.webdriver === false`, but accessibility snapshots still exposed
  only `Email or mobile number`, `Password`, and `Log In`. No credentials,
  cookies, retained profile data, or private state were copied or changed.
  The post-login acceptance recipe is the provider's exact filtered workload,
  `https://m.facebook.com/search/posts/?q=OpenAI&filters=eyJyZWNlbnRfcG9zdHM6MCI6IntcIm5hbWVcIjpcInJlY2VudF9wb3N0c1wiLFwiYXJnc1wiOlwiXCJ9In0%3D`,
  followed by bounded renderer, lifecycle, stderr, and process checks; the
  unfiltered `OpenAI` posts route is a comparison only if the filtered route
  does not supply decisive evidence.
- Checkpoint `P0001-C07`: plan version `2`; state `active -> blocked_unit`;
  progress `blocked`; evidence: the installed Chromium 153 browser remains
  healthy and operator-visible on Route B, exact executable/PID and webdriver
  proof remain stable, and the third consecutive goal-turn snapshot still
  shows an unauthenticated Facebook login form; subagent status `not_spawned`;
  authority `disposable-profile-only`; review disposition summary
  `blocking=1` operator-seeded Facebook authentication, `needs_evidence=1`
  authenticated posts-search renderer acceptance, `rejected=2` retained-profile
  copying and credential automation; next action: replace the raw Guacamole
  provider URL with a durable dashboard-backed handoff, then the operator
  signs in, leaves the browser open, and resumes this goal. Plan remains
  `OPEN`.
- 2026-08-11: The operator reported that the raw Guacamole client URL did not
  resolve as an existing connection. Current remote-view doctor and Guacamole
  database evidence nevertheless confirm Route B as connection `2`, display
  `:11`, with retained Chromium PID `20044` healthy. The raw client hash is the
  provider URL and is not an operator handoff. A canonical service handoff was
  minted and resolved with `status=ready`, `resolved=true`, browser ID
  `session:chromium-153-facebook-line-breaker-acceptance`, and durable URL
  `https://agent-browser.ecochran.dyndns.org/remote-view/http-service-request-remote_view_open-4f2ac073-cf6c-40c8-b6ba-c780887882e0`.
- Checkpoint `P0001-C08`: plan version `3`; state
  `blocked_unit -> blocked_unit`; progress `blocker_reduction`; evidence: the
  stale raw provider link was rejected, the exact retained Chromium browser
  and Route B were revalidated without launching a duplicate, and the durable
  dashboard handoff resolves ready to the same browser session; subagent
  status `not_spawned`; authority `disposable-profile-only`; review
  disposition summary `blocking=1` operator-seeded Facebook authentication,
  `needs_evidence=1` authenticated posts-search renderer acceptance,
  `rejected=2` retained-profile copying and credential automation; next action:
  the operator signs in through the durable `/remote-view/` handoff, leaves
  the browser open, and resumes this goal. Plan remains `OPEN`.
- 2026-08-11: One operator-authorized authenticated comparison reused the exact
  retained profile/session `last30days-facebook` with installed Chromium
  `153.0.8003.0+stealthcdp.86aec912997e`. Live PID 39672 resolved to the
  artifact executable with SHA-256
  `17ba663c71256ae0f842c7f22236ba7d4c091d0d6da5f4378d28ea967b38045c`.
  Tab-open job
  `http-service-request-tab_new-c1c60416-7b52-4662-968c-6835af036151`
  reached Facebook title `(20+) OpenAI - Search Results | Facebook` at target
  `5F9E42559ACE9321F29CFF6081924676`; exact-target probe job
  `http-service-request-probe-530f5410-6761-4c18-b30e-556fbc704e30` then timed
  out after 20 seconds.
- 2026-08-11: Retained stderr
  `/home/ecochran76/.agent-browser/tmp/chrome-launches/chrome-39672-1786492827405.stderr.log`
  records the corresponding local `20:46:12` FATAL at
  `third_party/blink/renderer/core/layout/inline/inline_item_result.cc:55`:
  `DCHECK failed: Length() == shape_result->NumCharacters() (222 vs. 3)`.
  The stack reaches `InlineItemResult::CheckConsistency()` from
  `LineBreaker::HandleOverflow()` after `BreakText()`. The former
  `line_breaker.cc:4102` assertion is absent from this Chromium 153 source, so
  CL 7992797 repaired the old ordering invariant but not this next shape-result
  consistency failure.
- 2026-08-11: Agent-browser emitted only the probe timeout, not an immediate
  target-crash lifecycle event. Cleanup job
  `http-service-request-tab_handle_release-3df5f37a-af22-4d2a-b033-590c1c731727`
  closed only the failed target and preserved PID 39672, its retained profile,
  session route, and unrelated tabs. No profile data, provider, tick, cache, or
  shared alias was mutated.
- Checkpoint `P0001-C09`: plan version `4`; state
  `blocked_unit -> failed_acceptance`; progress `blocker_reduction`; evidence:
  authenticated retained-profile routing and installed Chromium identity are
  proven, the old ordering DCHECK is absent, and a new reproducible
  `InlineItemResult` mismatch is bound to exact process, target, jobs, and
  stderr; subagent status `not_spawned`; authority
  `operator-authorized-retained-profile-retry-without-profile-mutation`; review
  disposition summary `blocking=2` shaped-text consistency crash and missing
  target-crash propagation, `needs_evidence=1` authenticated search acceptance,
  `rejected=2` disabling DCHECKs and running another live retry before repair;
  next action: repair the new invariant with DCHECKs retained, rebuild, and
  separately repair agent-browser crash propagation before requesting another
  authenticated acceptance attempt. Plan remains `OPEN`.
- 2026-08-14: A DCHECK-only test seam now deterministically seeds a reused
  three-character `ShapeResultView` immediately before the overflow result is
  widened. With the production clear removed, the focused test crashes at
  `inline_item_result.cc:55` with `Length() ==
  shape_result->NumCharacters()` failed `(60 vs. 3)`; restoring
  `item_result->shape_result = nullptr` makes the same test pass without
  weakening the invariant.
- 2026-08-14: Chromium source commit
  `778b60e96df92414e75d0fb241b108ba1da452db` is clean and formatted. All 42
  `LineBreakerTest.*` cases pass from the exact committed tree, and the
  DCHECK-enabled `chrome` target completed with final `LINK ./chrome`. Builds
  used vendored Ninja with at most six jobs; the exact-tree Blink rebuild
  retained more than 35 GiB available memory and did not consume additional
  swap.
- Checkpoint `P0001-C10`: plan version `5`; state
  `failed_acceptance -> active`; progress `outcome_progress`; evidence:
  deterministic red/green invariant reproduction, source commit
  `778b60e96df92414e75d0fb241b108ba1da452db`, 42/42 focused tests, clean
  DCHECK Chrome link, and bounded WSL resource observations; subagent status
  `not_spawned` for the serialized critical path; authority `in-envelope`;
  review disposition summary `none`; next action: commit the two-patch queue
  and checkpoint, then smoke, stage, and hash-verify a dedicated repaired
  candidate without changing the shared platform-neutral alias. Plan remains
  `OPEN`.
- 2026-08-14: The two-patch queue was committed as
  `9f8084c151aab38c62b72d0830ebec0a27562796`; stable patch IDs match source
  commits `6e2a5bb35b050375e5748deb72479cf851950064` and
  `778b60e96df92414e75d0fb241b108ba1da452db`. Local smoke passed with
  `navigator.webdriver=false` and executable SHA-256
  `75aad493dc70e9f2529985e842bedf5b34a325fbf455fb6670c1b8abecbaf3de`.
- 2026-08-14: Repaired candidate
  `153.0.8003.0+stealthcdp.02d1c35532eb` was staged at
  `../artifacts/chromium-stealthcdp-candidates/linebreaker-778b60e96d/current`.
  Its manifest binds source `778b60e96df92414e75d0fb241b108ba1da452db`,
  patchset `9f8084c151aab38c62b72d0830ebec0a27562796`, queue SHA-256
  `02d1c35532eba8d4eaf18a043b8db1a8a8f47b0374c830378444263bda37fd84`,
  executable SHA-256
  `75aad493dc70e9f2529985e842bedf5b34a325fbf455fb6670c1b8abecbaf3de`,
  and smoke SHA-256
  `70a1e2b2be72dbc406b78a3980430e068e9928ae54f7f739bc073873ff1e48a6`;
  both dirty flags are false. Independent staged-binary verification passed.
- 2026-08-14: Adding a second patch exposed a deterministic freshness-helper
  bug: promotion hashes checksum rows by filename, while the checker sorted
  rows by hash. `scripts/check-freshness.sh` now normalizes and sorts entries
  by patch filename; the repaired candidate reports `fresh=true`. The shared
  platform-neutral alias still resolves to Windows artifact
  `150.0.7835.0+stealthcdp.6b6558b55a1d`.
- Checkpoint `P0001-C11`: plan version `6`; state
  `active -> blocked_unit`; progress `outcome_progress`; evidence: exact
  two-patch reproduction, passing local and staged webdriver smoke, complete
  manifest/hash readback, `fresh=true`, and unchanged shared alias; subagent
  status `not_spawned` for the serialized critical path; authority
  `in-envelope-candidate-staging`; review disposition summary `blocking=1`
  explicit agent-browser installation and retained-profile acceptance gate;
  next action: obtain authorization to install the exact verified Linux
  candidate without alias cutover, then resolve crash propagation before one
  bounded authenticated acceptance retry. Plan remains `OPEN`.
