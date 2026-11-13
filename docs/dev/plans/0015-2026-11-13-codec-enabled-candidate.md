# Codec-enabled Chromium StealthCDP candidate

State: OPEN
Owner: primary Codex agent
Source repo: 38aa4b7e00213847ffb8bfc9e33373317ab32501
Authority: operator approved build, actual MP4 acceptance, review and promotion.

## Current State

Configuration-only qualification is complete in note0005. Full compilation,
actual H264 and independent AAC decoding, exact-byte smoke/regressions and
candidate staging remain. Installed browser and automatic updater are unchanged.

## Scope and acceptance

Use clean qualified source e71aaa2a1effe15abe00fc43fc712acc961a28d4 on upstream
4b3d0dabb8250b6f152d2d85d79e7706e309d087; retained replay is range-diff plus
ordered patch-id equality. Preserve that queue and PGO input. New output
out/CodecCandidate-20261113 only. Explicit proprietary_codecs=true and
ffmpeg_branding="Chrome", is_chrome_branded=false, both Chrome-for-Testing
flags=false, resolved before compilation. No Chrome assets, CFT, Widevine,
profile mutation or updater default change.

Acceptance: actual H264 decoded frames, independent AAC decoded PCM from a
synthetic tone, WebM control; active-CDP smoke success=true and webdriver=false;
LineBreakerTest.* including retained regression passes with no skips; selected
FFmpeg media tests. Bind source, queue, GN args, fixture and executable hashes.
Stage under a dedicated candidate root because promotion helper updates that
root's current alias. Recheck staged bytes. Local install/cutover only after
accepted evidence; no public release or distribution entitlement inferred.

## Execution bounds

One build attempt, at most one diagnosed repair/retry. Maximum12 hours per
build within the existing controller resource envelope: CPUQuota800%,
MemoryMax32G, MemorySwapMax0, Nice10, four compiler jobs. Stop if disk free falls
below80GiB. No global caches or previous outputs cleared. Hold controller.lock
for source ownership; failure to acquire stops before mutation. Build supervisor
writes heartbeat and terminal receipt, verifies source/GN identities before and
after compilation. No automatic retry. Durable checkpoint at each stage.

## Delegation and review

Primary owns source/build/harness/integration. Independent read-only agent
codec_acceptance_review completed bounded review: existing comparison does not
assert decode success and muted MP4 does not prove AAC. Accepted blocking gaps:
assert real video frames and independent AAC PCM; pin candidate executable, not
managed installed selection; preserve GN hash sidecar because runtime artifact
name is only version+queue. Re-run smoke/media on staged bytes. No additional
broad presentation research. Final closed-world evaluator checks these criteria.

## Continuation

Private evidence root ~/.local/state/chromium-stealthcdp/codec-20261113.
Unit chromium-stealthcdp-codec-20261113.service; runner/build-result.json is the
terminal trigger. On continuation inspect exact unit/result before any retry.
Retain failed receipts. Build success alone cannot authorize or prove promotion.


## Checkpoint 1 | compilation active

State transition: ready -> active. Progress: blocker_reduction and outcome_progress.
Supervisor invocation 1c80db5c1d4e496fa5a59b5117cd38f6 owns the controller lock.
GN generation passed; resolved proprietary codecs=true, FFmpeg configuration
Chrome, all three browser/testing branding flags=false. Args SHA256
c48179af48c83713ef789b90b60a61454588a91925e3a92ca4cbf53903020cc4;
queue SHA256 243270639b115d74420d98a85e45344b6086e6b1bb1bfd80717a32c6148bd215.
Actual cgroup readback confirms32GiB, zero swap, eight CPU quota. Four compiler
jobs build chrome, blink_unittests and media_unittests. No installed selection,
previous output, updater defaults or retained profiles changed.

New scripts/codec-acceptance.mjs asserts actual browser APIs via active CDP:
64x64 video frames for H264/WebM, AAC-only decoded PCM duration/channels/samples
and nonzero tone RMS. Baseline RED on installed StealthCDP156.73 reports H264
media error4, AAC decode failure, WebM10frames, webdriver=false. Exit1 is the
expected capability failure; exact owned profile writers gone and profile removed.
Private fixture hashes, executable hash, full report and logs retained. This
matches the pre-existing comparison gap; no candidate GREEN is claimed.

Continuation wake wake_intent_3f2501454b6340f8b42921918231b132 is armed with a
ready monitor, persistent24h lifetime and exact terminal file predicate. This is
schedule admission, not delivery proof. Native CLI reconcile did not find this
lifecycle intent in its default root; direct canonical retained record confirms
file_exists predicate, same thread and current pending/zero attempts. Do not
submit a duplicate wake. Original tool receipt is saved privately.

Next: read exact build result and source/GN hashes, then decoder GREEN, upstream
regressions, staged-byte verification and closed-world review. If result is
absent inspect original unit/heartbeat; do not start a second build. Two-attempt
bound is cumulative. Primary remains critical path owner.


Independent closed-world harness review: PASS, zero blocking findings; reviewed
SHA256 8c55e6e4309b39401ca366aa9543dee42b1da86f97ea5c23f6e7d0c62b8dde8f.
Primary adjudication accepts the result only for the harness gaps; staged-byte
identity, fresh OS readback and actual candidate GREEN remain outstanding.
Baseline command: node scripts/codec-acceptance.mjs --chrome
/home/ecochran76/.local/share/chromium-stealthcdp/current/chrome-linux/chrome
--artifact-root /home/ecochran76/.local/state/chromium-stealthcdp/codec-20261113/baseline-red.
Result: expected exit1; independent AAC failure and passing WebM retained.
Memory disposition for this interim checkpoint: not_durable; running build state
is transient and no terminal candidate outcome is qualified. Rich restart
continuity is this committed plan and private attributable receipts.
