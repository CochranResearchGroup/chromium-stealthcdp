# Migrate installer and updater identities

State: CLOSED

Status: locally validated

## What to build

A qualified chromiumQ installation can be upgraded and rolled back under the new package, launcher and updater identity.

## Blocked by

None. Can start immediately.

## Acceptance criteria

- [x] Local Linux and Windows installer fixtures cover the new identity and existing installation inputs.
- [x] The updater retains the approved patch queue and build profile, uses the renamed GitHub repository, and has exactly one scheduler owner.
- [x] A disposable upgrade and rollback preserve the previous qualified binary and browser profiles.

## Validation

Validated at `f3acfe0` on Linux/WSL. `PYTHONPATH=tests python3 -m unittest
discover -s tests` passed 124 tests. Shell and Node syntax checks and
`git diff --check` passed. The Windows installer fixture uses stubbed
PowerShell and WSL path translation. The updater fixture verifies the timer
handoff and pinned state preservation without writing host units.

The disposable Linux install accepted the legacy manifest and the canonical
manifest, switched to the new version, and rolled back while retaining both
versions and the profile sentinel. A smoke attempt under a fresh HOME timed
out at browser startup. The same staged binary passed CDP smoke from the
regular launcher environment with a disposable profile. Codec acceptance
passed after making cleanup wait for the owned browser session to exit.
Evidence is under `/tmp/chromiumq-named-install.nLDHkb`. Host activation
and release publication are outside this ticket.
