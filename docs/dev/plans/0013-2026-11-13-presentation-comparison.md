# Controlled desktop presentation comparison

State: CLOSED
Owner: primary agent
Date: 2026-11-13

## Objective and Current State

Operator authorized the experiment proposed in the stock Chrome research note.
Compare existing stock Chrome, manual StealthCDP and managed StealthCDP using
synthetic local content and fresh disposable profiles. No production settings,
build, install, retained profile or unrelated browser changes are authorized.

Reference Chrome is 153.0.8010.52; installed StealthCDP is 156.0.8078.73.
Version differences confound cross-product attribution; manual/managed
StealthCDP use identical bytes. Current Agent Browser source is 24bb970c84e5,
different from the earlier deployment; pin its actual executable hash.

## Execution and bounds

Primary owns one sequential harness and the final judgment. No worker required.
At most two measurements per mode, one host, one controlled origin, 30-minute
execution budget. Preserve first failures; no blind task-open retries. Use fresh
MCP stdio and exact returned task IDs. Each manual browser uses its own profile
and process custody; terminate only that verified owned process after reporting.

The fixture uses loopback HTTP, a potentially trustworthy browser context,
rather than install certificates or change trust flags. Assert secure-context
availability and capture initial/negotiated Client Hints. HTTPS transport and
TLS fingerprint equivalence remain unmeasured. Two managed payloads are retained from the initial and exact-window-check
attempts. Both tasks closed with PID and profile-writer absence. Managed display
identity was not exposed in /proc and its exact PID had no X window on :0.
Stop display recovery; capture two manual rows per browser on the verified :0
server, with display differences explicit. No further managed opens are needed.
The Xvfb setup failure started no browser and left no owned server. A fixture
server exception was reconciled using the same task key; close was fenced by
idle retirement, and a fresh OS scan proves no writers for that exact profile.
All failed receipts remain private. The final harness preflights fixture HTTP
and script compilation before browser effects; no shared socket directory repair.
This bounds the remaining unit to one manual-only run, with no additional retry.

Capture browser/header/worker identity, viewport/fonts/GPU, media support and
actual synthetic playback, permissions, and script-opened popup behavior.
Use only synthetic content; do not export cookies, credentials or private pages.
Close exact tasks; verify own PIDs/profile writers gone and preserve peers.

## Acceptance and exit

Produce a repeatable harness, private raw receipts, and a compact cited results
note distinguishing observed, intentional, version/environment-confounded and
unmeasured differences. Stop after the comparison; select a demonstrated next
repair without modifying production launch settings or adding engine patches.
Report technical gates honestly if a row cannot complete. Validate harness
syntax, result completeness and exact cleanup, then reconcile this plan.


## Final evidence

Six selected payloads complete the bounded comparison: two managed reports
retained from display-assertion failures, and four passing manual rows. The
[results](../notes/0004-2026-11-13-presentation-comparison-results.md) retain
version/display confounders, all setup/fixture failures, exact cleanup, and
the recommended popup-policy repair. Node syntax, fixture preflight, selected
repeat/identity assertions and fresh OS writer-absence checks pass. One
interrupted close was fenced; exact retirement readback shows no active task
or browser and ended history. No production modification was made.
