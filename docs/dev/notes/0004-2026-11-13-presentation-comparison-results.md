# Desktop presentation comparison results

Date: 2026-11-13
Status: bounded experiment complete; production configuration unchanged.

## Outcome

The most immediately actionable launcher difference is unsolicited popup
behavior. Both managed StealthCDP samples allowed a script-opened window;
both manual StealthCDP samples and both stock Chrome samples blocked it.
The measured managed command line includes `--disable-popup-blocking`,
consistent with the difference. This is a strong candidate for a focused
launcher repair, not an isolated flag-ablation experiment proving causation.

The clearest build-capability gap is H.264/AAC MP4 playback: both StealthCDP
modes fail while the existing Chrome reference succeeds. Identity spoofing
would not supply that missing decoder capability. No engine patch, build,
install or production launcher change was made by this experiment.

See the [sanitized machine-readable results](0004-2026-11-13-presentation-comparison-results.json),
[research rationale](0003-2026-11-13-stock-chrome-presentation-research.md), and
[closed execution plan](../plans/0013-2026-11-13-presentation-comparison.md).

## Method and identities

The primary ran all measurements and verified cleanup. Six selected synthetic
payloads cover two observations per mode. The two managed payloads were retained
from runs that completed page measurement but subsequently failed a display
assertion; they are not two successful end-to-end harness runs. The four manual
rows completed together in the final manual-only run.

All selected runs used identical executable hashes:

| Executable | Version/source | SHA256 |
| --- | --- | --- |
| Existing Google Chrome reference | 153.0.8010.52 | `0ba9d6c54dbc1a46dfaa5f95d5975bc9b963030c8647880f5b6a537f8af7d2e8` |
| Chromium StealthCDP | 156.0.8078.73 | `36294494abee9f0e304793797c8ebe8c70a65814f0924abf05b21a5511d12eaa` |
| Installed Agent Browser | source `24bb970c84e5d1d98fc9e7c0f50d88e1c1d74538` | `934f03443c98ccc92db21ea9f43c6a42148c81c3a7fe826eb472b3ee1bc335c5` |

Chrome 153 versus Chromium 156 is an explicit version confound. No Chrome for
Testing or replacement reference was downloaded, built or installed. Manual
browsers had fresh profiles, no debugging port, and only profile selection,
first-run/default-browser-check suppression, new-window and the local URL as
explicit arguments. Managed rows used the ordinary disposable MCP workflow.

The fixture used loopback HTTP; all six pages reported a secure context.
It captured initial requests and negotiated Client Hints through an echo
request, page/frame/worker identity, graphics availability, font-width samples,
permission queries and real playback of silent 64x64 test clips. No private
website, login, cookies, account, challenge or detector service was used.

## Observed comparison

Every discrete outcome below repeated in both selected observations per mode.

| Measurement | Stock Chrome | Manual StealthCDP | Managed StealthCDP | Interpretation |
| --- | --- | --- | --- | --- |
| `navigator.webdriver` | false | false | false | Existing downstream behavior retained; not proof of general parity |
| H.264/AAC reported support | probably | empty | empty | Build/media gap, also present without Agent Browser |
| Actual silent H.264/AAC MP4 | decoded, 6 frames | failed, media error 4 | failed, media error 4 | Real playback difference, not just a support string |
| Actual VP9/Opus WebM | decoded, 6 frames | decoded, 6 frames | decoded, 6 frames | Shared tested capability |
| Script-opened popup, no gesture | blocked | blocked | opened, then fixture closed it | Managed behavior differs; explicit popup flag is a repair candidate |
| WebGL and WebGPU | unavailable | unavailable | unavailable | No GPU-specific attribution established |
| PDF viewer/plugin list | enabled, 5 entries | enabled, same 5 | enabled, same 5 | No plugin-list shim justified |
| Five queried permissions | prompt | prompt | prompt | Geolocation, notifications, camera, microphone, clipboard-read |
| Page/worker/frame identity | internally consistent | internally consistent | internally consistent | Compared corresponding UA/platform/language/hardware/UAData fields |
| Manual/managed StealthCDP headers and identity | different product/version reference | equal to managed | equal to manual | No measured UA/Client-Hints repair justified |

Chrome advertises its Google Chrome and Chromium brands; StealthCDP advertises
Chromium, with version-derived arbitrary brand entries. These are coherent
product differences, not evidence that a Google Chrome brand should be added.
The sampled Accept-Language, locale, timezone and six named-font width probes
matched across modes. Width equality does not enumerate installed fonts or
establish identical font rendering for every page.

## Limits that matter

- Managed DISPLAY was unavailable in `/proc`, and its PID had no matching X
  window on the manually verified `:0` server. Manual rows used the same
  1024x768 display; managed samples reported 1440x900. Graphics and window
  differences remain environment-confounded. The managed command line disables
  GPU/compositing, but all three modes lacked graphics APIs in this experiment.
