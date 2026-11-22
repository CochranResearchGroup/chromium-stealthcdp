# Weekly conservative Chromium builds

State: OPEN

## Current State

The existing updater used eight jobs, a 32 GiB floor and ceiling, a 12-hour
timeout, and daily discovery at 03:00 Central. The current Chromium 158
requeue uses that installed generation.

## Scope and acceptance

Use two jobs for compilation and dependency sync, a two-CPU quota, 16 GiB
memory admission and ceiling, and a 36-hour timeout by default. Keep the
standard eight-job profile selectable. Schedule discovery for Sundays at
03:00 America/Chicago and retain the manual service entry point. Neither
profile changes GN arguments, candidate identity, or acceptance gates.

Verify admission at the memory boundary, both resulting systemd unit profiles,
and the repository's local suite. A build and deployment require separate
runtime evidence. Preserve the active requeue.

## Validation

Base controller 36e96e4faed00a94786412a5d71d2193568b4da4. Independent
review found no blockers. The Linux/WSL run of
`python3 -m unittest discover -s tests` passed 120 tests. The installer fixture
and the final controller wiring and admission checks passed with
`PYTHONPATH=tests python3 -m unittest test_install_automation test_automation.ControllerTests.test_conservative_admission_accepts_16_gib test_automation.ControllerTests.test_cleanup_runs_after_durable_deployment_and_does_not_fail_it`.
`systemd-analyze calendar 'Sun *-*-* 03:00:00 America/Chicago'` and
`git diff --check` passed. Hosted CI was skipped. A complete build at 16 GiB
has yet to be measured.
