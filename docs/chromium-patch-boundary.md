# Chromium Patch Boundary

Date: 2026-05-12

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

The Facebook posts-search crash diagnosed on Chromium 150 does not require a
downstream patch on the current base. Chromium CL 7992797, commit
`de949449a7fc4df4551492407a65fc3d63015c42` ("[line-break] Relax the DCHECK for
BreakText results"), removed an invalid `LineBreaker` ordering DCHECK while
preserving the existing failed-break restoration path. It also added
`external/wpt/css/css-text/crashtests/line-breaker-overflow-crash.html`.

Chromium `153.0.8003.0` at
`b84d5f5c55a43d2f7778cfbc1996d3b835296d1c` contains that accepted upstream
repair. Keep the downstream queue at one patch; do not add a duplicate
line-breaker backport while this repair and its regression test remain present.

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
