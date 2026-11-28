# Complete the chromiumQ identity migration

State: PLANNED

## Current State

Chromium 158.0.8127.36 is installed under
`/home/ecochran76/.local/share/chromiumQ` with the `chromiumQ` launcher.
The installed binary passed CDP smoke and H.264, WebM, and AAC acceptance.
The chromiumQ repository is at `85dcd4a1c2661d4b47650a0e43f0b914971af591`
after PRs #26 and #27. Agent Browser's configured build manifest and capability
registry point to the new install. Its status resolves the new executable.
A disposable managed launch still needs proof because the MCP transport closed.

Plan 0022 records the completed presentation change. This plan extends it to
active installation, release automation, and browser consumer identities.

## Decision

Use `chromiumQ` for the product, launcher, and canonical Agent Browser build
ID. Use the lowercase `chromiumq` in identifiers whose format requires
lowercase, including Debian package names. Accept the old Agent Browser build
ID temporarily on input and emit the canonical ID in new responses and state.
Remove the input alias after the migration and retention checks below pass.
Preserve original identities in historical release records and receipts.

Deployment installs a qualified immutable artifact. Activation selects it for
new browser launches. Preserve existing browser processes and retained
profiles. Rollback changes selection to a previously qualified installation.

## Implementation tickets

1. **Normalize Agent Browser input and prove canonical output.** No blockers.
   Use an isolated worktree from freshly fetched `origin/main`. The observed
   baseline was `7d4274400bfdda72986ef2b033d39e0d8680489a`. The root contains
   unrelated work. Start with a failing test through the config or request
   interface that submits both IDs and expects identical routing and canonical
   output. Carry that behavior through CLI, API, generated clients, retained
   state readers and dashboard. Run local contract and routing tests. Resolve
   conflicting dual declarations explicitly.
2. **Migrate chromiumQ installation and release automation.** No blockers.
   Inventory launchers, package and artifact IDs, manifests, data roots,
   updater units, defaults, and registry/repository references. Rehearse in a
   disposable installation with existing state and a versioned rollback
   target. Prove the new updater still honors its approved patch queue and
   build profile, and that only one scheduler owns builds. Verify Windows
   paths and package identifiers with local fixtures before each platform's
   activation. Use GitHub's current repository identity for release URLs.
3. **Activate the coordinated defaults.** Blocked by tickets 1 and 2.
   Verify reviewed merged commits and immutable installed generations.
   Migrate the actual consumer configuration and verify canonical status.
   Open one fresh, disposable managed task and bind its browser process
   executable and version to the installed chromiumQ manifest. Close the task
   and verify its process and profile cleanup. Preserve active sessions and
   run a no-launch observation of rollback routing.
4. **Retire legacy input and active installation references.** Blocked by
   ticket 3 and a verified consumer census. Confirm deployed config, caller
   requests, retained-state readers, scheduler, generated contracts and
   installer entry points operate without the old identifiers. Remove aliases
   and disable retired launch or updater entry points once no active consumer
   relies on them. Re-run the managed launch, package/install and rollback
   checks. Preserve historical evidence and retained profiles.

## Completion evidence

Record source SHAs, path and artifact digest, local test commands, results,
and deployed generation readback. A status response proves resolution.
Managed process identity proves activation. Package or controller qualification
does not establish public release eligibility. Use local validation in place
of hosted CI.
