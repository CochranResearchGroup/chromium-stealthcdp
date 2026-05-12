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
