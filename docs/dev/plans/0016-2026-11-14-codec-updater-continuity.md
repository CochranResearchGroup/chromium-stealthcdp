# Codec updater continuity and maintained delivery

State: CLOSED
Owner: primary Codex agent
Authority: operator explicitly requests codec updater changes and PR/review/merge/deployment.
Base: upstream/main144974f; prior local integration814c364 preserved and merged.

## Current State

PR14 is merged asd546875f834c35aee4e1d6972d1eb7632bd40e7a. The clean merged
controller generation is installed; its config source_repo and current selector
match that merge. Codec defaults/recipe, dependency PATH and enabled timer are
verified. Installed39b260e9 browser and managed host892794 remain unchanged.
The pending local branch backlog is integrated into main through the reviewed
PR, including source/test helpers and qualified candidate/cutover history.
Actual public codec distribution remains gated by unresolved metadata errors.


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


## Controller adoption | 2026-11-14

PR: https://github.com/CochranResearchGroup/chromium-stealthcdp/pull/14
Reviewed head84350776f9f9e8023e13febd7414f58a69b1dbfd; merge
d546875f834c35aee4e1d6972d1eb7632bd40e7a. Local qualification status posted;
no paid/hosted CI run.118 tests passed across102 normal and16 separately completed
retention cases; real GN, actual Debian fixture and disposable managedMCP proof
passed. Independent Standards/Spec review, accepted F1 remediation and precompile
metadata guard verification are recorded; authors and final reviewer separated.
No force push or rewrite of old branch/release history.

Installed via scripts/install-automation.py under controller.lock from the clean
merge. Current immutable generation and config source_repo both resolve to that
SHA. GN arguments SHA c48179af48c83713ef789b90b60a61454588a91925e3a92ca4cbf53903020cc4;
recipe343b4878b7d81bda2f2026ce708bfd8489668632c7e073dedec6fc091646f512.
Installed controller --help loads successfully. Daily timer active and enabled;
service retains32GiB/no-swap/eightCPU/12h caps and includes the required local
fixture encoder PATH. No update run, browser compile, codec package publication
or Slack notification was triggered by controller installation.

Before/after readbacks retain installed browser SHA39b260e9a9bf5129571aa41d916504442213ce09db2f4f8faa3067f81d516265
and runtime hostPID892794 unchanged. Existing profiles, browser roots, old
artifacts/controller generations and failed receipts are preserved. Private
codec-updater-20261114/ evidence binds source, commands, results, GN, actualMCP,
packaging, timeouts and controller adoption. This is native Linux/WSL validation,
not a hosted or full cross-platform/browser-rebuild claim.

The following documentation-only closeout may advance main. Its controller code
closure must equal d546875 before a final generation readback; no repeat browser
build/tests are required for unchanged executable/controller inputs.
Memory disposition: unavailable for project-cloud write because no reviewed
Chromium group is configured. This source-backed packet retains durable outcome.
