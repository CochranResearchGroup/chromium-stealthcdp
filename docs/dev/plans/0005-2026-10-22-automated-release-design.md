# Plan 0005: Automated update, build, publication and deployment design

State: OPEN

## Objective

Use the operator-invoked grill-with-docs interview to establish the automation
contract, document agreed vocabulary and consequential architecture decisions,
and confirm shared understanding before implementation or enabling schedules.
The operator requested a Previews questionnaire when there are more than five
questions. No new operational automation is authorized by an unanswered form.

## Current State

Both tracked worktrees began clean. Patch repo main is
304a2a6a26fa0db933749da296dc7b2100c788f4; Chromium source is
15a1e89ace187947b2a39881b45f4de992157b56 on the Stable 156 downstream branch.
Existing helpers implement build, smoke, promotion, packaging and installation.
No scheduled CI release/update orchestrator is implemented in this repository.
The older updater-packager system document contains proposed helpers that do
not exist and must not be treated as delivered automation.
All three interview rounds are complete. Operating policy and repair bounds
are settled; the final instruction to use existing gh authentication overrides
the earlier dedicated-credential preference. The consolidated design is in
docs/automated-release-design.md and awaits shared-understanding confirmation.
No operational automation is enabled.

## Interview frontier

Round 1 asks seven independent policy decisions: routine automation authority,
platform scope, deployment targets, detection cadence, active-browser behavior,
patch-conflict handling and build location. Each recommendation is an offered
choice, never an inferred answer. Other has a conditional free-text answer.
Resource budgets, scheduling details, security-update exceptions, recovery,
credentials, notifications and platform-dependent gates follow only when their
prerequisites are settled.

Round 1 response a04e811b46a5411b8a4499a496c105f2 was retrieved as complete
against the exact revision below. All seven recommendations were explicitly
selected: unattended routine pipeline; Linux first; current user/workstation;
daily checks plus manual trigger; active browsers finish normally; stop and
prepare reviewable repairs on conflicts; dedicated local managed checkout.
No Other answers were active. Raw answers remain outside Git. These choices
settle design policy, not permission to enable an unfinished implementation.

ADRs 0001 and 0002 record the consequential placement and continuity trade-offs.
At the end of round 1, the next frontier covered schedule, resource budget, qualification, recovery,
credential custody, notifications and security-update exceptions. Decisions
were not treated as settled before their answers arrived.

Round 2 is published in the same Previews session as questionnaire e2b56a1c353b,
revision 01de8166f1fb9c7c5c3471cdeec3ffb9e67709bfcf8d9bd955388624f40ffd16.
It asks Q8–Q19: schedule, resource budget, retention, qualification, local
rollback, public-release quarantine, urgent security behavior, credentials,
notifications, bounded retries, concurrency and source integration.

Round 2 response ce433e392bf249e3a556aa6168905ae5 was retrieved as complete
against that exact revision. All twelve recommendations were explicitly
selected, with no active Other answers:

| Area | Accepted policy |
| --- | --- |
| Schedule | Daily at 03:00 America/Chicago, with a catch-up check after unavailability. |
| Resource budget | Eight compile jobs, eight CPU-equivalents, 32 GiB memory ceiling, 12-hour run limit, 200 GiB free-disk reserve, low CPU/I/O priority; defer when headroom is insufficient. |
| Local retention | Active and previous releases plus one more good release; preserve versions used by running browsers, latest failed-run evidence and 90 days of logs. Clean only unused automation-owned files. Never delete public history or operator-owned source/output trees. |
| Qualification | Exact Stable identity, clean patch replay, normal Chromium branding, official release flags and matching optimization profiles, retained-patch regressions, CDP webdriver=false, package/provenance/hash checks and isolated Agent Browser acceptance before release; verify installed launch after activation. |
| Local recovery | Automatically restore previous known-good activation after a failed installed check and stop further deployment. Preserve profiles, active peers and failure evidence. |
| Public defects | Quarantine confirmed release defects and withdraw latest eligibility while preserving tag/assets. Local environmental failures do not automatically condemn the release. |
| Urgent security | Preserve the no-forced-restart rule and prominently flag older running browsers. |
| Credentials | Round-2 preference for a dedicated credential; superseded in round 3 by the explicit instruction to use existing gh authentication. No App or extra token provisioning is required. |
| Notifications | Deduplicated GitHub issues for failures/repair proposals; release notes and receipts for successful runs. |
| Retries | One retry for a verified transient fetch/download failure; reconcile uncertain publication/deployment effects before resuming. No identical blind rebuild loops. |
| Concurrency | One pinned run at a time; coalesce pending triggers into the newest pending target after it finishes. |
| Integration | Automatically merge qualified routine PRs; repairs require human review; never bypass protections or force-push. |

