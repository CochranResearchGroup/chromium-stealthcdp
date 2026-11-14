# Plan 0014: Controlled integration and updater retry preparation

State: CLOSED

## Current State

Operator authorized preparation with "ok go" after Ask Matt recommended preparing
exact integration/retry action for approval. Qualified source queue and helpers
are e2d53b5bd10f7ce71487620134e9827ab462c07f. This packet prepares a concrete
local merge and review body; public push/PR/merge, installed controller adoption
and updater effects require final approval of this concrete packet.

Remote main refreshed to 10580990a1629e674a170652e3a5d7f15c359bb6. Its 9 commits
contain routine 156 release history. Local branch carried 10 reviewed commits,
including already-installed retention changes. Integration branch
integration/chromium-157-repair preserves both histories. Three conflicts were
limited to exported patches and upstream-revision.txt; resolved to exact
qualified e2d53b5 queue/base. Scripts/tests/queue/base are byte-identical to
e2d53b5; remote release receipts are retained. No force/reset/discard operation.

## Scope, validation and bounds

Primary owns one local integration packet. Serial: current remote/runtime read
-> semantic merge -> exact input comparison -> replay/full local suite -> local
merge commit and review body -> explicit effect approval. Two repair attempts,
one review/remediation pass maximum. No delegation: all current operations are
serialized identity reconciliation, and source/qualification already have
independent review. No repeated broad review discovery.

Acceptance: preserve remote release history and qualified source/helper bytes;
replay pinned 157.0.8103.38 and current official 157.0.8103.50; full 83 local tests;
clean committed integration branch; exact retry gates documented.
No publication, release, push, profile or browser selection effects in preparation.

## Current target and runtime gates

Official Stable discovery now returns 157.0.8103.50 at
049750111b1e5c11565c792b2aeed5541f332bad. Exact tag fetch matches discovery.
The qualified artifact remains 157.0.8103.38. Both revisions pass the actual
isolated git-am checker with the repaired queue. Replay is not compiled .50
acceptance; a standard updater invocation will freshly qualify .50.

Installed controller remains 804590e9dde97ebba99d95ee5dff4a3a41fcbc40, inactive
MainPID 0. No deployment-stopped or deployment-halted marker exists. Baseline is
156.0.8078.73 / 0279989f6f077009. Failed automation source remains 16fc7584 with
.git/rebase-apply retained. Do not blindly invoke --requeue against that checkout:
interrupted preparation is intentionally fail-closed. After effect approval,
preserve the old builds root by a same-filesystem rename under controller.lock,
record old/new paths, then allow a fresh marked builds root for the new queue.
Do not clear failed receipts, reset/abort its am, or delete source/artifacts.

## Concrete proposed effects

1. Push integration/chromium-157-repair, open repair PR to main using prepared
body below, and merge through normal protection-aware GitHub APIs after local
qualification status. Hosted CI is skipped per operator policy.
2. Install the exact merged committed controller generation with
python3 scripts/install-automation.py --depot-tools
/home/ecochran76/workspace.local/depot_tools (no timer enable change). Verify
installed script hashes and existing config routing/limits remain correct.
3. Under the controller lock and with service inactive, preserve failed managed
build checkout/evidence by rename to a deterministic archival sibling. Record
rollback locator; leave retained profiles, old run receipts and baseline intact.
4. Start one bounded updater execution through the installed service. Changed
queue identity makes this a new target, so --requeue is unnecessary. It discovers
current Stable, builds/qualifies it, packages, opens/merges routine source PR,
publishes release and deploys for new launches under existing acceptance gates.
This step includes those live/provider effects; it is not mere patch replay.

Stop on new target drift requiring a changed patch, protection conflict,
resource gate or actual qualification failure. No billing/hosted CI purchase,
force-push, skipped checks, retained-profile mutation or destructive retry.

## Prepared packet closeout

Local merge validation passed: `python3 -m unittest discover -s tests -v`,
83 tests in 334.156s; `git diff --check --cached`; isolated queue replay at both
pinned .38 and fetched/discovered .50. Functional byte comparison against
e2d53b5 across scripts/tests/patches/upstream-revision.txt is empty. The merged
source/queue is the same input already independently reviewed and compiled.
All three remote release receipts survive. No unresolved index entries remain.

The PR body is prepared outside Git at
`~/.local/state/chromium-stealthcdp/qualification-157/integration-pr-body.md`.
It describes the conflict, exact qualified source/binary/queue identities,
local checks and .50's remaining compiled qualification requirement. Source
integration is concrete; effects in the numbered packet await final operator
approval. No remote mutation, controller install, source reset, archive rename,
updater start or notification was performed by this preparation packet.

Checkpoint: `outcome_progress`, integration conflicted -> validated local merge
ready / awaiting effect approval. No broad review cycle was restarted. This
closes preparation only, not the original updater recovery objective.

Memory disposition: `forbidden`, project Graphiti group is undefined and repo
instructions retain source-backed continuity in docs without speculative
cross-cloud writes. No write attempted. Receipt:
`~/.graphiti-openclaw/state/closeout-memory/20261110T013041Z-remember.json`.

## Approved execution: 2026-11-09

Operator explicitly approved the concrete effect packet. PR #8 was created and
merged through normal GitHub API with expected head 8daa8a2; merge commit
1a7c2d44f9557eeb6cead9c1dc77db5b88e36fd4. The PR had mergeable_state=clean;
local/qualification success records 83 local tests, 43 DCHECK Blink tests and CDP
smoke. No hosted CI was purchased or required. Public PR:
https://github.com/CochranResearchGroup/chromium-stealthcdp/pull/8

Exact merged generation installed with script hashes verified. Timer remained
enabled. Under exclusive controller.lock with service inactive, renamed the
marked old builds root (source 16fc7584, failed am intact) to
~/.local/state/chromium-stealthcdp/automation/builds-preserved-before-157-repair-1a7c2d4.
No reset, am abort, deletion or retained-profile mutation occurred.

Started one normal bounded updater invocation 0659e1d718314b2db842c797924a33e1.
Verified CPU 800%, memory 34359738368 bytes, swap 0, timeout 12h and control-group
cleanup. It fetched approved main and selected new run
157.0.8103.50-587a95d8d49a7644. Resource preflight returned deferred at prepare:
available memory 3880914944 bytes (3.61 GiB), disk 515278172160 bytes. Required
memory 32GiB was unmet. Service exited success, inactive/MainPID 0. This is a
resource gate, not a compiler or patch failure. No new compilation, release or
deployment happened; installed browser remains 156.0.8078.73+stealthcdp.0279989f6f07.

Private receipt: ~/.local/state/chromium-stealthcdp/qualification-157/recovery-execution.json.
Run receipt remains under automation/runs/<new-run-id>/run.json. Remote merge,
installed generation and approved-source readbacks bind integration outcome.
No immediate retry: free workstation memory first; the enabled daily timer will
retry this deferred target without --requeue, or a normal manual service start
can do so after headroom recovers. Do not raise limits or kill unrelated work.

Checkpoint: approved execution -> integrated/controller recovered -> deferred
at resource gate. `blocker_reduction`: repair queue accepted and installed;
full updater recovery remains open pending 32GiB headroom and .50 qualification.
