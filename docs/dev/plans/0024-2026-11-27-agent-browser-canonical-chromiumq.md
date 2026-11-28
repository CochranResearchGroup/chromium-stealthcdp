# Normalize Agent Browser input and emit chromiumQ

State: PLANNED

Status: ready-for-agent

## What to build

Existing and new consumers route to the same qualified browser during migration. Newly emitted identity is chromiumQ.

## Blocked by

None. Can start immediately.

## Acceptance criteria

- [ ] Config and requests using either build ID select the same browser. Conflicting dual declarations are rejected.
- [ ] CLI, API, generated clients, dashboard and newly persisted state use the canonical output ID.
- [ ] Existing retained state remains readable. Local contract and routing tests pass.
