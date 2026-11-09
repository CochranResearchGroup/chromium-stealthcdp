# Chromium Patch Boundary

Date: 2026-11-09

## Decision

Keep the Chromium patchset small. Most anti-anti-bot and site compatibility
work belongs in agent-browser site policy, profile management, launch mode,
streaming, and input behavior.

Chromium patches should only cover browser-internal signals that agent-browser
cannot fix from outside without creating new detectable inconsistencies.

## Current Patch

Keep the first patch:

```text
patches/0001-Make-navigator.webdriver-non-advertising.patch
```

It changes `Navigator::webdriver()` so external websites do not receive the
explicit automation signal from headless, CDP pipe, `remote-debugging-port=0`,
`enable-automation`, or CDP automation override paths.

## Upstream Compatibility Repairs

The original Facebook posts-search DCHECK diagnosed on Chromium 150 has an
upstream repair. Chromium CL 7992797, commit
`de949449a7fc4df4551492407a65fc3d63015c42` ("[line-break] Relax the DCHECK for
BreakText results"), removed an invalid `LineBreaker` ordering DCHECK while
preserving the existing failed-break restoration path. It also added
`external/wpt/css/css-text/crashtests/line-breaker-overflow-crash.html`.

That ordering-DCHECK repair is distinct from the stale shape-result defect
covered by downstream patch 0002. Chromium `157.0.8103.38` at pinned base
`a733b5afbb3ba618844ff8876b89ad1a774b2f18` now clears stale shaping under
`LineBreakerClearShapeResultOnOverflow`, a feature marked `stable`. Its new
context broke replay of the old patch 0002.

The repaired queue retains two patches: private webdriver behavior and the
downstream unconditional stale-shape invariant with the existing seeded
`BreakWordWithReusedShapeResult` regression and DCHECK consistency check.
Patch 0002 replaces the upstream feature-guarded clear with unconditional
clearing, preserving downstream behavior even with runtime feature overrides.
Its testing hook and regression remain unchanged. This is a source-level
repair proposal; Chromium compilation, focused DCHECK-enabled tests and CDP
smoke must qualify the candidate before release or activation. See
[Plan 0011](dev/plans/0011-2026-11-09-chromium-157-patch-repair.md).
Do not add a duplicate ordering-DCHECK backport.

Upstream review: <https://chromium-review.googlesource.com/c/chromium/src/+/7992797>

## Chromium-Level Work To Consider

Only request additional Chromium patches after a source-backed assessment shows
a narrow, page-observable browser-internal side channel.

Candidates for assessment:

- DevTools or CDP attachment side channels beyond `navigator.webdriver`.
- Page-observable protocol serialization differences triggered by DevTools
  inspection or automation overrides.
- Build identity surfaces such as user agent, client hints, product strings,
  and related brand/version metadata, but only if the full identity remains
  internally coherent.

## Non-Goals

Do not add broad fingerprint spoofing patches in this repo for:

- WebGL
- Canvas
- Audio
- fonts
- plugins
- hardware
- permissions
- media devices
- timezone
- locale
- arbitrary viewport or device emulation

These surfaces are high maintenance and easy to make inconsistent. Prefer
agent-browser policy and profile management unless Chromium is the only layer
that can fix a proven internal contradiction.

## Agent-Browser Boundary

Agent-browser should remain responsible for:

- site policy and access posture
- managed profiles and account state
- headless versus headed launch selection
- stream viewer and human intervention UX
- pacing, input behavior, and action serialization
- service-owned browser lifecycle and CDP connection management

The patched Chromium binary is an engine option, not a replacement for
agent-browser's control plane.