ADRs 0003 and 0004 record recovery/public-history and source-integration
trade-offs. Round 3 settled the credential and repair-drafting frontier.

Round 3 is published in the same session as questionnaire fa40846681c1,
revision 04c87cf74ca69fefa01f6e67c4bb4a3c7a890c203d48ea5362b6b7ad492c9242.
Q20 proposes a repository-only GitHub App with short-lived installation tokens;
Q21 proposes one isolated 30-minute Codex repair-draft attempt per failed target,
with human review and report-only fallback when unavailable.

Round 3 response 4747459c3d9f4eaf8883ef28392aea39 was retrieved complete against
that exact revision. Credential choice was Other with the explicit instruction
to use gh; this is preserved as a custom instruction, not silently mapped to
the recommended GitHub App. It is interpreted as the existing installed gh login
and supersedes round 2's dedicated-credential preference. The one-attempt,
30-minute isolated Codex repair-draft recommendation was explicitly selected.
ADR 0005 records the credential trade-off. There are no unanswered design
branches; final consolidated confirmation remains, not another questionnaire.

Previews session: 943d71120464.
Questionnaire: aeee4d08ffbd.
Revision: 455aa0c8040b9f3bf459863e1fdf386384724e5a19088e42eaf1ce4d0a3e3130.
Retrieve structured answers with get_form_responses for that questionnaire;
do not infer answers from default controls or ordinary feedback comments.
Keep raw responses outside Git; record only accepted design decisions here.

## Documentation and acceptance

GLOSSARY.md captures established release lifecycle vocabulary from the current
repository. Add ADRs lazily under docs/adr only for a resolved consequential
trade-off. Recompute the interview
frontier after every round and document decisions as they settle. This design
packet is complete only after all decision branches have been visited and the
operator confirms shared understanding. Implementation is a subsequent packet.

## Delegation and memory

Read-only fact inventory /root/automation_design_facts completed successfully.
Primary reconciled its distinction between proposed and implemented helpers
against the current file inventory; build and installation evidence remains
anchored to Plans 0003 and 0004. No delegated mutation or runtime qualification
was performed. Graph memory disposition: forbidden; no reviewed repo group is
defined, so retain this interview locator and source continuity in repo docs.

The follow-up read-only fact inventory confirmed operating user timers,
lingering and delegated cgroup v2 CPU/memory controls. The host has 28 logical
CPUs and 94 GiB RAM; current free capacity is advisory and must be checked per
run. Noninteractive GitHub authentication works but has broad repo/workflow
scopes. Desktop/email delivery was not established. These facts ground the
round-2 recommendations; no service, credential or notification was changed.

Final read-only prerequisites: GitHub native auto-merge is disabled, all three
merge methods are enabled, and the main protection endpoint reported no branch
protection while the ruleset listing returned none. No settings were changed;
controller-driven merging after qualification does not require enabling native
auto-merge or bypassing protections. A dedicated automation credential has not
been provisioned and is no longer required following the round-3 gh instruction.
Codex CLI 0.163.0 supports noninteractive exec and separate
workspaces; its help exposes no explicit wall-time, token or dollar cap.
An outer service/process limit can enforce wall time. Authentication/model access
and owned-process containment under timeout remain implementation acceptance,
not proven readiness. Fact inventory /root/automation_design_facts reported these
limits without invoking a model or changing repository/runtime settings.

Independent design consistency review /root/review_automation_design completed
with no material findings. It compared the consolidated design with accepted
policies and ADRs, including the credential override and repair bounds. Primary
accepted this bounded review; it is documentation consistency evidence, not
implementation or runtime acceptance. Final design confirmation remains open.
