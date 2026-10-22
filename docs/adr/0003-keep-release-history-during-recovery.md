# Separate local recovery from public release quarantine

A failed installed-launch check automatically restores the previous
known-good activation for new launches, preserves failure evidence and stops
further deployment. It does not copy profiles or restart active browsers.

A confirmed defect in a published artifact also quarantines that release and
withdraws it from the latest-release channel, while retaining its tag and
assets. Workstation-specific failures cause local rollback without condemning
the public release; uncertain failures stop further rollout for investigation.
This preserves reproducibility and consumer history at the cost of retaining
unusable releases with explicit quarantine status instead of deleting them.
Accepted in Plan 0005 interview round 2.
