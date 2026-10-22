# Plan 0004: Publish and install Stable 156 as a browser choice

State: OPEN

## Objective and authority

The operator explicitly requested publication and installation, Agent Browser
selection support, and broad browser-choice availability. This authorizes the
shared artifact alias cutover and user-scoped runtime configuration. Public
GitHub destination remains a clarification because the configured repo is
public and the modification was described as private. Do not disclose the
private queue publicly while that clarification is pending.

## Current State

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
