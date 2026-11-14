# Automated Linux Stable releases

The approved policy is [automated-release-design.md](automated-release-design.md).
The user service uses an immutable committed controller generation. Mutable
checkouts, stage journals, private logs and notifications live under
`~/.local/state/chromium-stealthcdp/automation/`. GitHub authentication uses the
existing `gh` login; credentials are never copied into this repository.

## Daily operation

The user timer `chromium-stealthcdp-update.timer` checks at 03:00 America/Chicago
and catches up after downtime. The service limits compilation to eight jobs,
CPU to eight equivalents, memory to 32 GiB without swap and elapsed time to
12 hours. It runs with low CPU/I/O priority. Builds defer if available memory
is below 32 GiB or free disk below 200 GiB. An unchanged Stable version, approved queue and build recipe return `unchanged`
without building or publishing. Legacy/no-recipe receipts cannot suppress codec
qualification or resume as current artifacts.

```
chromium-stealthcdp-update             # start the bounded service manually
chromium-stealthcdp-update status      # state and adopted/active identity
chromium-stealthcdp-update logs        # recent service journal
systemctl --user list-timers chromium-stealthcdp-update.timer
```

Only one controller holds the lock. Concurrent direct invocations write a
pending marker; the controller coalesces to the newest official target after
the pinned run. Starting an already active systemd service leaves that pinned
run alone. Each subsequent daily/manual check discovers the newest target.

## Release gates and recovery

Candidate preparation uses a separate marked checkout, exact official tag/SHA,
`git am`, ordered patch-id comparison and a reconstructed reference range-diff.
It synchronizes Chromium and V8 optimization profiles, builds non-testing
official Chromium and runs the retained repair's LineBreaker tests and CDP
smoke. Candidate Agent Browser selection verifies the actual OS executable
hash. Portable/Debian package identities are checked before the source PR.

Routine PRs receive an explicit local qualification status and merge through
the normal GitHub API after the pinned local qualification status is confirmed.
Repository merge protections still apply. Paid hosted Actions are not requested
or used as the qualification boundary.
A deterministic tag/draft release and server asset digest readback reconcile
publication interruption; differing identities stop rather than overwrite.

Activation journals the previous current alias, launcher, desktop/MIME entry
and both Agent Browser configuration bindings. A failed installed acceptance
restores those values and halts further deployments. Existing browser sessions
and profiles are preserved. An interrupted prepared transaction is recovered
before any no-op decision. Examine both `deployment-stopped.json` and
`deployments/deployment-halted.json`; clear them only after investigating the
cause and confirming the restored activation is usable.

Failed target identities do not repeat automatically. After fixing the cause,
an explicit operator reconciliation may run the controller with `run --requeue`
inside the same service resource limits. Do not restart an identical failed
build blindly. A new target/approved queue has its own identity. Stage receipts
remain outside Git; absence of a terminal receipt does not prove remote effects
were absent.

Public quarantine is reserved for a **confirmed release defect**. The
controller's `quarantine TAG --confirmed-defect EVIDENCE` command marks it
prerelease and ineligible for latest while preserving tag/assets. A local
installation failure alone never triggers public quarantine.

Failure issues are deduplicated per target. Authentication/network failures
retain an undelivered notification locally. Success evidence appears in release
notes and run receipts. No raw private logs or secrets are published.

## Installation / controller upgrades

Controller changes follow a short-lived branch, PR review, passing local checks,
merge into `main`, then installation from that clean merged source. Hosted GitHub
CI is not funded; do not enable it. Preserve recorded local validation rather
than waiting on billing-blocked hosted runs. After installation compare both the
`current` controller generation and config `source_repo` with the merged SHA.
Routine patch-queue fetching updates inputs only, not the immutable controller.

From that clean merged checkout:

```
python3 scripts/install-automation.py --depot-tools /absolute/depot_tools
python3 scripts/automation.py --config ~/.config/chromium-stealthcdp/automation.json adopt \
  --artifact ~/.local/share/chromium-stealthcdp/current
python3 scripts/install-automation.py --depot-tools /absolute/depot_tools --enable
```

