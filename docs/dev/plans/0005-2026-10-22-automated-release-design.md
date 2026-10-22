# Plan 0005: Automated update, build, publication and deployment design

State: PLANNED

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
prerequisites are settled. No automation design choices have been accepted yet.

Previews session: 943d71120464.
Questionnaire: aeee4d08ffbd.
Revision: 455aa0c8040b9f3bf459863e1fdf386384724e5a19088e42eaf1ce4d0a3e3130.
Retrieve structured answers with get_form_responses for that questionnaire;
do not infer answers from default controls or ordinary feedback comments.
Keep raw responses outside Git; record only accepted design decisions here.

## Documentation and acceptance

GLOSSARY.md captures established release lifecycle vocabulary from the current
repository. Add ADRs lazily under docs/adr only for a resolved consequential
trade-off; there is no accepted architecture ADR yet. Recompute the interview
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
