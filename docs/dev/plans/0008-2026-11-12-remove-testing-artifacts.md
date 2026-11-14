# Plan 0008: Remove Chrome for Testing artifacts

State: OPEN

## Objective and scope

Remove positively identified Chrome for Testing build candidates and downloaded
artifacts. Primary owns serialized inventory, process checks, removal and final
verification. Preserve Chromium StealthCDP, all profiles, source and active peers.
No service restart or browser task termination without resolving the active-task
choice with the operator. No builds or hosted CI are needed.

## Current State

Patch repository starts clean at 62568acea32f306ca09819db9ae28ba6b6679931;
Chromium source starts clean at 15a1e89ace187947b2a39881b45f4de992157b56.
Twenty downloaded browser directories report Google Chrome for Testing through
`chrome --version`. Fresh /proc executable inspection identifies live processes
using versions 157.0.8103.50 and 157.0.8103.78. Remove only inactive confirmed
copies first; operator choice on live copies remains pending. Existing Chromium
outputs and StealthCDP manifests checked so far identify Chromium and are retained.
Private removal receipt belongs outside Git under the user's local state.

## Acceptance

Each removal has positive testing-brand identification and a fresh no-live-use
check. Retained StealthCDP executable hash and current aliases remain unchanged.
Report removed versions, reclaimed allocation, remaining live copies and any
uninspected artifacts explicitly. Final process inspection is required.

## Execution evidence

Removed 18 positively identified inactive downloaded CfT directories from the
user browser store. Files occupied 7,454,232,576 allocated bytes (6.94 GiB).
Private receipt: ~/.local/state/chromium-stealthcdp/cleanup-20261112.json.
Fresh final inventory contains only chrome-157.0.8103.50 and
chrome-157.0.8103.78; final process census observes 17 and 90 processes,
respectively. Operator choice about closing those active tasks is pending;
this plan remains OPEN. No process was terminated and no profile was touched.

Artifact-root inventory checked 13 version-bearing manifests and 10 Linux
binaries: all identify Chromium, zero testing binaries. Five packaged archives
have StealthCDP names and are preserved; archive payloads and Windows executable
branding were not requalified. Existing Linux build-output binaries identify
Chromium; source/out build directories are preserved.

Installed StealthCDP SHA-256 remains
36294494abee9f0e304793797c8ebe8c70a65814f0924abf05b21a5511d12eaa.
Shared artifact alias remains 156.0.8078.47+stealthcdp.4b864442a8fd.
Chromium source status remains clean at the starting SHA. No compilation,
installation, tests or hosted CI were needed for this artifact-only cleanup.

Memory disposition: forbidden for repo graph writes because no reviewed repo
group exists. Current filesystem evidence was sufficient; no Graphiti discovery
was needed for this cleanup.
