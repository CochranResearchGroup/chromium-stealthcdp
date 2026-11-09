# Plan 0011: Repair Chromium 157 patch replay

State: CLOSED

## Current State

The reviewed source repair is complete: both patches replay on Chromium
157.0.8103.38 and retain the downstream invariant and regression. Compiled
browser qualification subsequently passed under Plan0012; approved-queue
integration and updater requeue remain outstanding before automation can resume. Original diagnosis is retained in note 0002.
Both operator checkouts were clean at start (repo b543e2f; source 15a1e89a).

## Scope and acceptance

Primary owns one bounded repair proposal: replay both patches on pinned target
a733b5afbb3ba618844ff8876b89ad1a774b2f18 in isolated sparse source, retain
unconditional downstream clearing and existing regression coverage, export
binary patches and update pinned base and current patch-boundary documentation.
Add an unattended replay checker at the real git-am seam; demonstrate old queue
red, repaired queue green, range-diff and local controller tests.

Non-goals: installation, service/controller adoption, requeue, publication,
deployment, profile mutation, shared alias changes or hosted CI. Full Chromium
build/smoke remains an explicit qualification requirement before release; do
not describe source replay as compiled browser acceptance.

## Execution and bounds

Serial dependency: red checker -> isolated repair -> green replay + range-diff
-> independent review -> one remediation pass -> committed proposal.
Two repair attempts maximum. Primary owns edits, policy and integration.
Independent reviewer owns read-only verification of the frozen diff. Parallel
implementation is not useful because patch generation, base identity and
validation are coupled; review is the independent lane. Checkpoint after this
packet with exact remaining build qualification gate. Stop after a reviewed
source-level proposal or verified blocker; no automatic live retries.

Repo proposal branch: `repair/chromium-157-patch-replay`, based on
`b543e2fda4a13f8d189c4ddda5b474dcd8e12a37`.

## Repair evidence

Red command, before editing patches (exit 1 in less than one second):

```sh
python3 scripts/check-patch-replay.py --src ~/.local/state/chromium-stealthcdp/automation/builds/checkout/src --revision a733b5afbb3ba618844ff8876b89ad1a774b2f18
```

It ran actual `git am` and rejected patch 2 at `line_breaker.cc:1700`, matching
the original failure. After repair the same command passes, as does its default
pinned-base invocation. It extracts four touched source blobs into an isolated
temporary repository. This is the correct regression seam for patch replay;
it does not claim to reproduce the browser invariant through execution.

Source worktree:
`~/.local/state/chromium-stealthcdp/patch-repair-157/source`, branch
`repair/chromium-157-patch-replay`, HEAD
`2dd44af34c06840df3aaebc6cf32ebc691293f43`, clean. It is a sparse source
worktree, not a dependency-synchronized build checkout. Failed automation am
state, operator source, installed controller, timer and browser aliases are
untouched. Fetching the old operator commits into the candidate Git object
store enabled full-tree range-diff without changing either existing checkout.

Reviewed command:

```sh
git -C ~/.local/state/chromium-stealthcdp/patch-repair-157/source range-diff --no-color 1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775..15a1e89ace187947b2a39881b45f4de992157b56 a733b5afbb3ba618844ff8876b89ad1a774b2f18..2dd44af34c06840df3aaebc6cf32ebc691293f43
```

Result: patch 1 `=`; patch 2 `!`, limited to author/message and reconciliation
of the upstream guard in the overflow path. The header/test additions are
unchanged, and the complete regression test source is byte-identical to the
old downstream source. Patch 1 stable patch-id remains
`cffde3fb05a73c96ec730e18abb95ea2b0e58971`. Patch 2 intentionally changes from
`fb016ad4f07528a0acd0b4fffe2124d97b65528b` to
`71dcd97e1869f960e0029666c4051d02eaefc1b6`.

Both the source delta against the pinned base and the exported repo delta pass
`git diff --check`. The source-level fix addresses the confirmed context-change
hypothesis without retiring the regression or weakening the old downstream
unconditional-clear invariant. No debug instrumentation was added.

## Independent review

Delegation receipt: `/root/repair_review`, read-only drift-discovery of the
frozen proposal. Reviewer independently ran the checker, checked source HEAD,
verified patch 1 identity and unchanged header/test additions, and found no
blocking source-proposal findings. Primary accepts this evidence and also ran
the checker, compared patch IDs and entire test source, and reviewed range-diff.
No remediation cycle was required. Browser compilation/acceptance is outside
this review's evidence and remains required before release.

## Memory disposition

`forbidden`: no repo-specific Graphiti group is defined; repo instructions keep
source-backed continuity in repo docs and avoid speculative writes. The
healthy service does not authorize placing this project result in another cloud.
No Graphiti write was attempted. Non-write receipt:
`~/.graphiti-openclaw/state/closeout-memory/20261109T112108Z-remember.json`.

## Validation and closeout

Primary validation: `python3 -m unittest discover -s tests -v` passed all
81 tests in 345.690 seconds; the replay checker passed twice after the repair;
`git diff --check` passed in both repositories. Validation inputs: controller
base `b543e2fda4a13f8d189c4ddda5b474dcd8e12a37` plus this proposal's diff,
Chromium pinned base `a733b5afbb3ba618844ff8876b89ad1a774b2f18`, source
`2dd44af34c06840df3aaebc6cf32ebc691293f43`. No hosted CI ran; tests use this
workstation's local Python/runtime, not a hosted image, and no Chromium binary
was compiled or executed. Unchanged original failed-run receipt and am state
remain available; the green repro uses isolated exact-target blobs.

Checkpoint: source-repair active -> complete / awaiting browser qualification;
`outcome_progress`: exact patch rejection is resolved and locked down by the
real git-am checker. Reviewer complete with no accepted blocking findings.
No debug instrumentation or retained throwaway harness exists; the isolated
source worktree is intentionally retained for review and subsequent build work.

Next bounded unit: populate a separate full candidate checkout from the pinned
base with synchronized dependencies, replay this queue, build into a new output
directory with DCHECKs under the documented eight-job/32-GiB/12-hour limits,
and run `LineBreakerTest.*` plus `scripts/smoke.sh`. Require `success: true` and
`navigator.webdriver=false`. Compiled qualification is still open; subsequent
approved-queue integration/controller adoption and any release/deployment
requeue must respect their existing human-review and live-effect gates.
This closed packet delivers a reviewed source repair, not an accepted release
or resumed production updater.
