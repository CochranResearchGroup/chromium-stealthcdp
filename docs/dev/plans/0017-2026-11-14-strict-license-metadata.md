# Repair strict target license metadata

State: OPEN
Owner: primary Codex agent
Authority: operator requests fixing the remaining license-metadata gate; prior
PR/review/merge/deployment authorization continues. No browser replacement.

## Current State

Strict target scan on clean source39f8185e reproduces8 errors (exit1), retained
under private license-repair-20261114/. Installedcodec39b260e9 and controller
1e2aa85 remain accepted. No scan exclusions, warning suppression or artificial
Shipped:no flags are allowed. Existing license text and source headers are the
attribution authority, not invented metadata or a claim of legal entitlement.

## Scope and acceptance

Repair integrated metadata for external/dependency checkouts and Crashpad paths.
Use ordinary strict metadata parsing for every entry; missing license files and
malformed upstream metadata must still fail. All8 prior errors accounted for,
strict original target scan exits0, credits/license output contains the repaired
components after successful strict scan, focused parser/regression tests pass.
Export/replay reviewed queue against pinned4b3d0dabb base, preserve prior patch
identities; merge PR then deploy clean merged controller/queue source. Do not
rebuild Chromium or mutate installed runtime/profiles for metadata-only changes.

## Bounds and delegation

Primary sole source writer under controller.lock; read-only license_gate_check
provides exact source attribution/mapping evidence, fresh independent evaluator
reviews the final repair. Two attempts per failing unit, one consolidated
review/remediation,3h renewable window; checkpoint after scan/test/replay stages.
Operator ../src remains untouched. Use a fresh repair branch from the pinned
upstream in the managed source, sync dependencies and replay approved queue.
Preserve original commits, outputs, active/failed receipts and installed browser.


## Diagnosed and repaired

The baseline strict target command exits1 with exactly8 errors. Two Crashpad
metadata entries assume embedded standalone lss/zlib; integrated Chromium uses
existing //third_party/lss/linux_syscall_support.h and //third_party/zlib/LICENSE.
The other6 paths lack recognized parent-checkout metadata (Catapult,2Perfetto
proto roots, Chromium Rust forwarding glue, packaged Crubit and nested Marl).
The Rust entry describes only unversioned Chromium build forwarding; separate
crate metadata remains authoritative. Perfetto Chromium includes BSD proto and
Apache build headers. Full Crubit text retains LLVM exceptions AND Unicode2015
notice, verified against source and the official SPDX2015 identifier.

Fresh managed repair branch starts at pinned4b3d0dabb, dependency sync exits0,
and replayed2-patch tree equals preserved39f8185e. Source repair commit:
d689a50fd1502a7d9f6ccd432bd524e516a4c2e1. Operator ../src remains clean15a1e89.
No dependency gitlink was rewritten. Parent-owned integration README files are
used for six exact paths only when no recognized upstream README exists; normal
ParseMetadataFile/ProcessMetadata still validate everything. Existing invalid
or empty metadata, missing fallback/license and unknown paths stay fatal.
No scan exclusion, warning suppression or artificial Shipped:no added.

## Validation and review

Regression RED proves missing metadata/path failures. Final7 regression cases
pass; upstream license URL tests9, SPDX writer6 and golden integration12 pass.
The first GREEN fixture expected absolute paths but the existing parser contract
returns root-relative license paths; corrected assertions also check real file
existence. Initial integration failure was missing vpython3 on PATH, resolved by
using the existing depot_tools PATH; no golden or product behavior weakened.
Both first failures are preserved privately.

Original full strict target scan exits0 with no errors on codec GN configuration.
Credits and license-text generation exit0; all6 fallback names appear in both,
and complete LLVM/Unicode notices are present. Output digests:
credits1717ebdbc04c8e06df58318639661a15df08b7df4c95cc3290bd275006c28e20;
license text08076ea442c22b5bb8fd4cc90c47c34ff252409453e7be06fe9a37ee0ef6eb89.
Source code/README formatting after initial scan has no semantic change; frozen
source strict-scan receipt additionally binds source SHA and GN args digest.

Full base..HEAD binary patch export was reviewed. Existing2stable patch IDs match;
only new0003 is added to the maintained queue, preserving both original files
byte-for-byte. Temporary-index replay of all3 patches on pinned base reproduces
tracked source treeb3dfed6689f43f52537087e859d184da791dac98 exactly. Range-diff
shows2equal existing patches plus the new metadata repair; diff hygiene passes.

Fresh independent license_fix_review: Standards PASS, Spec PASS, zero blocking
findings. Reviewer independently reran7 regression cases, verified clean frozen
source, output digests, raw failure/pass logs and replay tree. Attribution review
was separate read-only license_gate_check. Primary adjudicates both results.
Neither reviewer performed a build, runtime change or publication.

Private license-repair-20261114/ receipts retain exact commands, source lease,
original errors, RED/first failures/GREEN, outputs, range-diff and replay proof.
The source lease process ended during the explicit turn interruption; state was
reconciled and an owned lease reacquired before further work. All source changes
were committed; no incomplete source effect was replayed blindly.

Pending: PR review/merge and clean merged controller-source installation/readback.
No new browser build or codec public release is claimed by metadata acceptance.


Final local validation:49 tests pass (7+9+6+12 upstream/metadata and3+12 repo
helper/codec cases). Existing installed browser smoke success=true and
navigator.webdriver=false is separately recorded; no rebuilt-browser claim.
Frozen full scan receipt confirms exit0 at d689a50 with codec args digestc48179af.
All source-facing checks ran native Linux/WSL with existing depot_tools; no hosted
CI. Plan remains OPEN only until source PR and merged-generation readback finish.
