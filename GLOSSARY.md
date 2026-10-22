# Chromium StealthCDP releases

The language used to distinguish an upstream browser update, a validated
downstream release, and the browser a person or agent actually runs.

## Language

**Upstream Stable release**:
A Chromium version corresponding to the production Stable release for a
particular operating system.
_Avoid_: Latest Chromium, development snapshot

**Downstream patch queue**:
The ordered set of maintained changes applied to an upstream Chromium revision.
_Avoid_: Private browser, automation settings

**Release candidate**:
A particular downstream browser build undergoing qualification before release.
_Avoid_: Installed browser, published release

**Published release**:
A qualified downstream browser version made available to consumers together
with its identity and validation evidence.
_Avoid_: Successful build, local candidate

**Deployment**:
The installation and configuration of a qualified release for a particular
browser consumer.
_Avoid_: Publication, compilation

**Activation**:
The selection of an installed browser version for subsequent launches by a
particular consumer.
_Avoid_: Restart, installation

**Browser consumer**:
A person, application or service that selects and launches a downstream browser.
_Avoid_: Browser profile, build platform

**Routine update**:
An upstream Stable update that works with the approved downstream patch queue
and satisfies the established release qualification requirements.
_Avoid_: Repair, unreviewed patch change

**Repair proposal**:
A proposed downstream change needed to restore compatibility or qualification
when an upstream update cannot complete as a routine update.
_Avoid_: Automatic patch acceptance, routine update

**Release quarantine**:
The withdrawal of a confirmed defective published release from eligibility for
new activation while preserving its identity, artifacts and history.
_Avoid_: Release deletion, local rollback

**Activation rollback**:
The restoration of a previously qualified browser selection for subsequent
launches by a particular consumer.
_Avoid_: Profile restoration, release deletion
