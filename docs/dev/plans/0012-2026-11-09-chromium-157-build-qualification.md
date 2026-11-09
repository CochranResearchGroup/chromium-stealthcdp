# Plan 0012: Qualify repaired Chromium 157 candidate

State: CLOSED

## Current State

The repaired Chromium 157.0.8103.38 candidate is compiled and qualified with
DCHECKs forced on. All 43 LineBreaker tests, including the retained regression,
and CDP smoke passed. Primary final verification and independent closed-world
review passed. Source and existing browser selections remain clean/unchanged.
Approved-queue integration, publication, installation and updater requeue remain
separate gates. User's "ok go" authorized this build/qualification packet.

## Scope and acceptance

Prepare separate full worktree and synchronize Linux dependencies at exact
pinned base; apply reviewed queue; verify tree matches reviewed repair. Build
new out/Qualification-157-DCHECK with dcheck_always_on=true. Run all
LineBreakerTest.* including BreakWordWithReusedShapeResult, require no skipped
or failed tests, then scripts/smoke.sh with success=true and webdriver=false.
Bind artifacts/evidence to source, patch queue, GN args and executable hashes.
Primary owns preparation/build; read-only /root/build_preflight checks execution
prerequisites off critical path. After execution use independent evidence review.

Non-goals: publication, push, installed controller adoption/requeue, profile
mutation, installation, consumer activation, shared alias changes or hosted CI.
No existing failed automation checkout/output is modified.

## Execution and bounds

Owned root: ~/.local/state/chromium-stealthcdp/qualification-157/.
Serial: headroom -> isolated full source -> gclient sync/hooks/PGO -> reviewed
queue replay/tree check -> headroom -> fresh build -> tests -> smoke -> receipt
review. Preparation may proceed with low memory; compilation must defer below
the documented 32 GiB headroom threshold. All execution cgroup-limited to 8 CPU
equivalents, 32 GiB memory, zero swap, 12 hours; compilation uses 8 jobs and
continuous 200 GiB disk reserve checks. Two work-unit attempts maximum, one
review/rework cycle; no blind repeat of deterministic failure. Checkpoint after
preparation, build and acceptance. Stop precisely at resource/technical gate;
no automatic live retries. Source review is inherited from Plan0011; final
review is closed-world verification of this qualification evidence.

## Execution receipt

Started cgroup unit `chromium-stealthcdp-qualify-157.service`, invocation
`6319e122fed94b57af824ae8a6941e3b`. Verified CPU quota 800%, memory 34359738368
bytes, swap 0 and runtime 12h. Private runner/logs/receipts are under the owned
root; `execution-metadata.json` binds the runner hash and invocation.

Delegation: `/root/build_preflight` independently reviewed build prerequisites
and live runner limits. Confirmed explicit GN args must override the normal
controller's dcheck_always_on=false and that direct autoninja -j8 is required.
One accepted finding: runner's final receipt alone does not recheck tracked
source cleanliness after the long build. Primary closes this gap with mandatory
post-run source status and identity/hash verification in a separate primary
acceptance receipt; runner qualification.json is provisional. Running code is
not silently changed by editing its source file.

## Preparation checkpoint

`outcome_progress`: full worktree/dependencies/hooks and both optimization
profile checks passed. Both patches replayed and the complete source tree
matches reviewed repair 2dd44af. New source HEAD
`997304ee0ffc57e87df6945393084efcfa287f51`, tree
`88a40531127b9e286ccb92669229aee2fe06d0b9`.
GN generation passed and compilation of chrome+blink_unittests started with
8 jobs. Start headroom 34457042944 memory bytes and 538307497984 disk bytes
passed the 32-GiB/200-GiB gate. GN args SHA256
`07cf9ef14782cfc17090b813f3a8d2a383a838a7cb2301ec945fb467f7e21bb6`;
queue SHA256
`587a95d8d49a76446e1686f54e427e37c1d6cbe73c5db33c0d054ab1deffa9ee`.
Driver receipt is `qualification.json`; current build log ends in
`016-autoninja.log` under evidence. Existing checkouts and activation remain
untouched. Browser acceptance is still unmet until build, tests, smoke and
primary final identity/cleanliness checks pass.

## Qualification result