Adoption verifies the existing public manifest digest, binary identity, CDP
smoke and a fresh installed Agent Browser launch. It does not republish the
baseline or replace retained profiles. Controller upgrades explicitly install
a new immutable generation; routine upstream changes never silently replace
the controller code itself.

Local retention protects active browser executable paths, the three latest
accepted owned versions, the latest failed candidate and active runs. It deletes
only marked automation-owned installs/candidate outputs; operator-owned source
and artifacts are excluded. Logs expire after 90 days except the latest failure.
Unreadable same-user process identity defers destructive retention.

## Repair admission

The current repair lane is **report-only**. Real installed-model access and
owned cgroup timeout/child cleanup were qualified, but those checks did not
establish isolation from all local control sockets and effect credentials.
No Codex repair worker is launched. A deduplicated local repair report and
failure issue preserve the target for a human-reviewed repair. This is the
approved fallback, not a claim that automatic repair drafting is operational.

## Private Slack upgrade announcements

Optional `slack` settings in the private controller configuration enable
operator-selected workspace/recipient delivery. Routing stays outside Git.
The notifier uses the installed Slack Receipts service layer and its existing
credential configuration; it does not create or borrow another integration's
HTTP machine credential. Sends require recipient readiness and a resolved
identity binding. A delivery receipt must include Slack provider acceptance,
channel and message timestamp; this is not proof that the recipient read it.

Successful upgrades, failures, restored activations, resource deferrals and
waiting/stopped outcomes produce curated notices. Daily `unchanged` checks are
quiet. Systemd `ExecStopPost` covers service timeout/abnormal termination even
when the controller cannot reach its normal failure handler. Notification
failure does not roll back or fail a qualified browser update.

The durable private `slack-outbox/` records each logical outcome before sending.
A repeated invocation reuses its idempotency key and original recipient. The
installed service reconciles that key; an existing failed/pending action does
not silently become a fresh send. Unconfirmed actions stay in the outbox for
readback on later checks, with no automatic new-key resend. If Slack is
unavailable, the existing GitHub failure issue and local receipts remain.


## Codec build and release identity

Routine GN configuration explicitly enables proprietary codecs with FFmpeg's
`Chrome` codec configuration; Chromium branding remains unbranded and both
Chrome-for-Testing flags must resolve false. All five values are read back from
GN before compilation. The accepted installed codec candidate demonstrated
H264 video frames and independent AAC PCM; automatic qualification runs the same
actual decoder seam on original and staged bytes plus WebM, active-CDP smoke,
LineBreakerTest and selected FFmpeg/AAC media tests.

The recipe SHA covers GN arguments and the decoder harness. It participates in
controller target/run/output identity, baseline no-op/resume checks, immutable
artifact manifests/names, release tags and Debian versions. A codec-only change
therefore cannot reuse or overwrite a noncodec release with the same upstream
version and patch queue. Old public releases remain immutable.

The target license-metadata scan is checked before compilation to avoid known
unpublishable full builds, then again after exact-byte qualification. It must
pass before packaging, source integration,
public release or automatic deployment. Its existing missing-metadata failures
remain unresolved in the manual candidate packet; local installed codec success
is not distribution qualification. This means the controller defaults can be
deployed now, while a future automated run may stop at qualification. It must
preserve the accepted installed browser, not substitute a noncodec/CFT build.
Do not adopt a privately staged codec installation as a published baseline.

Managed runtime hosts retain their launch configuration. Successful future
installation must refresh only the verified production host using its preserving
KillMode=process supervisor, require a complete unfiltered job snapshot with only known terminal states,
verify original browser PID/
start/executable identities survive, and prove fresh disposable managed-MCP
selection against the installed digest. Temporary-home fixture runs never touch
real systemd. Config/file restoration on rollback also refreshes cached launch
selection. Readiness/job observations are not an atomic admission lease; retain
that concurrency limitation and any interrupted effects for reconciliation.


The current Agent Browser CLI globally consumes `--state` before service-jobs
filtering. Refresh therefore uses unfiltered `service jobs --limit 10000 --json`
and requires integer count/matched/total equal to the returned row count. Missing,
truncated, queued/running/lease-waiting or unknown-state results block restart.
This preserves the existing observation boundary; it is not an admission lease.
