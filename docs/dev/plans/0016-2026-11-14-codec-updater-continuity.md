# Codec updater continuity and maintained delivery

State: OPEN
Owner: primary Codex agent
Authority: operator explicitly requests codec updater changes and PR/review/merge/deployment.
Base: upstream/main144974f; prior local integration814c364 preserved and merged.

## Current State

Installed codec browser39b260e9 is accepted. Controller remains pinned to old
1a7c2d4 code with no codec defaults; run/baseline/release identities omit GN.
Local research, actual decoder harness, CFT build guard and qualification records
need PR integration alongside the narrowly scoped updater repair. Current main's
157 patch queue/pin must survive. Distribution metadata scan failed previously;
private installation acceptance does not qualify automatic public publication.

## Acceptance and scope

Explicit H264/AAC GN configuration, all browser/testing branding false; actual
decoder checks and resolved GN values before compilation, original/staged bytes
qualified. Build recipe identity participates in run, baseline, candidate,
artifact/package/tag naming and resume checks so old noncodec receipts cannot
skip or collide with codec builds. Preserve existing releases/receipts/profiles.
Reconcile onto current main, use PR and serial Standards/Spec plus independent
closed-world review; all applicable tests local, no paid/hosted CI. Deploy clean
merged controller generation and verify actual source/config/readback. Do not
start another full browser build merely to qualify controller installation.
Keep actual publication eligibility separate; no inferred codec distribution
clearance from local decoder success or failed metadata scan.

## Bounds and ownership

Primary implementation writer; read-only codec_acceptance_review audits identity,
acceptance and publication boundaries. One consolidated review/remediation pass,
two attempts per failing unit,3h implementation/checkpoint window; no new
Chromium compile or retained-profile migration. Original candidate evidence and
all prior failed receipts retained. Public codec release remains unqualified
unless its concrete distribution gate is satisfied. No provider messages.


## Source and validation checkpoint

Fresh upstream/main144974f merged into the maintained branch without conflicts;
its157 patch queue/pin and releases retained. Pending local research, actual
codec harness, CFT build guard and source-backed candidate/install history are
included for review, rather than staying hidden in a local-only branch.

Core TDD RED: seven recipe/branding/publication cases found identical run IDs,
missing recipe APIs and untyped publication lookup failures. GREEN follows
recipe-aware implementation. Additional negative decoder and actual Debian
packaging/notice retention tests pass. Actual GN-only generation on39f8185e
resolves proprietary codecs=true, FFmpeg Chrome, Chromium/testing branding false;
args SHA c48179af... matches accepted installed codec bytes' configuration.
Recipe SHA343b4878b7d81bda2f2026ce708bfd8489668632c7e073dedec6fc091646f512
covers GN plus actual decoder harness. No browser compilation was invoked.

Primary's initial all-suite run encountered an obsolete no-op fixture without
recipe identity, entering source preparation unexpectedly. Exact owned test/Git
processes were stopped; fixture now explicitly represents qualified baseline,
with a separate regression proving legacy baseline cannot suppress codec work.
A later all-suite timeout at180s was due to slow unchanged retention fixtures.
Retention was rerun separately:16 pass in279.313s, with the first timeout retained.
No passing full-suite claim is made from a timed-out invocation.

Independent source review: initial Standards/Spec PASS. Primary live preflight
then found accepted F1: global CLI --state parsing prevents the intended service
job filter. Concrete source confirmed it; the complete-unfiltered-snapshot
workaround preserves fail-closed inventory semantics. Guard tests cover unknown,
malformed, truncated and active inventories; this is the single consolidated
remediation, followed by F1-only review. The earlier flattened /proc argv root
parser issue was corrected with raw-byte regression coverage before final review.

New managed-MCP acceptance script ran against installed39b260e9 bytes: success,
matching executable SHA and scoped-close/profile-writers-gone. No actual shared
host restart or retained-browser mutation was required during this controller
packet. Independent author agent owns only deployment helper/script/tests;
primary adjudicates and fresh reviewer is separate from both source writers.

Publication remains gated by real target license metadata scan. Missing metadata
was not relabeled passed and no operator rights determination is inferred. Future
runs can stop before packages/source PR/publication/deployment while preserving
current codec installation. Controller source deployment itself is separately
authorized and does not trigger another browser build or publish existing bytes.


## Final pre-integration evidence

102 Python tests pass in34.967s, plus16 independently completed unchanged
retention tests in279.313s. Actual Debian version includes recipe and preserves
codec notices/evidence; real GN and managedMCP checks pass. Bash/Node/Python
syntax and diff hygiene pass. No hosted CI. Final independent Standards/Spec
review has zero blockers; F1-only verification and the added precompile metadata
failure RED/GREEN were independently accepted. Metadata scan is verified by a
separate source reader to be target-aware and strict; credits generation is not
an equivalent gate. Existing missing metadata is not bypassed.

Precompile metadata failure is now checked immediately after resolved GN values,
so known unpublishable inputs stop before a full compile. Final qualification
repeats the scan after exact-byte tests. Source PR and immutable controller
installation remain the only outstanding steps for this packet.
