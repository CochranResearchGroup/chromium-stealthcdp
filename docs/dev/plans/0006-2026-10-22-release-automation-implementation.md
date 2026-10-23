# Plan 0006: Implement automated Linux Stable releases

State: CLOSED

## Authority and Current State

Operator confirmed the consolidated design with implement on 2026-10-22.
The approved contract is docs/automated-release-design.md. Installation,
publication and enabling the user timer are authorized; repair PRs require
human review. Initial repo HEAD 760ff54f239d187d6dadf1e947a38d24fbde2a5a;
source 15a1e89ace187947b2a39881b45f4de992157b56, both clean. Existing Stable
156.0.8078.47 is the adoption baseline. No new Chromium rebuild is required
for unchanged version and queue. No graph index/group is defined; do not
initialize either. The implementation is not yet enabled.

## Work units and bounds

1. Primary: durable serialized controller, discovery/resource gates, existing gh
   publication/PR reconciliation, reporting, repair containment, systemd install.
2. /root/pipeline: scripts/automation_pipeline.py and its isolated tests only;
   dedicated source setup, patch replay, build and candidate qualification.
3. /root/deployment: scripts/automation_deploy.py and its isolated tests only;
   consistent activation, installed acceptance, rollback and owned retention.
4. Join interfaces; run meaningful fixtures and installed baseline acceptance.
5. Independent fresh drift_discovery review; adjudicate once, one bounded
   remediation pass and closed-world verification of accepted findings.
6. Commit/push coherent implementation; install immutable controller snapshot,
   adopt qualified baseline and enable timer; verify remote and runtime state.

Concurrency is three including primary until implementation join; no nested
agents. Each delegated unit has a 45-minute bound, one initial implementation
and one fix attempt. Checkpoint each validated slice; stop/reframe after two
hardening checkpoints without acceptance movement. Preserve operator source,
profiles and all live peers. No force pushes or public asset deletion.

## Acceptance

All agreed design controls require implementation and isolated fixture evidence.
Unchanged Stable baseline must validate and return no-op without publication.
Real gh read auth, disposable Agent Browser executable/ webdriver acceptance,
resource limits and owned repair timeout cleanup must pass before arming timer.
Document any report-only repair fallback honestly. Fresh systemd readback and
process census are required after integration. Raw evidence remains in user
state outside Git; curated summary here.

## Checkpoints

- v1 ready -> active: outcome_progress; design confirmed, worktrees recorded,
  primary plus pipeline/deployment agents spawned with disjoint ownership.
  Review not yet run; next action implement and qualify joined controller.

- v1 active -> review-remediation: outcome_progress; joined controller and
  delegated pipeline/deployment modules; 32 isolated tests passed. Real
  installed/candidate Agent Browser checks passed exact binary hash,
  webdriver=false and 15 owned descendants reaped. Actual gh push-access
  preflight and official Stable156 discovery passed. Real configured Codex
  model access and cgroup child-timeout cleanup passed; worker tool-authority
  isolation did not qualify, so the approved report-only fallback is explicit.
  No timer enabled yet. /root/pipeline and /root/deployment completed; primary
  inspected sources and independently reran joined tests. Runtime receipts are
  under ~/.local/state/chromium-stealthcdp/automation-design/.

## Independent review ledger

/root/review_implementation ran the single fresh drift_discovery pass and
independently reported 29 tests passing before the latest joined additions.
Primary adjudicates:

| ID | Disposition | Fix and criterion |
| --- | --- | --- |
| D1 | blocking | Exported patch clone retained local origin. Set explicit approved GitHub origin and independently guard it before integration/publication; fixture refuses wrong origin. |
| D2 | blocking | Preflight/discovery after a prior run omitted notification. Always attempt the deduplicated issue or persist delivered=false; reuse stage notification when already attempted. Isolated prior-run/auth-failure fixture added. |
| D3 | blocking | Entry-only disk reserve allowed later consumption. Monitor reserve every 15 seconds during candidate commands and reserve artifact-copy bytes before installation. Stop candidate and preserve installed activation. |

One bounded remediation pass addresses this consolidated finding set. Next:
closed-world verification of D1-D3 and critical regressions, then immutable
installation, baseline adoption/no-op service run and timer readback.

## Delivery and acceptance

- v1 review-remediation -> complete: outcome_progress. Independent closed-world
  evaluator /root/review_implementation verified D1-D3 pass, independently ran
  33 tests and found no critical remediation regressions. Primary accepted its
  bounded evidence and independently reran all 33 tests before installation.
- Source implementation 18268c01b03081d0e89fada03fa94a9407e5e916;
  systemd parser readback exposed quoted WorkingDirectory as invalid. Corrected
  to systemd %h expansion in 4e6dedd70dcaf059557440b98c0fdb4105bd5391;
  actual systemd-analyze verification then passed. An unrelated existing
  mail-receipts unit warning was not changed.
- Installed immutable controller generation:
  ~/.local/lib/chromium-stealthcdp-automation/generations/4e6dedd70dcaf059557440b98c0fdb4105bd5391.
  Config ~/.config/chromium-stealthcdp/automation.json. Both design and source
  implementation commits pushed to upstream/main; remote readback matched
  4e6dedd before this documentation-only closeout.
- Adopted public Stable156.0.8078.47 manifest digest and installed browser SHA
  2492fd6e2bab04707c263862df5563d10eee1660253cbcc0c06af3699ecc7b9c.
  Actual fresh installed Agent Browser selection returned webdriver=false and
  ownedProcessesRemaining=[] for all 15 observed owned PIDs. Receipt:
  ~/.local/state/chromium-stealthcdp/automation/baseline-acceptance.json.
- Actual bounded systemd service run returned unchanged, exit0/Result=success;
  no build, new tag, public release or activation was attempted. Official
  discovery matched156.0.8078.47 / 1d17a2e2ee147bb7d6ae2ab6abdb3a2510c17775.
- Timer enabled and active, Persistent=yes; next trigger read back as
  Friday2026-10-23 03:00:00 CDT. Service readback: CPUQuotaPerSecUSec=8s,
  MemoryMax=34359738368, MemorySwapMax=0, TimeoutStartUSec=12h,
  KillMode=control-group, Nice=10, IOSchedulingClass=3. No recurring approval
  is required for routine qualified releases within the approved contract.
- Post-acceptance OS census found no installed/source StealthCDP executable
  processes and none of the owned disposable processes remaining. Seven
  same-user unrelated process executable identities were unreadable, so global
  absence is not inferred and destructive retention conservatively defers.
  Receipt: automation/post-acceptance-process-census.json under user state.
- Repair admission remains explicitly report-only: installed configured model
  access and owned timeout cleanup passed, but tool/effect isolation did not
  qualify. No automatic repair worker/PR is claimed. The accepted fallback
  creates a durable report and deduplicated failure issue, requiring human
  repair review. See automation-design/repair-qualification/qualification.json.
- Future new Stable full builds/publication are implemented and fixture-gated,
  but not live-executed on an invented target; unchanged156 was intentionally
  neither rebuilt nor republished. First actual new target must pass every
  candidate/publication/installed gate before activation.

All delegated implementation workers returned complete and primary inspected
and integrated their files. No retained profile, active peer, OS browser default,
operator source/output tree, public release history or unrelated service was
changed. Source checkout remains clean at15a1e89. Graph memory disposition:
forbidden; no reviewed repo group exists. Durable continuity is this source
plan and operations guide, with raw receipts outside Git.
