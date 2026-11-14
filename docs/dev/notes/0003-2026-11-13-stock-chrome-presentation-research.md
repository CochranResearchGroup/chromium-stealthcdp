# Stock Chrome presentation within Chromium StealthCDP

Date: 2026-11-13
Status: bounded research complete; recommendations are not implemented.

## Research contract

Question: how can Linux desktop Chromium StealthCDP behave more like ordinary
desktop Chrome, while retaining the StealthCDP executable and avoiding Chrome
for Testing entirely?

Allowed sources: Chromium source and project documentation, Chrome developer
documentation, DevTools Protocol definitions, standards and first-party Widevine
documentation. Stop after identifying the principal actionable differences,
ranking changes, and specifying a bounded comparison. This is source research,
not an empirical fingerprint audit or a claim of undetectability. No browser,
profile, build, updater, deployment or provider state is changed.

The primary investigated identity/launch behavior. One background researcher
investigated branding/media/services; the primary checked the cited primary
sources. There was no delegated implementation or independent runtime test.

## Recommendation

First measure and reduce unnecessary departures from stock Chromium defaults
in the launcher and desktop environment. Preserve coherent native browser
identity and real capabilities. Defer additional engine patches until a
reproducible difference demonstrates their value. This is an engineering
recommendation, not evidence that a particular site will accept automation.

There are three distinct targets: native browser UI, web-visible capability and
identity, and site-side risk decisions. Improving the first two does not prove
the third. W3C guidance identifies request/network information and active probes
such as fonts, window dimensions and graphics as fingerprinting surfaces, and
explicitly describes technical mitigations as incomplete. [S1]

## Local baseline and limits

Source identities inspected:

- Patch/controller repository: `17a16bc89dfa178ffe3e95c8a3f23a40a2b9ddfa`,
  initially clean on `integration/chromium-157-repair`.
- Retained sibling Chromium: `15a1e89ace187947b2a39881b45f4de992157b56`,
  initially clean on the retained 156 source branch.
- Agent Browser launcher: read the immutable Git object at merged repair
  `ea9bcb186b41209b2887a871aaf38d7ef6f3115f`, not the canonical checkout's
  older HEAD. [L1]

The queue's identity-related patch changes the native `Navigator::webdriver()`
getter to return false. It does not patch Client Hints, codecs, GPU output,
fonts, permissions or network behavior. [L2] The controller sets official,
non-debug, non-component builds with both testing flags false and synchronizes
browser/V8 optimization profiles. Those are build/performance facts, not a
web-identity equivalence guarantee. [L3]

The launcher's ordinary branch includes disabled background networking,
component updates, popup blocking, repost prompts, sync and Translate, plus
forced NetworkService features. Its headed manual-login branch has a much
smaller initial switch list. Unless real keychain use is selected, the launcher
adds a basic password store and, outside manual login, mock-keychain. Headless
launches without extensions add unified headless mode and an unsafe SwiftShader
opt-in. These are source-level branches, not observations that every installed
task uses every switch. The SwiftShader opt-in alone does not prove actual
software rendering. [L1]

No same-version stock Chrome comparison, current per-task flag inventory,
resolved codec/CDM inventory, GPU trace or third-party detector test was run.
Upstream `main` documentation/source below was read on this date; implementation
proposals must be checked against the exact release being built.

## Ranked improvements

