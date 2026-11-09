# Plan 0012: Qualify repaired Chromium 157 candidate

State: OPEN

## Current State

User authorized the next build/qualification unit with "ok go" after Plan0011.
Repo source e6f5ec241d2417b1554e427f01719185a641ac1b is clean on
repair/chromium-157-patch-replay. Operator Chromium remains clean at
15a1e89ace187947b2a39881b45f4de992157b56. The repaired source tree was reviewed
at 2dd44af34c06840df3aaebc6cf32ebc691293f43, base
a733b5afbb3ba618844ff8876b89ad1a774b2f18. Browser compilation is running in the bounded unit below.
Initial headroom: 551 GiB disk free, approximately 25 GiB memory available;
compilation requires at least 32 GiB memory and 200 GiB disk free.

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
