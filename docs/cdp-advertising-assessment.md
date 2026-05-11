# CDP Advertising Assessment

Base Chromium revision: `d421c3af8268e2e6227b7fe4461183e69b64bc61`

## Scope

Assess how Chromium's Chrome DevTools Protocol implementation is activated and
which parts of that state are advertised to web content.

This note is evidence-gathering only. It does not propose a source patch yet.

## Current Findings

### Remote debugging startup

Chrome starts remote debugging from
`chrome/browser/devtools/remote_debugging_server.cc`.

Observed behavior:

- `--remote-debugging-pipe` starts a pipe handler.
- `--remote-debugging-port=<port>` starts the HTTP/WebSocket DevTools server.
- `--remote-debugging-port=0` also writes the selected port into the profile
  directory via the `DevToolsActivePort` bootstrap file.

Important source locations:

- `chrome/browser/devtools/remote_debugging_server.cc:354`
- `chrome/browser/devtools/remote_debugging_server.cc:364`
- `chrome/browser/devtools/remote_debugging_server.cc:368`
- `chrome/browser/devtools/remote_debugging_server.cc:391`

### Blink automation feature switch

Renderer runtime feature wiring is in `content/child/runtime_features.cc`.

`AutomationControlled` is enabled when any of these launch conditions are true:

- `--enable-automation`
- `--headless`
- `--remote-debugging-pipe`
- `--remote-debugging-port=0`

Notably, `--remote-debugging-port=<fixed-number>` is intentionally not treated
as automation in this code path.

Important source locations:

- `content/child/runtime_features.cc:436`
- `content/child/runtime_features.cc:437`
- `content/child/runtime_features.cc:438`
- `content/child/runtime_features.cc:476`
- `content/child/runtime_features.cc:488`

### Website-facing signal: navigator.webdriver

The main explicit web-facing signal is `Navigator::webdriver()`.

It returns true when either:

- Blink's `AutomationControlled` runtime feature is enabled.
- A DevTools emulation automation override has been applied.

Important source locations:

- `third_party/blink/renderer/core/frame/navigator.cc:100`
- `third_party/blink/renderer/core/frame/navigator.cc:101`
- `third_party/blink/renderer/core/frame/navigator.cc:105`

### CDP automation override

The CDP method `Emulation.setAutomationOverride` is wired through browser and
Blink layers.

Browser-side behavior:

- Enabling the override adds an automation infobar when a content infobar
  manager exists.
- Disabling it removes the infobar.
- The browser handler then falls through to Blink's emulation handler.

Blink-side behavior:

- `InspectorEmulationAgent::setAutomationOverride()` stores the override.
- `InspectorEmulationAgent::ApplyAutomationOverride()` ORs that stored value
  into `Navigator::webdriver()`.

Important source locations:

- `chrome/browser/devtools/protocol/emulation_handler.cc:134`
- `chrome/browser/devtools/protocol/emulation_handler.cc:156`
- `third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc:1050`
- `third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc:1098`

### DOM automation controller

`window.domAutomationController` is separate from CDP. It is injected only when
the renderer has the `--dom-automation` switch, mostly for Chromium tests.

Important source locations:

- `content/renderer/render_frame_impl.cc:4055`
- `content/renderer/dom_automation_controller.cc:21`
- `content/renderer/dom_automation_controller.cc:41`

## Patch Surface Candidates

Candidate patch surfaces, in likely order:

1. `content/child/runtime_features.cc`
   Remove or gate the automatic `AutomationControlled` enablement for CDP
   transport switches.

2. `third_party/blink/renderer/core/frame/navigator.cc`
   Adjust `Navigator::webdriver()` behavior directly, or make it conditional on
   a custom stealth policy.

3. `third_party/blink/renderer/core/inspector/inspector_emulation_agent.cc`
   Change how `Emulation.setAutomationOverride` affects the page-visible
   webdriver signal.

4. `chrome/browser/devtools/protocol/emulation_handler.cc`
   Change the browser-visible automation infobar behavior for CDP automation
   override.

5. `chrome/browser/devtools/remote_debugging_server.cc`
   Review whether `DevToolsActivePort` and startup mode behavior need changes
   for the intended launcher model.

## Open Questions

- Should the custom build hide all automation signals, or only avoid advertising
  CDP transport usage?
- Should `Emulation.setAutomationOverride` continue to exist but become
  page-invisible, or should it preserve upstream behavior for compatibility?
- Is the intended launcher using `--remote-debugging-pipe`,
  `--remote-debugging-port=0`, or a fixed debugging port?
- Do we need to preserve WebDriver specification behavior for explicit
  WebDriver/ChromeDriver use, or is this build intentionally nonstandard?
