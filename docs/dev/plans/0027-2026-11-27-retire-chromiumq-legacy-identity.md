# Retire legacy inputs and entry points

State: PLANNED

Status: ready-for-agent

## What to build

All supported active entry points use chromiumQ without requiring legacy build IDs or installation references.

## Blocked by

0026 and a verified consumer census.

## Acceptance criteria

- [ ] Confirm deployed config, callers, retained-state readers, generated contracts and updater ownership before removal.
- [ ] Remove the legacy input alias and retire unused launcher and updater entry points while preserving historical evidence and retained profiles.
- [ ] Re-run managed launch, package/install and rollback checks.
