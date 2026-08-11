# Policy adoption: repo-policy-selector v0.1.15

Date: 2026-08-11

## Decision

Adopt the pinned `repo-policy-selector` bundle `v0.1.15` at source commit
`082a4bc9be8119b059dc8efcc5a85c2cb694b9da` using the
`standalone-library` profile plus the selector-recommended
`validation-and-handoff` and `upstream-fork-maintenance` modules.

The installed selector lives under `.codex/skills/repo-policy-selector/`; its
install record is `.codex/policy-selector-install.json`. Repo-local active
policy lives under `docs/dev/policies/` and is wired through `AGENTS.md`.

## Adopted Modules

- policy-management
- policy-upgrade-management
- policy-adoption-feedback-loop
- graph-backed-memory-usage
- planning-discipline
- codegraph-usage
- git-worktree-hygiene
- commit-history-discipline
- branch-and-integration-strategy
- commit-and-push-cadence
- versioning-and-release
- turn-closeout
- validation-and-handoff
- upstream-fork-maintenance
- goal-execution-governance
- subagent-workflow-optimization
- parallel-plan-design
- notes-and-memories

## Deferred Module

- `subagent-runtime-governance` was reviewed and deferred. This repository may
  occasionally use a bounded validation worker, but it does not build,
  configure, or operate the subagent runtime. The module's own adoption notes
  direct ordinary repositories to the already adopted workflow, parallel-plan,
  and validation policies instead.

## Local Fit

- The lightweight profile fits: this repository owns a small patch queue and
  build/artifact helpers and does not need roadmap/runbook governance.
- Upstream-fork maintenance is required because `../src` carries a minimal
  downstream commit over active Chromium upstream.
- Validation and handoff policy is required because source tests, smoke,
  artifact provenance, and authenticated browser acceptance prove different
  things.
- CodeGraph policy is retained for future availability, but neither this repo
  nor `../src` currently has an index. Targeted native inspection is the
  documented fallback; initialization remains an operator decision.
- No repo-specific Graphiti group is currently defined, so repo documents are
  the durable authority and any graph write must remain compact and
  source-backed.

## Adoption Experience

- The one-shot local bundle install and deterministic profile selection worked
  cleanly.
- Generated `AGENTS.md` intentionally required repo-specific replacement of
  placeholder context and commands; that adaptation was completed in the same
  slice.
- The pre-adoption forced planning audit reported missing roadmap, runbook, and
  plans surfaces. The selected profile does not adopt roadmap/runbook
  governance; a serial plan under `docs/dev/plans/` supplies the applicable
  bounded-planning contract.
- The active goal caused a second deterministic selector pass to add goal,
  delegation, parallel-plan, and continuity modules. Concrete local bounds were
  added to the goal-execution policy before source work began.
- Behavioral success remains under evaluation until Plan 0001 completes its
  source, artifact, and browser acceptance gates.

## Upgrade Cadence

Review selector bundle updates during Chromium upstream refreshes or when a
policy audit reports drift. Do not overwrite repo-local adaptations blindly;
use the installed selector's upgrade report and merge-review changed modules.
