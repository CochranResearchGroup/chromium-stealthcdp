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
The next frontier covers schedule, resource budget, qualification, recovery,
credential custody, notifications and security-update exceptions. Decisions
whose prerequisites are still being inspected remain pending.

Round 2 is published in the same Previews session as questionnaire e2b56a1c353b,
revision 01de8166f1fb9c7c5c3471cdeec3ffb9e67709bfcf8d9bd955388624f40ffd16.
It asks Q8–Q19: schedule, resource budget, retention, qualification, local
rollback, public-release quarantine, urgent security behavior, credentials,
notifications, bounded retries, concurrency and source integration. These are
proposals, not accepted decisions. Later credential provisioning and any
alternative answers remain downstream decisions rather than assumptions.

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