`outcome_progress`: preparation -> building -> qualified -> primary accepted.
One execution attempt completed in 27264.71 seconds (7.57 hours) within 12h.
All 61298 Ninja actions completed. GN args use dcheck_always_on=true and
dcheck_is_configurable=false; `evidence/dcheck-defines.json` independently
confirms Blink core's DCHECK_ALWAYS_ON=1. Normal automation defaults to DCHECKs
off; this candidate intentionally differs for invariant-sensitive validation.
No hosted CI ran. Local workstation/toolchain evidence satisfies validation;
no hosted image parity is claimed.

Exact executed commands, after sync/hooks and browser/V8 PGO validation:

```sh
gn gen out/Qualification-157-DCHECK
autoninja -C out/Qualification-157-DCHECK -j 8 chrome blink_unittests
out/Qualification-157-DCHECK/chrome --version
out/Qualification-157-DCHECK/blink_unittests --gtest_filter=LineBreakerTest.* --test-launcher-jobs=1 --gtest_output=xml:/home/ecochran76/.local/state/chromium-stealthcdp/qualification-157/evidence/line-breaker.xml --no-sandbox
scripts/smoke.sh --chrome /home/ecochran76/.local/state/chromium-stealthcdp/qualification-157/checkout/src/out/Qualification-157-DCHECK/chrome --output /home/ecochran76/.local/state/chromium-stealthcdp/qualification-157/evidence/smoke.json
```

Build cwd is the isolated full source, not the retained operator checkout.
Smoke script is invoked from this repo. Results: exact version
`Chromium 157.0.8103.38`; 43 tests passed, none failed/skipped, including
`LineBreakerTest.BreakWordWithReusedShapeResult`; smoke success=true and
checks.navigatorWebdriver="false". Source tree matches the reviewed repair.

Chrome SHA256:
`bd5efff69d413e45d765a6c0e720c93061943e0215d2dbd04384f96c1ae382f7`.
Test executable SHA256:
`187659f72d79da48b6b0463366897a32e5bc5d2a2fdc1e1bf03fbe2342bb8384`.
`qualification.json` SHA256:
`fbc14c8704562ba92f72d01dc21d25da714288ac225ec638afed503cdec03d59`.

Primary `primary-acceptance.json` records 20 passing checks, including post-run
tracked cleanliness, HEAD/tree, GN/queue/binary hashes, generated DCHECK define,
V8 revision, unchanged functional repo inputs, XML results and smoke identity.
This explicitly closes F1. Fresh resource readback records MainPID 0/inactive;
`post-run-resources.json` independently proves the owned cgroup path is absent.
Service journal records 17.8G memory peak and 0B swap peak; kernel limits remained
800% CPU/32GiB/zero swap/12h. Evidence journal is retained locally.

Independent evaluator `/root/qualification_review` performed closed-world
verification of frozen qualification criteria and F1. It independently checked
source cleanliness/tree, all requested hashes, generated DCHECK define, 43 test
results/named regression and smoke. No blocking findings; primary accepts its
evidence and independently performed the 20 acceptance checks. No further source
review-discovery pass or remediation cycle was opened.

The operator source remains 15a1e89a and failed automation source 16fc7584 with
its failed am state intact. Shared artifact selection remains
`156.0.8078.47+stealthcdp.4b864442a8fd`; installed selection remains
`156.0.8078.73+stealthcdp.0279989f6f07`. No release, push, install, profile
mutation, consumer cutover or updater requeue occurred.

## Review artifact and next gate

Dedicated staging root:
`../artifacts/chromium-stealthcdp-candidates/chromium-157-repair/`.
Candidate identity:
`157.0.8103.38+stealthcdp.587a95d8d49a`.
The generated manifest and local staging receipt are the authority for the copy
and its selected binary hash. Staging uses only this dedicated root; it does
not repoint the shared alias. Private receipts remain under the owned execution
root, including subsequent `staging.json` and staged smoke evidence.

The build/qualification packet is complete. Next gate: approve/integrate the
reviewed queue through the repository's controlled path, then explicitly
requeue/adopt through the bounded updater lane. Installed controller and
approved-source snapshot have not been changed by this packet.

## Memory disposition

`forbidden`: repo-specific Graphiti group is undefined and repo instructions
keep source-backed continuity in docs while avoiding speculative memory writes.
No authority exists to place this project outcome in another cloud. No write
was attempted. Non-write receipt:
`~/.graphiti-openclaw/state/closeout-memory/20261109T190602Z-remember.json`.
