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
is below 32 GiB or free disk below 200 GiB. An unchanged Stable version and
approved queue return `unchanged` without building or publishing.

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
the normal GitHub API only after observed status/check suites pass. Repository
protections still apply. Pending checks retain the candidate for a later check.
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

From a clean committed checkout:

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
