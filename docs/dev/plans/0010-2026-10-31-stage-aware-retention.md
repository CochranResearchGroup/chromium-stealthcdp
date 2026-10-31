# Plan 0010: Verified process census and stage-aware retention

State: CLOSED

## Current State

The operator-authorized follow-on is implemented, installed and operationally
verified. Root-owned read-only process inspection resolves non-dumpable process
visibility without ignoring ambiguous identities. Eligible automation compiler
output and old deployed staging copies were removed; retry assets, evidence,
installed browser, source and upgrade schedule remain intact.

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
that evidence.

Functional commit 804590e9dde97ebba99d95ee5dff4a3a41fcbc40 was installed as an
immutable controller generation. Root probe provisioned via explicit WSL root
invocation of `scripts/install-process-probe.py --user ecochran76`; exact
no-argument sudoers rule validated by visudo. Installed scripts and root-owned
probe hashes match the tested source. Live disposable fixture proved cwd, fd and
maps detection and active-directory protection, with no unknown PIDs.

Installed `automation.py --config ~/.config/chromium-stealthcdp/automation.json
cleanup` ran under controller.lock, without upgrade/requeue/notification. It
removed both automation compiler trees and old committed staging artifacts and
packages (four paths). The publication-failed candidate's staged artifact and
all package hashes verify; its failure receipt is unchanged. Installed selector
and executable hash verify unchanged. Source remains, the daily timer is enabled,
and the update service remains inactive (MainPID=0).

Net filesystem free-space gain: 27.978855 GiB; final 852.044178 GiB free,
75.344869% used. Concurrent filesystem activity means this net counter delta is
not an exact sum of deleted-file blocks. No operator checkout/artifact cleanup,
Chromium compilation, browser/profile cutover, hosted CI or publication occurred.

Private operational receipts and before/after evidence:
`~/.local/state/disk-space-recovery/chromium-stage-retention-20261031/`.
Functional generation is the tested commit above; this closeout changes docs
only. Full local suite: 81 tests pass; installed live qualification proves the
process gate and retention result, not acceptance of a new browser release.
