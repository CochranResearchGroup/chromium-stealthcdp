# Plan 0004: Publish and install Stable 156 as a browser choice

State: CLOSED

## Objective and authority

The operator explicitly requested publication and installation, Agent Browser
selection support, and broad browser-choice availability. This authorizes the
shared artifact alias cutover and user-scoped runtime configuration. Public
GitHub destination initially required clarification because the configured repo is
public and the modification was described as private. Subsequent readback
resolved that ambiguity: remote main already contains the identical webdriver
modification and the public Stable 153 release distributes the same queue.
The operator's explicit publish instruction therefore follows that existing
release channel; no new private implementation is being disclosed.

## Current State

Stable 156 is published, installed and available through Agent Browser selection,
the user PATH and desktop browser chooser. The public release and source tag
are verified; all seven uploaded asset digests match local files. Installed
Agent Browser launch used the exact validated executable, reported
navigator.webdriver=false, and closed cleanly. No remaining acceptance work.

## Starting State

Plan 0003 produced validated candidate 156.0.8078.47+stealthcdp.4b864442a8fd;
source 15a1e89ace187947b2a39881b45f4de992157b56, clean patch repo
098dcd7172c23c937d03fb6a77e043f3ae435f02. Both smokes and 43 regression tests
passed. Agent Browser already offers stealthcdp_chromium, but its user-scoped
manifest selector still points to Stable 153. Sudo is not passwordless; a
user-scoped installed browser, desktop entry and PATH command are feasible.

## Execution and acceptance

Primary owns the serialized publish -> install -> selector -> smoke path.
Add a reusable Linux user installer and desktop registration to Debian
packaging. Preserve old artifacts, prior config, profiles and active peer
browsers. Publish the exact validated artifact under the shared artifact root;
install immutable version under the user's data home, with an atomic current
alias, desktop browser entry and PATH launcher. Bind the existing Agent Browser
choice through user configuration, without changing other browser choices.
Verify installed hashes/version, desktop registration, Agent Browser resolution,
an isolated launch and navigator.webdriver=false, then check process cleanup.
Use two attempts per unit and one independent final review. Keep the private
queue local unless the operator explicitly selects public source publication.
Definition of done: published artifact, usable installed browser, successful
selected Agent Browser launch, accurate remaining external-publication status.

## Delegation and memory

Implementation not_spawned: one coupled install/configuration surface.
Independent evaluator follows the verified install. No repo Graphiti group is
defined; use a forbidden non-write receipt at closeout and retain source
continuity here. User runtime configuration and receipts stay outside Git.

## Evidence and current execution

- Shared current alias now selects 156.0.8078.47+stealthcdp.4b864442a8fd;
  previous Stable 150 artifact is preserved.
- Reusable user installer installed the exact hash-validated artifact, desktop
  entry and PATH command; repeated installation succeeded without recopying.
  Direct installed smoke passed and reported Chromium 156.0.8078.47.
- Agent Browser user configuration now binds both the build manifest selector
  and exact Linux executable registry entry to the installed Stable 156 build.
  Other executable records and choices are preserved. Original configuration
  and runtime receipts remain in the private user state directory outside Git.
- Explicit stealthcdp_chromium launch through installed Agent Browser succeeded.
  Its OS executable SHA-256 matched the accepted binary
  2492fd6e2bab04707c263862df5563d10eee1660253cbcc0c06af3699ecc7b9c;
  JavaScript reported webdriver=false and Chrome/156. Scoped close succeeded;
  fresh process census found no installed-candidate processes remaining.
- GIO lists chromium-stealthcdp.desktop for HTTPS; the existing Google Chrome
  default is unchanged. The minimal host lacks desktop-file-utils, so the
  installer updates only this entry's MIME registrations atomically as fallback.
- Debian package built successfully and contains the desktop entry and
  /usr/bin/chromium-stealthcdp launcher. The executable extracted from both
  the Debian package and portable archive matches the accepted SHA-256.
- Independent reviewer /root/review_install156 returned no material findings
  in the initial pass or closed-world MIME fallback verification. Primary
  accepted the review and independently verified install and runtime behavior.
- Public release:
  https://github.com/CochranResearchGroup/chromium-stealthcdp/releases/tag/v156.0.8078.47-stealthcdp.4b864442a8fd
  Source main and the immutable release tag were read back at
  8787d3364a59c5336d466cbf2cbd7b25fb298c8e before this documentation closeout.
  All seven uploaded assets have server SHA-256 digests matching local hashes;
  the release is published and not a prerelease. Assets include Debian and
  portable Linux runtimes, user installer, manifest, smoke and checksums.
- Live Agent Browser service status reports the installed manifest valid and
  ready, executablePathSource=manifest, stealthCdpChromiumReady=true and no
  launch warnings. It resolves Chromium 156.0.8078.47 from the installed copy.
- Final memory disposition: forbidden because no reviewed repo Graphiti group
  is defined; zero graph writes. Continuity is preserved by this source plan,
  release notes and external install/publication receipts.
