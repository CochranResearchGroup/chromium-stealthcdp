# Activate chromiumQ for managed launches

State: PLANNED

Status: ready-for-agent

## What to build

New Agent Browser tasks launch the qualified chromiumQ binary after the coordinated deployment.

## Blocked by

0024 and 0025.

## Acceptance criteria

- [ ] Verify merged source, immutable installed generations and canonical status.
- [ ] Bind one fresh disposable managed process to the selected binary and manifest. Close it and verify task, process and profile cleanup.
- [ ] Preserve active sessions and verify rollback resolution to the qualified prior installation.
