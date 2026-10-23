# Plan 0007: Private Slack upgrade announcements

State: OPEN

## Current State and authority

Operator explicitly requested Slack announcements for upgrade success and
failure. Existing controller posts failure issues but has no Slack adapter.
Starting main fbe30d8 is clean and pushed. Scope: one operator-selected Slack
workspace/private DM; curated outcomes only, existing Slack Receipts service,
idempotent delivery/outbox, success/failure/deferred/rollback outcomes and
service timeout/failure hook. Unchanged daily checks remain quiet. No tokens,
profiles, raw logs or extra recipients are introduced.

## Work units and acceptance

Primary owns notifier, controller/service wiring, tests and deployment.
/root/slack_transport_facts has read-only10min exact supported transport lookup;
no sends or edits. Workspace choice is pending while independent implementation
proceeds. Verify recipient readiness; send one clearly labeled setup test after
selection. Tests must cover deduplication, failed/uncertain delivery outbox,
no-op silence and success/failure paths. Commit/push, install new immutable
controller, verify service/timer and test message receipt before closeout.
Bound one implementation and one fix pass; preserve existing authority envelope
and browser activity. Source-backed continuity here; no repo Graphiti group.

## Implementation checkpoint

Notifier/controller/service-hook wiring implemented; 42 provider-free tests
pass, including timeout, per-invocation failures, explicit retry attempts,
quiet unchanged checks, uncertain-key reconciliation and terminal failed-action
isolation. Existing automation remains active on its previous verified generation;
Slack delivery is not configured or enabled pending the selected workspace.

/root/slack_transport_facts completed exact read-only service lookup and a
bounded integration review. Primary inspected and accepted its transport
recipe: installed Slack Receipts Python service layer used by MCP/API, existing
credential loading, resolved human identity binding, status=sent with ok,
channel and timestamp required. No shared service restart or new machine token.
Two blocking review findings accepted and fixed in one pass: failed provider
action poisoning later notices, and constant identity suppressing subsequent
preflight failures. Their targeted fixtures pass; closed-world review pending.
No real Slack message has been sent. Remaining gate is recipient workspace,
then readiness/test receipt, immutable controller installation and runtime readback.
