# Execute the chromiumQ identity migration

State: OPEN

## Current State

Plan 0023 and tickets 0024–0027 are frozen at `a64b36e`. The
`integration/chromiumq-identity` branch starts there, from chromiumQ main
`85dcd4a1c2661d4b47650a0e43f0b914971af591`. Agent Browser work uses a separate
branch in the Agent Browser repository. Its dirty root is outside the write scope.

| Ticket | Blockers | Owner | State | Owned scope |
| --- | --- | --- | --- | --- |
| 0024 | None | agent_browser_0024 | running | Agent Browser worktree, identifiers, consumers and contracts |
| 0025 | None | Coordinator | validated | chromiumQ Linux/Windows installer, package and updater identities |
| 0026 | 0024, 0025 | Coordinator | pending | Merged generation, managed activation and rollback verification |
| 0027 | 0026 and verified census | Coordinator | pending | Legacy alias and active entry point retirement |

Validation and integration results belong here. The three-hour goal allocation
starts at epoch 1795837107. Stop and checkpoint before epoch 1795847907.


## Checkpoint

- 0024 worker `agent_browser_0024` owns `feat/chromiumq-build-identity` in
  `/home/ecochran76/workspace.local/.worktrees/agent-browser/chromiumq-0024`,
  based on Agent Browser origin/main `9a9845978f57cd84de48ff675de2e00abe99e83c`.
  The worker reported a confirmed red/green identity codec and active CLI checks.
- 0025 is committed on the integration branch at `670ea61`. The promoted
  artifact schema is `chromiumQ.artifact.v1`. Readers accept the prior schema,
  and the canonical package, install roots, GitHub repository, and updater
  units use the chromiumQ identity. Existing updater state and controller lock
  remain at their configured location during the compatibility window.
- Focused Linux/Windows packaging, provision, and rollback fixtures passed
  28 checks before the final process-probe namespace and promotion wiring edits.
  The full suite for the final change is running alongside independent checks.
  Its log is `/tmp/chromiumq-0025-final-suite.log`.
- Live activation remains gated on verified 0024 and 0025. The automated
  installer has a 200 GiB free-disk reserve plus the candidate copy requirement.
  A readback during 0025 showed about 166 GiB available. Do not bypass the
  reserve or clean retained state merely to advance the ticket.

### Validation checkpoint at f3acfe0

- 0025 passed all 124 local tests. The previous full-suite smoke cleanup race
  and the codec cleanup race observed on the staged binary each passed after
  bounded owned-session verification. The final suite log is
  `/tmp/chromiumq-0025-final-validation.log`.
- The canonical-schema Chromium 158 candidate is under
  `/home/ecochran76/workspace.local/chromium/artifacts/chromiumQ-candidates/identity-158-I74Myc/current`.
  Its binary digest matches the existing installed artifact. The post-fix
  decoder receipt records the revised harness separately from the earlier
  staged manifest's recipe digest.
- Stable Agent Browser runtime host reported inactive with exit status 9.
  Preserve the active development lanes. Re-read stable runtime state and
  ownership before ticket 0026. The legacy updater timer is still enabled.

### Publication checkpoint

- Draft PR 28 carries the validated installer and updater changes into
  chromiumQ review. Keep it separate from live activation until Agent Browser
  0024 is integrated and the stable runtime ownership is re-verified.
  https://github.com/CochranResearchGroup/chromiumQ/pull/28
- Agent Browser 0024 is now on `platform/chromiumq-build-identity` in its
  existing isolated worktree. The worker is still active.
- The full suite passed 124 tests at `f3acfe0`. No broad code review or
  remediation TDD pass has been run.