| Priority | Proposed work | Why it matters and acceptance |
| --- | --- | --- |
| P0 | Establish a controlled comparison before another patch | Compare unmodified same-platform desktop Chrome, StealthCDP opened manually, and the same StealthCDP through Agent Browser. Separate engine/build differences from launcher/CDP effects. Use an already available authorized reference, with no Chrome for Testing download or substitution. |
| P1 | Give ordinary managed launches a minimal, justified switch set | Test removal of unnecessary feature and interaction overrides individually, especially popup/repost changes, forced network features and disabled component/background behavior. Preserve lifecycle, profile ownership and remote-control requirements. Do not simply reuse manual-login mode: it has a different operational contract. [L1] |
| P1 | Use a coherent real desktop environment | For desktop presentation, qualify headed mode, actual window/viewport/DPR, fonts, locale, timezone and real GPU support on the intended host. Prefer fixing actual platform configuration over reporting invented hardware or OS values. These are proposed measurement dimensions, not proven current mismatches. [S1, S2, S3] |
| P1 | Audit identity as one bundle | Compare request UA/Client Hints with JavaScript UA/platform/UAData, including full versions and worker contexts. Keep native defaults unless an observed compatibility problem justifies an explicit, tested override. A UA-string-only edit is insufficient. [S4, S5, S6] |
| P2 | Qualify real media compatibility | Inventory resolved codec options and actual playback; compare `canPlayType`, MediaCapabilities and EME results with the reference. Investigate supported codec/CDM integration only where an actual gap matters. [S7, S8] |
| P2 | Measure control-session differences | Compare manual launch, launch with CDP available, attached client and normal task execution. Attribute any difference before changing protocol-domain subscriptions or adding engine patches. This is a proposed experiment, not a demonstrated universal CDP detector. |
| Defer | Cosmetic Google branding, fabricated plugins/devices, blanket JavaScript shims | These do not establish real capability parity. Keep Chromium identity and a small reviewable downstream queue; require a measured reason for each additional deviation. [S6, S9] |

### Identity: more than the User-Agent string

Chrome exposes brand/version/platform through both HTTP Client Hints and
`navigator.userAgentData`; higher-entropy values are separately requested. [S4]
The UA-CH draft exposes this information in Window and Worker contexts and
specifies arbitrary brand entries and ordering behavior. Therefore a comparison
must not mistake a normal GREASE brand or permutation for an error. [S5]

Chromium's native identity generator derives brands from build branding and
product information. A Chromium brand difference is expected product identity,
not proof of automation. [S6] Retaining Chromium honestly means some stock
Google Chrome identity differences remain. If a future compatibility experiment
changes identity, it must specify all affected surfaces and actual release/OS
values, rather than add a Google Chrome brand string as a capability claim.

The DevTools Protocol explicitly separates `userAgent`, `platform`,
`acceptLanguage` and `userAgentMetadata`; its Emulation command says metadata
must be supplied for Client Hint headers. [S10] Prefer native consistency over
an expanding collection of per-page getter overrides. Validate redirects,
new tabs, frames and workers instead of assuming override scope.

### Rendering and desktop posture

Modern headless and headed Chrome share browser code; Chrome documents that
unification began in 112. Headed mode is useful here because the target is a
desktop presentation, not because headless is inherently a different engine
or because visible windows prove non-automation. [S2]

Chromium documents SwiftShader as CPU graphics and warns that its unsafe WebGL
fallback reduces security guarantees. Do not add unsafe fallback or falsify
renderer names to resemble a GPU. Measure the real GPU/WebGL/WebGPU path and
retain a documented fallback where hardware acceleration is unavailable. [S3]
Likewise, use actual fonts and regional settings consistently; adding random
per-request values is not part of this recommendation. [S1]

### Media, branding and services

Chromium documents proprietary codec differences, and identifies
`proprietary_codecs` and `ffmpeg_branding` as separate media configuration
controls affecting reported support and codec selection. The FFmpeg value
`Chrome` is a media configuration name, not a request to build Chrome for
Testing or proof of Google product branding. Verify decoding rather than
altering only support answers. The documentation does not establish this
project's distribution entitlement for additional components. [S7]

Widevine integration needs actual platform CDM binaries and associated manifest
and license files; a public build flag alone does not provide them. Widevine's
integration overview describes agreements, SDK/library delivery and testing.
DRM parity remains unqualified without a supported integration and successful
authorized playback. No borrowing of another browser's CDM is proposed. [S8]

Google's branded assets require internal resources and are not released under
Chromium's open-source branding license. Changing the icon or product name
does not supply those resources or web capabilities. [S9] Google browser sign-in,
Sync-related access and extension identity APIs have separate restrictions;
arbitrary API keys do not recreate Chrome service parity. Website sign-in and
browser Sync are distinct requirements. [S11]

