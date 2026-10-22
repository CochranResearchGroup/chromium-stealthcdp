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
All source, dependency, build, smoke and candidate acceptance gates remain open.
The previous production output does not explicitly set testing flavor; its
current source default is false. The reported runtime designation remains
unattributed until the actual executable is identified.

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

Version 1; active source preparation packet; primary owns both worktrees.
Two attempts per unit, one drift review and one remediation pass. Checkpoint
after source replay, build, and validation; bound stalled network units to ten
minutes before recording a blocker. No delegation during coupled source work
(`not_spawned`: overlapping checkout and provenance); independent final review
will follow candidate validation. Stop on unexpected dirty state, unexplained
delta, unresolved replay conflicts or failed acceptance. No graph initialization.
Graph memory disposition: forbidden for repo graph writes because no reviewed
repo group is defined; maintain continuity here.
