# Plan 0009: Post-deployment build cleanup

State: OPEN

## Current State

Source implementation now separates installed rollback releases from disposable
completed/superseded build output and runs retention immediately after durable
deployment completion, as well as on later cycles. Local provider-free tests
pass; immutable generation installation and runtime readback remain.
The installed runtime also reports an ambiguous process census, which must
continue to defer destructive cleanup rather than weakening process protection.

## Scope and acceptance

Clean only marked automation-owned build output, staged artifacts and packages
once a deployment is committed, and older terminal output once superseded by a
committed deployment. Preserve installed current/rollback releases, live
references, unfinished candidates, latest failure evidence, source and profiles.
Run cleanup immediately after completion and on later maintenance cycles.
Cleanup failure must not reclassify a successful installed transaction as failed.
Reject malformed run IDs, symlink traversal and nested mounts. Retain receipts
and 90-day logs. Validate with provider-free local tests, then install a committed
immutable controller generation without running an upgrade or repointing the
installed browser. No hosted CI, provider publication or browser cutover.

## Execution and review

Primary owns implementation, local tests and installed identity readback.
One independent bounded review checks destructive scope and failure handling.
No Chromium build or live-browser acceptance is needed: browser code and
selection are unchanged. The existing latest failure/deferred runs remain
protected unless a newer committed deployment establishes supersession.

## Validation and review

Local `python3 -m unittest discover -s tests -v`: 57 tests pass. Validation
covers only the Python automation; no Chromium compilation or browser cutover.
Hosted GitHub Actions was not used under the operator CI-cost policy.
`git diff --check` passes. Base source checkpoint: 8cb678cda9fd11f32ac3705ddc1fa4a2c38f7e9b.

Delegation: spawned /root/review_chromium_cleanup for one bounded destructive-
scope review. R1 (same-device ancestor bind mount could redirect deletion) was
accepted as blocking, fixed, and independently verified in closed-world mode;
12 retention tests pass in that verification. No remaining R1 issue reported.
Primary accepts that evidence; no new broad review round is needed.

The installed process census currently has seven unreadable same-user
identities and must defer deletion. Preserve this gate and report it. The
operator-managed sibling Chromium source/output tree is never a cleanup target.