- Initial managed geometry was unstable: one sample reported outer dimensions
  zero. Some generic-font measurements also varied. Exclude those from equality
  or detector claims; a follow-up needs a settled window/font readiness barrier.
- EME accepted the requested CENC/H.264 configuration in stock Chrome and
  rejected it in both StealthCDP modes, for both Widevine and ClearKey. This
  does **not** establish missing CDMs: missing H.264 support can invalidate the
  same configuration. No protected media or license acquisition was attempted.
- There was no HTTPS/TLS fingerprint test, same-version Chrome reference,
  beforeunload/repost dialog test, real-provider acceptance or general
  automation-detection score. Repeats demonstrate these selected outcomes,
  not a platform matrix or comprehensive stock-Chrome equivalence.

## Failures and cleanup

Retained private attempts, in order:

1. Initial managed payload succeeded; the harness wrongly required DISPLAY
   to remain visible in `/proc`. Scoped close succeeded and PID/writers exited.
2. Dedicated Xvfb setup could not allocate sockets in the shared X socket
   directory. It launched no browser and left no owned Xvfb process. Shared
   socket permissions and existing display services were not changed.
3. A harness edit accidentally removed the header-selector function, causing a
   fixture server exception. The original task was reconciled with its same
   task key. Close returned an idle-retirement fence; later exact readback
   showed no active task/browser, ended history and no profile writers.
4. Fixture HTTP and script preflight passed; the exact-PID display assertion
   failed after the second selected managed payload. Scoped close succeeded
   and PID/writers exited. No more managed opens were performed.
5. The bounded manual-only run passed all four rows. Only exact verified owned
   browser processes received SIGTERM. All four PIDs/profile writers exited;
   only those four run-owned temporary manual profile directories were removed.

Fresh OS inspection found zero writers for all experiment profile paths.
No unrelated browser/daemon/compiler was terminated, and no retained profile
was copied, cleared or migrated. The fixture servers ended. Original receipts,
payloads, logs and media remain under user-scoped local state, outside Git:
`~/.local/state/chromium-stealthcdp/presentation-20261113*` and the sibling
`presentation-comparison-20261113-{aggregate,validation}.json` files.
The published summary contains no task IDs, profile contents or private URLs.

## Reproduction and validation

The reusable [harness](../../../scripts/presentation-comparison.mjs) requires
Node, a verified local X display, the existing binaries and an existing
`smoke-utils.js` MCP helper. It does not install these dependencies. A fresh
artifact directory is required; uncertain runs cannot be overwritten.

Generate local fixtures using FFmpeg: 0.6 seconds of black 64x64 video at
10fps with silent stereo audio. The experiment used libx264 baseline/yuv420p
plus AAC in MP4, and libvpx-vp9 plus libopus in WebM, one encoder thread.
Exact generated-byte hashes are retained in the private validation receipt;
new FFmpeg versions need not produce identical container bytes.

```sh
node scripts/presentation-comparison.mjs \
  --artifact-root /absolute/private/fresh-run \
  --mcp-helper /absolute/agent-browser/scripts/smoke-utils.js \
  --stock /opt/google/chrome/chrome \
  --stealth /absolute/stealthcdp/chrome-linux/chrome \
  --agent /absolute/installed/agent-browser \
  --display :0
```

Place `sample.mp4` and `sample.webm` in the artifact directory first. Use
`--modes manual-stealth,stock-chrome` for the manual-only unit. The default
selects all three modes, two iterations each; a display mismatch is recorded,
not concealed. Do not interpret new runs as directly comparable if executable,
fixture or environment identities change.

Validation: Node syntax check and fixture HTTP/script preflight pass. A final
`--preflight-only true` run also passes valid report ingestion and invalid
report-path/origin guard checks with zero browser launches. Independent
primary assertions pass for six secure-context payloads, page/worker/frame
identity consistency, repeated selected fields, identical manual/managed
StealthCDP identity/headers, six named-font width samples, executable identity
stability and exact cleanup. No production-code suite was claimed or needed.

## Next repair

Recommend a small Agent Browser change first: restore stock popup blocking for
ordinary managed launches, with a public workflow regression using this local
fixture. Preserve any explicit workflow requirement through deliberate policy,
not a blanket default. This experiment does not implement that change.

Next, qualify a supported H.264/AAC build configuration and actual decoding;
resolve applicable component/distribution requirements before adding codecs.
Then repeat EME with a codec configuration actually supported by the candidate.
Defer identity spoofing and additional graphics/engine stealth patches: the
present evidence does not justify them.

Memory disposition: forbidden. No reviewed Chromium project Graphiti write
route is defined; the source-backed outcome remains in this repository.
