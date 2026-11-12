# Plan 0007: Chromium StealthCDP only

State: CLOSED

## Objective and scope

Enforce the operator's Chromium StealthCDP-only requirement at the manual build
entry point and document it for future agents. Primary owns this serialized
slice. No compilation, installation, profile changes, service restart, artifact
cutover or Agent Browser source changes are included.

## Acceptance and outcome

New build arguments explicitly disable both testing flags. Before compilation,
GN resolves both flags and the script rejects anything other than false,
including existing testing outputs, without rewriting their configuration.
Local fixture tests cover new safe output, existing testing output and unknown
resolved values. Shell syntax and diff whitespace checks pass.

Starting patch source: 5e8f56a09144c59b2e1bc2679edd19a08fbe1246,
branch integration/chromium-157-repair. Chromium source is clean at
15a1e89ace187947b2a39881b45f4de992157b56 and unchanged by this slice.
Validation: `python3 -m unittest discover -s tests -p test_build_branding.py`
(3 passed), `bash -n scripts/build.sh`, `git diff --check`.
Hosted CI skipped under operator policy. Fixtures use fake GN/Ninja; no compiler
or full Chromium build was run. Actual GN query against the existing Stable156
output confirmed the expected `is_chrome_for_testing = false` output format.

Installed Agent Browser status independently reports defaultBrowserBuild
stealthcdp_chromium, executablePathSource manifest, required=true, ready=true,
Chromium 156.0.8078.73, and manifest smoke webdriver=false. Executable SHA-256:
36294494abee9f0e304793797c8ebe8c70a65814f0924abf05b21a5511d12eaa.
This is selection/manifest evidence, not a fresh browser launch or proof that
all explicit caller overrides reject Chrome for Testing. The reported recurrent
substitution remains unlocalized in Agent Browser; its runtime was not changed.

Memory disposition: forbidden for repo graph writes because this repository
has no reviewed graph group. Continuity is retained in this plan and AGENTS.md.
