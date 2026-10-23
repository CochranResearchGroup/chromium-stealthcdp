# Plan 0006: Implement automated Linux Stable releases

State: OPEN

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
