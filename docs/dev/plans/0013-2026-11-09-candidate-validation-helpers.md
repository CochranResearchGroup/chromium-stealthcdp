# Plan 0013: Candidate validation helper repair

State: CLOSED

## Current State

Both observed helper failures are repaired and independently reviewed. The
real CLI regressions pass, staged smoke/freshness checks pass, and all 83 local
tests pass. The Chromium 157 candidate remains compiled/qualified under
Plan0012. Binary, patch queue and Chromium source identities are unchanged.
No rebuild, retained-profile mutation, release or activation occurred.

## Scope, loop and bounds

Primary owns smoke process-group cleanup and freshness Git-root detection,
real CLI regression tests and staged verification. Preserve exit-code meaning,
reject non-repository/nested source paths, and kill only the freshly created
smoke browser process group. No retained-profile/process cleanup or activation.
Add fixture at the actual shell seam: parent browser with lingering child and
successful CDP result. Assert child termination/profile deletion plus unrelated
process survival. Freshness fixture uses actual git worktree and valid manifest.
Both tests must fail before fixes and pass after; original staged smoke and
freshness commands must then exit0. Two repair attempts and one closed-world
review/remediation pass. Existing build-review findings remain closed; no new
broad source review. Independent helper reviewer owns read-only verification.
No publication/push/requeue/install, no hosted CI. The exact acceptance gate is
staged helper commands returning0 with matched binary identity and no owned
smoke browser children remaining.

## Red-to-green evidence

Before fixes, `python3 -m unittest discover -s tests -p test_candidate_helpers.py -v`
failed both tests in 0.601s: linked worktree returned 2/missing checkout; smoke
left the owned child writer alive after parent termination. After fixes the
same command passed 2 tests in 1.751s. The fixture drives the actual shell helper
with a browser parent/child and successful CDP fixture; it also proves the
unrelated sentinel process survives. Freshness uses real Git/linked-worktree
and manifest/checksum checks, and still rejects a nested source path.

Accepted hypotheses: parent-only termination caused lingering profile writers;
a .git-directory assumption rejected linked worktrees. Source/manifest identity
was not the problem. Fixes create a fresh setsid browser group with job control
disabled, bounded TERM/KILL cleanup, original verdict preservation, and bounded
owned-directory cleanup. Freshness requires the supplied path to equal Git's
actual repository root. No identity checks were relaxed.

The original staged smoke command now exits 0 with success=true/webdriver=false
(`evidence/staged-smoke-fixed.json`); original freshness command now exits 0 with
fresh=true against source 997304ee and queue 587a95d8d49a. Artifact manifest still
truthfully records 970d417, the commit used for initial staging; helper-only
changes do not alter the compiled browser, queue or source tree. A separate
staging receipt binds the final helper commit without rewriting that manifest.

Independent `/root/qualification_review` conducted closed-world H1/H2 review,
reran both real CLI regressions (2 tests/1.817s), inspected process-group scope,
exit status and root rejection, and reported no blockers. Primary accepts the
evidence and independently ran the regressions and original staged commands.
The full local suite is recorded separately in
`~/.local/state/chromium-stealthcdp/qualification-157/evidence/helper-full-tests.log`.
Fresh same-user /proc readback found zero staged-browser processes and zero
unreadable identities. Exact disposable directory from failed staged smoke was
removed only after that readback; no retained profile was touched.

## Validation and closeout

Primary full local validation: `python3 -m unittest discover -s tests -v`
passed 83 tests in 225.320s. `bash -n scripts/smoke.sh scripts/check-freshness.sh`
and `git diff --check` pass. Validation source: 970d417 plus the exact helper/
regression-test diff committed by this packet; Chromium source 997304ee and
binary SHA256 bd5efff69d413e45d765a6c0e720c93061943e0215d2dbd04384f96c1ae382f7
are unchanged. No hosted CI or Chromium recompilation was run for helper-only
changes; the full build/43 upstream tests remain the Plan0012 acceptance.

H1/H2 blocking findings are resolved in one repair/review pass; no additional
findings were introduced by independent review. Checkpoint:
`outcome_progress`, staged validation blocked -> helper repair verified.
No debug instrumentation or throwaway prototype was added. Permanent tests
preserve the actual failure patterns and unrelated-process safety assertion.
Final `staging.json` in the execution root records helper commit/hash identity,
individual staged-smoke/freshness exit codes, artifact/source/binary hashes and
unchanged shared/installed aliases. Next gate is controlled approved-queue
integration and explicit updater requeue; this packet grants neither effect.

Memory disposition: `forbidden`, no defined project Graphiti destination and no
authority to write into another cloud. Repo docs retain durable evidence.
No Graphiti write was attempted. Non-write receipt:
`~/.graphiti-openclaw/state/closeout-memory/20261109T191554Z-remember.json`.
