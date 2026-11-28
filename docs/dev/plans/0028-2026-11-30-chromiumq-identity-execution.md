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
| 0025 | None | Coordinator | running | chromiumQ Linux/Windows installer, package and updater identities |
| 0026 | 0024, 0025 | Coordinator | pending | Merged generation, managed activation and rollback verification |
| 0027 | 0026 and verified census | Coordinator | pending | Legacy alias and active entry point retirement |

Validation and integration results belong here. The three-hour goal allocation
starts at epoch 1795837107. Stop and checkpoint before epoch 1795847907.
