# Integrate qualified routine updates through automatic pull requests

Routine updates record their pinned revision, exported queue, release metadata
and qualification evidence in a pull request that merges automatically after
the required checks pass. This leaves a reviewable source history without
requiring recurring manual approval, rather than writing automatic updates
directly to main.

Repair proposals require human review. Merge conflicts or branch-protection
requirements stop the run and report the blocker; automation does not
force-push or bypass repository protections. Accepted in Plan 0005 interview
round 2.
