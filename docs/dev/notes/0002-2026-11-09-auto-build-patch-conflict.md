# Auto-build failure: Chromium 157 patch replay

Date: 2026-11-09
Status: diagnosis complete; repair and release qualification pending.

## Research contract

Question: what stopped target `157.0.8103.38-8f5e9db0fcc7e083`, and is the
failure a compiler error, source mismatch, or downstream patch conflict?
Primary sources: immutable local Git objects, candidate source, controller
receipts and service journal. Stop after reproducing the exact failure and
identifying the conflicting source. No release, deployment, requeue, profile
mutation or automatic repair acceptance is included.

## Identity and evidence

Controller repo: `b1447b63d50556a9575128a43ed8f303176a8a92`, branch
`maintenance/stage-aware-retention`, initially clean. Operator source:
`15a1e89ace187947b2a39881b45f4de992157b56`, branch
`ec/chromium-stealthcdp-stable-156.0.8078.47`, initially clean.
Installed controller generation: `804590e9dde97ebba99d95ee5dff4a3a41fcbc40`
(private `runs/157.0.8103.38-8f5e9db0fcc7e083/repair.json` receipt).

Private evidence root (outside Git):
`~/.local/state/chromium-stealthcdp/automation/`.
`runs/157.0.8103.38-8f5e9db0fcc7e083/run.json` records `state=failed`,
`stage=prepare`. Its linked evidence log
`builds/runs/157.0.8103.38-8f5e9db0fcc7e083/evidence/1793956624274302155-012-git.log`
records patch 1 applied and patch 2 failed at `line_breaker.cc:1700`.
Compilation was not reached. `repair.json` dates the report to
2026-11-06T09:17:18Z and records a report-only repair, no worker started.

## Reproduction and cause

Run twice, each returning exit 1 immediately:

```sh
git -C ~/.local/state/chromium-stealthcdp/automation/builds/checkout/src apply --check "$PWD/patches/0002-Fix-stale-shape-result-during-line-overflow.patch"
```

```text
error: patch failed: third_party/blink/renderer/core/layout/inline/line_breaker.cc:1700
error: third_party/blink/renderer/core/layout/inline/line_breaker.cc: patch does not apply
```

This is a minimal read-only application check at the actual failing seam; it
reproduces patch rejection, not the original browser invariant failure.
Candidate HEAD `16fc75842fb71d13e7a71a975a0302ece369c9d9` has parent
`a733b5afbb3ba618844ff8876b89ad1a774b2f18`, exactly the target revision.
The sole delta is patch 1 in `navigator.cc` (`git show -s`, `git diff TARGET --stat`).

Ranked hypotheses before inspection: upstream context drift; upstream fix
already present; wrong candidate base. Wrong base is ruled out above.
Both upstream overlap and context drift are confirmed: at the pinned target,
`third_party/blink/renderer/core/layout/inline/line_breaker.cc:1704-1716`
already clears `item_result->shape_result` under
`LineBreakerClearShapeResultOnOverflowEnabled()` after `AssertNotEmpty()`.
`third_party/blink/renderer/platform/runtime_enabled_features.json5:4124-4129`
defines that feature as `stable` and cites Chromium bug 559557312.
[Downstream patch 2](../../../patches/0002-Fix-stale-shape-result-during-line-overflow.patch)
expects an immediate return after `AssertNotEmpty()` and adds an unconditional
clear plus a test hook, consistency check and regression test. Its context
therefore cannot match. This does not establish full semantic equivalence or
justify dropping its regression coverage without qualification.

## Current outcome and recommendation

The 2026-11-09 service journal reports `stopped` with
`explicit requeue or changed input required`. This is the controller's documented
failed-target gate ([operations](../../automation-operations.md),
[implementation](../../../scripts/automation.py), lines 348-349).
A separate `last-error.json` records a later GitHub DNS failure; it is not the
original target's patch failure.

Prepare a human-reviewable repair reconciling patch 2 with the upstream fix,
retain or adapt useful regression coverage, replay the full queue from the pinned
base, review range-diff, then run focused DCHECK-enabled LineBreaker tests and
CDP smoke before any explicit requeue. No patch queue or runtime state changed
in this investigation. No hosted CI, build, publication or deployment was run.
The original reproduction remains red; this is a diagnosis, not a fixed build.

Delegation: `/root/patch_research` independently inspected the pinned source and
confirmed upstream overlap, stable feature status and exact candidate parent;
primary independently read those same sources and reproduced the failure twice.
No graph index was created because repo policy reserves initialization for the
operator. Graphiti discovery transport reported degraded HTTP health; no
repo-specific group is defined. Durable continuity is this source-backed note.