Keep the existing custom profile directories and isolated remote-debugging
posture. Chrome documents a separate debugging profile as its supported
security model; its article's recommendation of Chrome for Testing is explicitly
not adopted under this repository's operator requirement. [S12]

## Smallest useful follow-up experiment

One synthetic HTTPS origin under operator control should return received
headers and explicitly request the relevant Client Hints. Capture both the
initial and subsequent negotiated requests; record secure-context and
Permissions-Policy conditions. UAData availability in workers must be tested
in supported contexts, not generalized from a page-only probe. [S4, S5]

For each of the three baseline modes, collect a curated report:

1. Exact executable hash, engine version, resolved build settings, launch
   switches and desktop environment; no cookies, tokens or private page data.
2. UA and negotiated Client Hints; UAData in page and workers; language,
   locale and timezone; screen/window/viewport/DPR and focus/visibility.
3. GPU availability/renderer, WebGL/WebGPU capabilities, representative font
   layout and media playback/support. Treat unavailable capabilities as results.
4. Native permissions and popup/repost behavior using synthetic fixtures;
   record intentional task-specific overrides separately.
5. Existing `navigator.webdriver=false` and smoke/regression acceptance. That
   getter is an intentional downstream difference, not complete stock parity.

Bound the first experiment to one host, one platform/version pair, three modes
and one repeat per mode. Stop with an attributed difference table. Do not start
a browser build until a selected difference actually requires source changes.
Success means fewer unexplained departures and no loss of required behavior;
there is no meaningful universal detector-pass percentage established here.
Do not copy or migrate retained profiles. Provision disposable comparison
profiles only within an explicitly authorized implementation experiment.

## Sources

All external sources accessed 2026-11-13. Recommendations and experiment design
are inferences from the cited mechanisms, not vendor promises of site acceptance.

- [S1: W3C fingerprinting guidance](https://www.w3.org/TR/fingerprinting-guidance/).
- [S2: Chrome Headless mode](https://developer.chrome.com/docs/automation-and-testing/headless).
- [S3: Chromium SwiftShader documentation](https://chromium.googlesource.com/chromium/src/+/main/docs/gpu/swiftshader.md).
- [S4: Chrome User-Agent Client Hints](https://developer.chrome.com/docs/privacy-security/user-agent-client-hints).
- [S5: UA-CH draft, interfaces and brand processing](https://wicg.github.io/ua-client-hints/).
- [S6: Chromium native User-Agent/brand generation](https://chromium.googlesource.com/chromium/src/+/main/components/embedder_support/user_agent_utils.cc).
- [S7: Chromium audio/video and build configuration](https://www.chromium.org/audio-video/).
- [S8: Chromium CDM build](https://raw.githubusercontent.com/chromium/chromium/main/third_party/widevine/cdm/BUILD.gn) and [Widevine integration overview](https://www.widevine.com/solutions/widevine-drm).
- [S9: Google Chrome branded builds](https://chromium.googlesource.com/chromium/src/+/main/docs/google_chrome_branded_builds.md).
- [S10: Official DevTools Protocol schema, Emulation.setUserAgentOverride](https://raw.githubusercontent.com/ChromeDevTools/devtools-protocol/master/json/browser_protocol.json).
- [S11: Chromium API keys and service restrictions](https://www.chromium.org/developers/how-tos/api-keys/).
- [S12: Chrome remote debugging changes](https://developer.chrome.com/blog/remote-debugging-port).
- [L1: Agent Browser launch argument construction, merged source](https://github.com/CochranResearchGroup/agent-browser/blob/ea9bcb186b41209b2887a871aaf38d7ef6f3115f/cli/src/native/cdp/chrome.rs#L923).
- [L2: Current native webdriver patch](../../../patches/0001-Make-navigator.webdriver-non-advertising.patch).
- [L3: Controller release configuration and profile synchronization](../../../scripts/automation_pipeline.py).
