# Plan 0009: Diagnose browser executable substitution

State: CLOSED

## Objective

Reproduce unintended Chrome for Testing selection when Chromium StealthCDP is
required, minimize the trigger, then identify the cause using the invoked
diagnosing-bugs skill. Primary owns the serialized investigation.

## Current State

Starting patch repository e99de47a784bf54cb7f1786cccf41c75202699b0 and Chromium
source 15a1e89ace187947b2a39881b45f4de992157b56 are clean. Agent Browser checkout
is clean at fb2e4bca108d99d158f007d249d823a801874c38. Service access-plan selects
StealthCDP; that does not qualify MCP owner's launch behavior. A disposable
about:blank MCP task is being used as the actual launch repro. Private runtime
receipts and task identifiers stay outside Git.

## Scope and acceptance

No retained profile mutation, active-peer cleanup, browser installation or
Chromium compilation. First qualify a repeatable red launch check; do not
promote source observations to causal diagnosis before that check exists.
Publish ranked falsifiable hypotheses after reproduction and minimization.
A repair requires the original launch check green and a regression at the
correct call seam. Runtime replacement remains distinct from source validation.
If the loop cannot be trusted, stop with the precise missing evidence under
the skill's Phase 1 rule. No subagents are needed for coupled local diagnosis.

## Diagnosis outcome and bounded closeout

Version 2: this packet closes diagnosis answering the operator's original cause
question; source repair and installed qualification remain separate unfinished
work. No Agent Browser source or runtime configuration was changed.

Actual MCP browser_open with a disposable profile and about:blank launched
Google Chrome for Testing 157.0.8103.78. Repeating the same task key returned
the same task/browser. An exact-profile /proc executable check followed by
--version failed the assertion requiring Chromium. The launch path takes
minutes through provider readiness; the physical executable assertion takes
under one second. Thus the full fast regression loop required by the skill is
not yet qualified, and no green repair result is claimed.

Ranked hypotheses tested: (1) MCP bypasses service selection, (2) stale startup
configuration, (3) a retained testing-profile pin. Fresh disposable reproduction
excludes a retained profile pin as a necessary trigger. Current source shows
load_default_browser_session_host in cli/src/native/browser_session_host.rs
initializes runtime executable_path from AGENT_BROWSER_EXECUTABLE_PATH alone
(lines 505-508), without resolving the service manifest/default. Inspected MCP
processes have that variable unset. Generic find_chrome in
cli/src/native/cdp/chrome.rs prioritizes the downloaded installation cache
(lines 2196-2200). Those boundaries explain why a passing service access-plan
and valid StealthCDP manifest did not prevent the observed MCP substitution.

Important identity distinction: inspected Agent Browser source is
fb2e4bca108d99d158f007d249d823a801874c38; the installed generation observed
at closeout is 0.28.0-2c03c4cafd7b-7a113b1862e9. Source inspection is not
exact installed-binary provenance or a source repair qualification. Earlier
turns observed a different installed generation; do not install or restart over
concurrent runtime work based on this diagnostic packet.

Exact disposable task close returned closed=true, browser_closed and
 taskRetained=false. Fresh /proc check confirms the original test PID absent.
No retained profiles or peer browsers were closed. No debug instrumentation
was added. The preliminary repeat-cell process assertion ran after close and
reported no matching process; that is cleanup timing, not a second symptom
assertion. The earlier pre-close exact-profile assertion is the valid red proof.
Private curated receipt is under the user's local state directory, not Git.

Recommended repair: make the managed MCP launch owner resolve the configured
StealthCDP executable through the same manifest/default authority, fail when it
is required but unavailable, and cover disposable, named, manual and recovery
launches with an isolated deterministic regression. Phases 5 and repaired
original-loop qualification have not been executed in this diagnosis packet.
Memory disposition: forbidden for this repo graph write because no reviewed
Chromium StealthCDP graph group is configured; retain continuity here.
