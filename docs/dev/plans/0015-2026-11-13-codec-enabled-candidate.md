# Codec-enabled Chromium StealthCDP candidate

State: CLOSED
Owner: primary Codex agent
Source repo: 38aa4b7e00213847ffb8bfc9e33373317ab32501
Authority: operator approved build, actual MP4 acceptance, review and promotion.

## Current State

The codec-enabled Chromium157 candidate is built, independently reviewed,
qualified and promoted into its dedicated candidate root. Actual H264 frames,
AAC PCM and WebM, active-CDP smoke and80 focused regressions pass; staged bytes
were retested successfully. Installed156.73 and updater defaults remain unchanged.
Distribution qualification remains open after upstream metadata scan failures.


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


## Checkpoint 2 | runtime stop, bounded incremental retry

Attempt1 stopped by systemd runtime limit at61,651/62,075 edges. Terminal state
failed, result=timeout, signal15; no compiler failure in terminal log. Wall
receipt39284.297 seconds differs from nominal12h service timer; retain both,
no exact clock-cause assertion. Source, clean status and original GN digest
remain verified. No browser/test executable exists yet, so no decode claim.
The original output and every receipt remain. Attempt2 is the one allowed
incremental retry, same output/source/PGO/queue/GN and resource caps, limited to
2hours rather than another12hours. This does not reset attempt count or erase
elapsed spend. No third build attempt is authorized by this packet.
Retry unit chromium-stealthcdp-codec-20261113-retry1.service; terminal evidence
codec-20261113/retry1/build-result.json. Inspect that original unit before any
follow-up; no automatic retry. Promotion remains gated by actual acceptance.


Retry invocation:04b66526a8d44303b80ac6b7035f4a48. Dry-run confirms424 remaining
steps, including media_unittests/chrome/blink_unittests links. Continuation wake
wake_intent_bf9dcc0b417e4bbc9fe31f618228737e is armed with ready monitor on the
retry1 terminal file, lifetime8h; original completion wake was delivered and
reconciled in this turn. The new wake is a distinct final-attempt event, not a
replay of the original. No browser executable exists at retry admission.
Interim memory disposition:not_durable; still-running compilation is transient,
with no terminal qualified release outcome. Source-backed continuity retained
here and in attributable private receipts.


## Checkpoint 3 | candidate qualified and staged

State transition: active -> complete (bounded build/test/staging packet).
Progress: outcome_progress. Retry2 built successfully in2460.038 seconds,
within its2h limit. Attempt1 timeout39284.297 seconds remains; cumulative recorded
wall spend41744.335 seconds, not a claim about stable-clock elapsed limits.
No third attempt. Both scheduled completion wakes delivered and were reconciled.

| Acceptance | Verified result |
| --- | --- |
| Browser | Chromium157.0.8103.78, source e71aaa2a1effe15abe00fc43fc712acc961a28d4 |
| Executable SHA256 | 39b260e9a9bf5129571aa41d916504442213ce09db2f4f8faa3067f81d516265 |
| Build configuration | Original args/queue/PGO hashes unchanged; proprietary_codecs=true, ffmpeg_branding=Chrome; is_chrome_branded=false and both testing flags=false |
| Actual H264 |64x64,10 decoded frames, completed playback |
| Independent AAC |44099 PCM samples at44100Hz,0.999977s, mono, tone RMS0.088482 |
| WebM control |64x64,10 decoded frames, completed playback |
| Active CDP | smoke success=true, navigator.webdriver=false |
| LineBreakerTest.* |43 pass,0fail/skip/notrun, including BreakWordWithReusedShapeResult |
| Selected media |37 pass,0fail/skip/notrun; FFmpegVideoDecoderTest.*, FFmpegAACBitstreamConverterTest.*, AACTest.* |
| Staged-byte acceptance | Same executable SHA, decoder H264/AAC/WebM and active-CDP smoke pass again |
| Cleanup | Both decoder test profiles removed after writers absent; fresh OS inspection confirms zero owned writers |

Independent closed-world review: PASS, zero blocking findings against the frozen
codec/source/configuration/regression criteria. Primary verified raw receipt
hashes/XML and accepted the findings. The reviewer also accepted private staging
scope despite the separate metadata-scan failure; no license eligibility claim.

Staged artifact:
/home/ecochran76/workspace.local/chromium/artifacts/chromium-stealthcdp-candidates/codec-20261113/157.0.8103.78+stealthcdp.243270639b11

Staging used the matching157 qualified patchset helper, upstream base
4b3d0dabb8250b6f152d2d85d79e7706e309d087 and queue243270639b11, not the retained
local156 queue. Source and patchset clean, manifest digests verified. Only this
dedicated candidate root's current alias changed. codec-qualification.json binds
GN/source/queue/binary identity because the original artifact name lacks GN hash.
codec-evidence/ retains decoder/smoke/XML/build receipts and failed metadata log;
codec-notices/ preserves Chromium LICENSE and FFmpeg README/CREDITS.

License metadata command: python3 tools/licenses/licenses.py scan --gn-out-dir
out/CodecCandidate-20261113 --gn-target //chrome:chrome --target-os linux.
Exit1 identifies missing upstream metadata/license entries including crashpad
zlib, perfetto generated dependency directories, Rust/crubit and swiftshader marl.
This is failed/open distribution qualification, not a codec test failure and not
repaired in this packet. No public packaging/publication, redistribution-rights
claim, Widevine/CDM integration or updater-default change.

Installed browser remains156.0.8078.73 with SHA256
36294494abee9f0e304793797c8ebe8c70a65814f0924abf05b21a5511d12eaa. No shared
platform-neutral alias, install selection, retained profile or downstream live
session changed. Local cutover is a separate explicit deployment decision; this
packet closes qualified dedicated-root staging, not installed codec adoption.

Memory disposition: unavailable for a project-cloud write because no reviewed
Chromium Graphiti group is configured; durable outcome/provenance retained here
and in the staged evidence. No speculative destination or duplicate memory write.
