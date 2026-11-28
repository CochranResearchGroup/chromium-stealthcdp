# Migrate installer and updater identities

State: PLANNED

Status: ready-for-agent

## What to build

A qualified chromiumQ installation can be upgraded and rolled back under the new package, launcher and updater identity.

## Blocked by

None. Can start immediately.

## Acceptance criteria

- [ ] Local Linux and Windows installer fixtures cover the new identity and existing installation inputs.
- [ ] The updater retains the approved patch queue and build profile, uses the renamed GitHub repository, and has exactly one scheduler owner.
- [ ] A disposable upgrade and rollback preserve the previous qualified binary and browser profiles.
