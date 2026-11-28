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

## Problem Statement

The installed browser has the chromiumQ name, but Agent Browser still exposes a legacy build ID, and packaging and automation still depend on legacy names. Changing those identifiers in one step risks breaking saved configurations, consumers, and updater ownership.

## Solution

Expose chromiumQ as the canonical identity throughout active supported interfaces. Migrate consumers during a temporary compatibility window, verify activation in the managed runtime, and retire the old identifiers after confirming that consumers have migrated.

## User Stories

1. As an operator, I want to select chromiumQ in Agent Browser so I can identify the browser used by new tasks.
2. As a CLI consumer, I want an existing build selection to keep routing during migration so saved commands still work.
3. As an API consumer, I want canonical build IDs in responses so clients converge on the new identity.
4. As a dashboard operator, I want the displayed selection to agree with CLI and API status.
5. As an operator with retained sessions, I want them to continue while new sessions launch chromiumQ.
6. As a package user, I want a versioned chromiumQ installation and launcher so the active version is easy to verify.
7. As an updater operator, I want exactly one scheduler to own builds during migration.
8. As a release maintainer, I want updater and release URLs to use the current GitHub repository.
9. As an operator, I want rollback to select a previously qualified binary without resetting a profile.
10. As a maintainer, I want criteria for removing aliases so compatibility code has an end condition.
11. As a reviewer, I want original release and validation records to retain their provenance.

## Implementation Decisions

- Use `chromiumQ` for the product, launcher, and canonical Agent Browser build ID. Use `chromiumq` where lowercase is required, including Debian package identifiers.
- Accept the legacy build ID temporarily on input and emit the canonical ID in responses and newly persisted state. Treat conflicting dual inputs as an explicit configuration error.
- Coordinate executable discovery, package and artifact identifiers, updater units, generated contracts, and release URLs. Preserve a versioned rollback target and a single scheduler owner.
- Deployment installs an immutable qualified artifact. Activation selects it for subsequent launches. Retained profiles and active sessions keep their existing ownership.
- Remove compatibility after verifying deployed consumers and retained-state readers no longer require the alias. Preserve historical release records and receipts.

## Testing Decisions

- Exercise the public config and request interfaces with both inputs. Assert equivalent routing and canonical output using the existing contract and service routing suites. Cover conflicting declarations.
- Use disposable package and updater installations with seeded legacy state. Assert upgrade, rollback, one scheduler, preserved approved queue, and platform-specific naming through installer fixtures.
- For activation, compare no-launch resolution to a fresh disposable managed process bound to the installed manifest. Verify task and process cleanup with the same interfaces used by operators.
- Record exact commands, reviewed source SHAs, binary digest, and deployed generation. Run local checks in place of hosted CI.

## Out of Scope

Browser behavior changes, retained profile migration, public release publication, and rewriting historical records.

## Further Notes

Agent Browser work starts from freshly fetched upstream state in an isolated worktree because the root checkout contains unrelated edits. The observed remote-tracking base was `7d4274400bfdda72986ef2b033d39e0d8680489a`.

## Implementation tickets

- [0024 Normalize Agent Browser input and emit chromiumQ](0024-2026-11-27-agent-browser-canonical-chromiumq.md)
- [0025 Migrate installer and updater identities](0025-2026-11-27-chromiumq-installer-updater-identity.md)
- [0026 Activate chromiumQ for managed launches](0026-2026-11-27-chromiumq-activation.md)
- [0027 Retire legacy inputs and entry points](0027-2026-11-27-retire-chromiumq-legacy-identity.md)
