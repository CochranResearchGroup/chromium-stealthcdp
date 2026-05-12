# Minimal Stealth CDP Plan

Base Chromium revision: `d421c3af8268e2e6227b7fe4461183e69b64bc61`

## Objective

Disable external, website-visible automation signals for CDP-driven Chromium
across launch modes including headless, `--remote-debugging-pipe`, and
`--remote-debugging-port=0`, while keeping the changeset as small as possible.

This plan targets page-visible signals. It does not try to hide process command
line flags, local DevTools sockets, profile files, or operating-system-level
artifacts from local users or other processes.

## Minimal Patch Strategy

Use one Chromium patch that targets the website-visible automation signal.

### Patch 1: Make navigator.webdriver stay false

Files:

- `third_party/blink/renderer/core/frame/navigator.cc`

Change:

- Modify `Navigator::webdriver()` so it does not expose automation state to web
  content.
- The smallest behavior change is to return `false` directly.
- A slightly more maintainable version is to gate the upstream behavior behind a
  new build flag or runtime feature, but that increases the patch surface.

Rationale:

- This is the narrowest external visibility choke point found so far.
- It covers all current inputs that feed the webdriver signal:
  `AutomationControlled`, headless mode, remote debugging pipe,
  `--remote-debugging-port=0`, `--enable-automation`, and
  `Emulation.setAutomationOverride`.
- It avoids changing CDP startup, DevTools transport, or ChromeDriver connection
  mechanics.

Expected result:

- `navigator.webdriver` returns `false` in normal, headless, pipe, fixed-port,
  ephemeral-port, and automation-override cases.

Risk:

- This intentionally diverges from WebDriver expectations.
- Some Chromium/ChromeDriver tests that assert standards-compliant webdriver
  exposure may need expectation updates or exclusion from this custom patch
  queue.

## Explicit Non-Goals For Minimal Changeset

Do not change these in the first patch:

- `chrome/browser/devtools/protocol/emulation_handler.cc`
- `chrome/browser/devtools/remote_debugging_server.cc`
- `content/child/runtime_features.cc`
- `content/browser/devtools/devtools_http_handler.cc`
- `content/browser/devtools/devtools_pipe_handler.cc`
- `content/browser/devtools/protocol/browser_handler.cc`
- `content/renderer/dom_automation_controller.cc`

Reasoning:

- Remote debugging transport still needs to work.
- `AutomationControlled` may affect internal behavior beyond
  `navigator.webdriver`; changing its launch-switch wiring is broader than
  changing the public accessor.
- `Browser.getBrowserCommandLine` is CDP-client-visible only and already gated
  on `--enable-automation`; it is not website-visible.
- The automation infobar is browser UI. It is visible to human observers, but it
  does not expose automation status to external websites through JavaScript or
  normal web APIs.
- `window.domAutomationController` is controlled by `--dom-automation`, not CDP,
  and should stay out of the first patch.

## Validation Matrix

For each mode, open a page and evaluate:

```js
navigator.webdriver
```

Required modes:

- Normal browser, no automation flags.
- `--headless --remote-debugging-port=0`.
- `--remote-debugging-pipe`.
- `--remote-debugging-port=0`.
- `--remote-debugging-port=9222`.
- CDP attached session after calling `Emulation.setAutomationOverride` with
  `enabled: true`.

Expected value for all modes after Patch 1:

```js
false
```

## Recommended Patch Queue

1. `0001-Make-navigator-webdriver-non-advertising.patch`

## Build And Test Commands

Build target:

```sh
autoninja -C out/Default chrome
```

Focused source-level smoke:

```sh
autoninja -C out/Default browser_tests content_browsertests
```

Likely focused tests to inspect or adapt:

- `chrome/browser/devtools/protocol/devtools_protocol_browsertest.cc`
- Blink tests around `navigator.webdriver`, if present in the checkout.
- ChromeDriver tests that assert WebDriver conformance.

Patch export:

```sh
cd ../src
rm -f ../chromium-stealthcdp/patches/*.patch
git format-patch --binary -o ../chromium-stealthcdp/patches "$(cat ../chromium-stealthcdp/upstream-revision.txt)..HEAD"
```
