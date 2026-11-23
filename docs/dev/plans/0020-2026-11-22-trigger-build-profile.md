# Select the build profile at trigger time

State: OPEN

## Current State

The weekly timer is active. The previous controller generation is still in
use by the current Chromium 158 invocation. Plan 0019 introduced two resource
profiles and a fixed selection at installation.

## Scope and acceptance

Default to automatic selection. The weekly timer and manual launcher share a
dispatcher that samples available host memory once and starts the fastest
eligible systemd worker. The worker fixes the selected profile's admission
floor, concurrency, quota and timeout for the run. Preserve explicit profile
selection, weekly timing, and the existing disk and release gates.

Exercise memory boundaries, both generated worker budgets, and the controller's
explicit profile handoff in local tests. Do not interrupt an active build.

## Local validation

Base controller 1c0c9520affdc84747085855828766a3eee0c3da. Independent review
verified the final stop-only propagation and recovery path below the build floor.
The final controller and installer tests passed with
`PYTHONPATH=tests python3 -m unittest test_install_automation test_automation`
(20 tests). Systemd verified the generated dispatcher, workers and timer in
an isolated home. The first full discovery run collected the earlier
below-floor test before the recovery-path edits landed, yielding 121 passes and
one stale expectation. The final focused run passed the updated expectation.
Hosted Actions were skipped.
