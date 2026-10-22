# Plan 0003: Stable 156 with private CDP behavior

State: OPEN

## Objective

Refresh to current Linux Stable 156.0.8078.47, retaining the private
`navigator.webdriver=false` patch, and build normal Chromium with
`is_chrome_for_testing=false` explicitly recorded.

Release source: https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_02018666648.html

## Current State

Starting patch repository: clean main at b1f77a64e2bd4a2924abd948c39015ddc0d75209.
Starting source: clean ec/chromium-stealthcdp-stable-153.0.8010.36 at
d417aadf10fc848a686badd2b074649cb1da971c. Pin is
507c6ee3e2f3b2ca0e660547e5b9ea4820c67f4c. Stable tag fetch is in progress.
Stable tag and VERSION verified at 1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775.
Source branch ec/chromium-stealthcdp-stable-156.0.8078.47 carries an equivalent
two-patch replay: range-diff reports equality for both patches; base diff is
67 insertions and 6 deletions across four files; diff --check passes.
Dependency sync and hooks passed; build, tests, smoke and candidate acceptance
remain open.
The previous production output does not explicitly set testing flavor; its
current source default is false. The reported runtime designation remains
identified in Agent Browser at ~/.agent-browser/browsers/chrome-156.0.8078.47/chrome:
the disposable baseline smoke identifies Google Chrome for Testing and reports
navigator.webdriver=true, CDP reachable, success=false. Receipt:
/tmp/chromium-stealthcdp-managed-156-baseline.json. Operator confirmation of the
intended replacement target remains pending.

## Scope and Execution

Primary owns serialized tag verification -> new source branch -> dependency
sync -> patch reconciliation -> binary export/range-diff -> new release output
-> focused Blink tests and CDP smoke -> dedicated candidate staging.
Use a fresh output, official release configuration, and explicitly disable CfT.
Keep the Blink repair only when still required; preserve earlier branches,
outputs, artifacts and retained profiles. Do not publish private patches.
No shared alias cutover, installation or retained profile operation is included
in candidate preparation. Resolve the active executable before replacement.

## Acceptance and Definition of Done

- Official Stable tag SHA and chrome/VERSION agree.
- Reviewed replay, range-diff, base diff and diff --check pass.
- Release build records is_official_build=true, is_debug=false,
  is_component_build=false, symbol_level=0 and is_chrome_for_testing=false.
- Every retained repair passes focused upstream tests.
- Smoke succeeds with active CDP and navigator.webdriver=false.
- Candidate manifest, hashes and freshness match source and patch identities.
- Actual runtime replacement scope is resolved and outcome reported accurately.

## Governance

Version 3; active V8 profile repair/build packet; primary owns both worktrees.
Two attempts per unit, one drift review and one remediation pass. Checkpoint
after source replay, build, and validation; bound stalled network units to ten
minutes before recording a blocker. No delegation during coupled source work
(`not_spawned`: overlapping checkout and provenance); independent final review
will follow candidate validation. Stop on unexpected dirty state, unexplained
delta, unresolved replay conflicts or failed acceptance. No graph initialization.
Graph memory disposition: forbidden for repo graph writes because no reviewed
repo group is defined; maintain continuity here.

## Execution Evidence

- Source replay checkpoint 14ba094: source HEAD
  15a1e89ace187947b2a39881b45f4de992157b56; both patches equal in range-diff.
- Dependency sync and Linux hooks completed successfully using the separate
  ../.gclient.stable156-linux config. Original Windows config is unchanged.
  The optional instrumented_libs checkout was fetched and aligned to its exact
  gitlink 51898bc68243bf1f096b49420f96312df48c363f; tracked source is clean.
- GN generation passed (36,329 targets). Matching Stable PGO profile downloaded;
  output out/Stable156ProductionStealthCDP records all requested release flags
  and both is_chrome_for_testing=false and is_chrome_for_testing_branded=false.
- Chrome compilation started with eight concurrent jobs, bounded for available
  memory. Log /tmp/chromium-stable156-build.log. Build and tests remain pending.
- Independent drift review /root/review_stable156 completed with no material
  findings. Primary accepted the review, having independently checked tag,
  VERSION, range-diff and diff --check. Reviewer correctly leaves runtime
  replacement and future build/test acceptance unresolved.
- Durable baseline smoke retained at
  ../artifacts/chromium-stealthcdp-candidates/stable-156-production-1d17a2e2/evidence/managed-browser-baseline.json.
- Version 2 replanning: both allowed Siso attempts failed on fresh generated
  output timestamps roughly nine seconds ahead of Siso's clock; no compiler
  failure was reported. Preserve evidence/build-attempt-1.log and
  evidence/build-attempt-2.log under the same candidate root. A direct Python
  realtime/file-mtime probe agrees to within a millisecond; host clock changes
  are outside this packet. Depot_tools explicitly supports use_siso=false.
  GN generated a separate out/Stable156ProductionStealthCDPNinja directory
  with identical release/branding flags plus use_siso=false. Native Ninja
  1.12.1 compilation is running at eight jobs, log
  /tmp/chromium-stable156-build-ninja.log. This is a distinct build-runner repair
  packet, bounded to two attempts; no shared outputs were cleaned or altered.
- With improved host capacity (38 GiB available; load ~20 on 28 CPUs), the
  initial eight-job Ninja run was intentionally interrupted and resumed at
  twelve jobs without clearing outputs. The subsequent run stopped at V8
  mksnapshot: stale builtins profile rejected for RecordWriteSaveFP. The browser
  PGO profile and V8 builtins profile are distinct. Version 3 repairs this
  verified blocker by executing Chromium's exact V8 profile hook with
  --check-v8-revision; it downloaded version 15.6.75.19 successfully, checked
  against V8 392e44423f46d75904da712fadea4c7d5d97967f. No optimization or profile
  consistency check was disabled. Failure evidence is retained at
  evidence/build-ninja-v8-profile-failure.log. Incremental twelve-job build
  retried in the same output, log /tmp/chromium-stable156-build-profile-retry.log.
- Chrome build completed successfully (38,057 steps in the final retry).
  Executable reports Chromium 156.0.8078.47 without a testing designation.
  Durable evidence/smoke-stable156.json reports success=true, active ephemeral
  CDP and navigator.webdriver=false. The V8 snapshot profile check passed.
  Focused blink_unittests build is running in the same output; log
  /tmp/chromium-stable156-blink-build.log. Candidate staging and installed
  runtime replacement remain pending.
