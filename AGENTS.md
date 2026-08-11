# Chromium Stealthcdp

## Repo Context

- This repository owns the small downstream Chromium patch queue, reproducible
  build and smoke helpers, artifact metadata, and maintenance documentation for
  `chromium-stealthcdp`.
- Chromium source lives in the sibling checkout `../src`; large build products
  and promoted artifacts live outside this git repository under `../src/out/`
  and `../artifacts/`.
- Substantive work is planned under `docs/dev/plans/`. This lightweight repo
  does not use `ROADMAP.md` or `RUNBOOK.md` as additional authorities.
- `upstream-revision.txt` is the immutable Chromium base for the exported queue.
  The ordered files under `patches/` are the reviewable downstream delta.

## Repo-Specific Guidance

- Start branch-sensitive work by recording `git status --short --branch` and
  `git rev-parse HEAD` in both this repo and `../src`. Stop rather than
  overwriting unexpected changes.
- Keep upstream Chromium and downstream work distinct: create a new source
  branch from a pinned upstream SHA, sync dependencies, then apply the queue
  with `git am patches/*.patch` or an equivalent explicit path.
- Review a replay with `git range-diff`, `git diff --check`, and a diff against
  the pinned base before replacing the exported queue.
- Export patches from `../src` with `git format-patch --binary` over
  `$(cat upstream-revision.txt)..HEAD`; review the generated files before
  committing them here.
- Build into a new `../src/out/<candidate>` directory. Preserve DCHECKs when a
  candidate is intended to validate invariant-sensitive fixes.
- Run focused upstream tests plus `scripts/smoke.sh`; the smoke must report
  `success: true` and `navigator.webdriver` as `false`.
- Stage review candidates under a dedicated artifact root. Do not repoint the
  shared platform-neutral `../artifacts/chromium-stealthcdp/current` alias
  without an explicit cutover decision.
- Do not copy, clear, migrate, or reconstruct retained browser profiles without
  explicit operator authority. Authenticated browser acceptance uses an
  operator-seeded disposable profile unless a different lane is authorized.
- CodeGraph is preferred when an index exists. Neither this repo nor `../src`
  is currently initialized; use targeted source reads and tests, and do not
  initialize a graph without operator approval.
- No repo-specific Graphiti group is currently defined. Treat graph recall as
  advisory, keep source-backed continuity in repo docs, and avoid speculative
  or duplicate memory writes.

## Policy Loading Contract

- `AGENTS.md` is a routing surface, not a one-time pointer.
- Re-read the relevant policy files under `docs/dev/policies/` at the start of any non-trivial turn.
- Re-read the relevant policy files when task scope changes mid-session.
- When behavior is ambiguous, prefer re-reading policy over improvising from stale assumptions.

## Policy Re-read Triggers

- re-read planning-related policy before opening, revising, or closing a substantive plan
- re-read documentation-related policy before changing docs, contracts, or canonical authorities
- re-read validation and closeout policy before claiming work complete

## Policy Entry

This repo keeps its durable repo-local policy under `docs/dev/policies/`.

Read and follow:
- `docs/dev/policies/0001-policy-management.md`
- `docs/dev/policies/0002-policy-upgrade-management.md`
- `docs/dev/policies/0003-policy-adoption-feedback-loop.md`
- `docs/dev/policies/0004-graph-backed-memory-usage.md`
- `docs/dev/policies/0005-planning-discipline.md`
- `docs/dev/policies/0006-codegraph-usage.md`
- `docs/dev/policies/0007-git-worktree-hygiene.md`
- `docs/dev/policies/0008-commit-history-discipline.md`
- `docs/dev/policies/0009-branch-and-integration-strategy.md`
- `docs/dev/policies/0010-commit-and-push-cadence.md`
- `docs/dev/policies/0011-versioning-and-release.md`
- `docs/dev/policies/0012-turn-closeout.md`
- `docs/dev/policies/0013-validation-and-handoff.md`
- `docs/dev/policies/0014-upstream-fork-maintenance.md`
- `docs/dev/policies/0015-goal-execution-governance.md`
- `docs/dev/policies/0016-subagent-workflow-optimization.md`
- `docs/dev/policies/0017-parallel-plan-design.md`
- `docs/dev/policies/0018-notes-and-memories.md`

## Scope

- `AGENTS.md` includes repo-local guidance plus the policy entry section.
- The durable policy body lives under `docs/dev/policies/`.
- Keep repo-specific commands, environment details, and operational caveats in this file or adjacent local docs.
