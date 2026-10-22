# Chromium StealthCDP automated releases

Status: design decisions settled; awaiting final shared-understanding confirmation.

This is the consolidated design from Plan 0005's three interview rounds. It
describes the automation to implement, not an already running updater.

## Outcome

Keep the approved Chromium StealthCDP build current with Linux x86_64 production
Stable, automatically qualify and publish routine updates, and deploy them to
this user's workstation and Agent Browser. The browser remains available by
the terminal command, desktop browser choice and Agent Browser's
`stealthcdp_chromium` selection. Windows is a separate later lane.

The controller uses a dedicated managed checkout on this workstation, separate
from interactive source work. It does not modify retained browser profiles,
force-restart active browsers, change the OS default browser, or manage other
users or machines.

## Routine update

1. Check the official Linux Stable identity daily at **03:00 America/Chicago**,
   catching up once after workstation unavailability. Support a manual trigger.
   An unchanged upstream version and approved patch queue produce no rebuild or
   duplicate publication.
2. Permit one pinned run at a time. Coalesce additional triggers into the newest
   pending target; finish the current pinned run before starting that target.
   Keep durable stage receipts so interruption does not imply starting again.
3. Check resource headroom, fetch the exact upstream revision, synchronize
   dependencies and both browser/V8 optimization profiles, replay the approved
   patch queue and review the resulting source delta. A conflict is a repair
   case, not a routine update.
4. Build normal Chromium with the accepted official release configuration and
   explicit non-testing branding. Stage in a candidate root without changing
   the installed/current release.
5. Require exact tag/version and provenance, clean patch replay, matching build
   configuration and optimization profiles, focused regressions for every
   retained repair, active-CDP smoke with `navigator.webdriver=false`, package
   hash/provenance checks and an isolated Agent Browser acceptance check.
   For the currently retained Blink repair this includes its exact regression
   and the surrounding `LineBreakerTest.*` suite, not a permanently fixed test
   count.
6. Record the pin, exported queue, metadata and qualification evidence in a
   routine PR. Merge it automatically only after the required checks pass.
   Honor current repository protections and refuse force-push or unexplained
   source changes. Controller-driven merging does not require changing the
   repository's native auto-merge setting.
7. Publish the qualified source tag and Linux portable/Debian artifacts using
   the existing release naming and public repository. Verify uploaded asset
   identities and digests before advancing the release channel. Reconcile an
   uncertain result by reading remote state instead of blindly repeating it.
8. Deploy the immutable release and atomically activate it for new launches.
   Keep the PATH/desktop entry and both Agent Browser manifest and executable
   registry binding consistent. Verify a fresh installed Agent Browser launch
   against the accepted binary identity and webdriver behavior.

Runtime state, credentials and raw logs remain outside Git. Public summaries
contain source identities and curated qualification evidence, not raw private
runtime output.

## Workstation budget and retention

| Control | Accepted limit |
| --- | --- |
| Parallel compilation | Eight jobs |
| CPU | Eight CPU-equivalents, low priority |
| Memory | 32 GiB ceiling |
| Run duration | Twelve hours |
| Free-disk reserve | 200 GiB |
| I/O | Low priority |
| Local good releases | Active, previous and one additional release |
| Logs | Ninety days, plus retained latest-failure evidence |

Defer a build when headroom is insufficient. Resource exhaustion fails the
candidate without changing the installed browser. Retention deletes only
unused automation-owned files; protect versions used by live browsers,
rollback versions and the latest failure evidence. Never delete public history
or operator-owned source/output directories. If protected data prevents the
disk reserve, stop and report the condition.

## Continuity and recovery

Activation changes subsequent launches. Existing browser sessions finish
normally, including during urgent security updates; prominently report older
running browsers rather than forcing their restart.

A failed installed-launch check automatically restores the previous known-good
activation, retains failure evidence and stops further deployments. It does not
restore profiles, terminate active peers or erase release history.

Quarantine a public release and withdraw it from the latest channel only when
a release defect is established. Retain its tag and assets. A workstation-only
failure causes local recovery; an uncertain failure stops further rollout for
investigation rather than declaring the public artifact defective.

Allow one retry for a verified transient fetch/download failure. Do not repeat
identical failed builds or tests. Resume uncertain publication or deployment
only after reading back the actual outcome and matching its operation identity.

## Repair drafting

A non-routine failure stops release advancement and opens or updates a
deduplicated failure/repair issue. For each failed target, permit one Codex
draft attempt in a separate repair workspace, capped at **30 minutes** by the
controller's outer process/service limit. Use installed Codex and its configured
model/access; do not introduce another paid provider or silently change models.

A successful draft becomes a repair PR requiring human review. The repair
worker has no delegated release, merge or deployment authority. If Codex access
or safe owned-job containment cannot be qualified, retain a report instead of
launching an uncontrolled job. Preserve failure evidence. The same failed
target requires explicit requeue or changed input before another attempt.
The limit is wall time, not a claimed token or dollar cap.

## GitHub and reporting

Use the installed **`gh` CLI with its existing login** for repository-scoped
controller operations. No new GitHub App or credential setup is required.
Never copy authentication material into source, artifacts, logs or model
prompts. Authentication failure stops remote advancement.

Create/update one deduplicated GitHub issue for actionable failures or repair
proposals. Record successes in release notes and durable run receipts. If an
authentication/network failure also prevents issue creation, retain the
undelivered notification and local error receipt; do not claim it was delivered.

## Implementation acceptance

Implement and test stage transitions, idempotence, interruption/readback,
resource gating, active-version retention, rollback and repair timeout handling
with isolated fixtures before arming the schedule. Qualify the real installed
`gh`, Agent Browser and bounded Codex paths rather than equating installed tools
with working unattended execution.

Adopt the already qualified Stable 156 release as the starting baseline and
verify the unchanged-version path without republishing or needlessly rebuilding
it. Exercise the installation/selection checks with disposable browser work and
verify owned-process cleanup. A future new Stable release still requires the
complete build and qualification path before publication or activation.

Final design confirmation precedes implementation. After that confirmation,
ordinary implementation, testing and activation of this agreed automation do
not require repeated approval; only a material departure from this scope does.

## Decision sources

Plan 0005 records the exact questionnaire revisions and responses. ADRs 0001–0005
record placement, continuity, recovery, integration and credential trade-offs.
