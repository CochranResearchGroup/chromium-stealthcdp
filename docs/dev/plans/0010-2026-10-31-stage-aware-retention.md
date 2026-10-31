# Plan 0010: Verified process census and stage-aware retention

State: OPEN

## Current State

Plan 0009 cleanup is installed but defers on non-dumpable same-user system
processes. A deployed build retains 13.3 GiB; a publication-failed packaged
candidate retains 13.2 GiB of compiler output. The operator authorized this
bounded follow-on implementation and cleanup.

## Scope and acceptance

Use an optional root-owned, no-argument, read-only process probe scoped to the
operator's UID and two managed Chromium roots. Preserve every ambiguous or
live-reference gate; do not change kernel ptrace/dumpability or ignore PIDs.
Retire only compiler output of failed integrate/publish stages after verifying
all retained packages and the staged artifact executable. Keep packages,
artifact, receipts and failure evidence for explicit retry. Keep compile and
deployment failures protected. Add a locked provider-free cleanup command.
Run local tests, independent destructive-scope review, install a committed
controller/probe, and execute maintenance with before/after receipts.

Non-goals: upgrades/requeue/publication, browser/profile/service cutover,
operator checkout cleanup, source deduplication, compiler flag changes.

Primary owns integration, provisioning and execution. Independent agent
/root/chromium_census_review owns the disjoint process probe/tests and then
reviews integration. Serialized critical path: tests, review, commit, install,
live probe qualification, cleanup. No hosted CI.

## Validation and outcome

Local validation: `python3 -m unittest discover -s tests -v` passes 81 tests;
`git diff --check` passes. Source base b4bebdc85505de44f8815fa1af95a5cdc5e1a22f.
No hosted CI or Chromium compilation: this changes automation only.

Delegation receipt: /root/chromium_census_review implemented the disjoint probe
and tests; primary inspected its source and ran the full suite. Agent then
reviewed parent integration. R1 (malformed census could accept null unknownPids)
was accepted blocking; R2 (check all provisioning ancestors) accepted hardening.
Both were fixed and independently verified in one closed-world remediation
pass: 17 focused tests pass and no critical regression reported. Primary accepts
that evidence. Installed operational verification and cleanup remain pending.
