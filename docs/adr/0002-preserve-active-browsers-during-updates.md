# Preserve active browser sessions during automated activation

Activating a newly deployed browser changes the version used for subsequent
launches while already-running sessions continue until closed normally. This
preserves tabs, authentication and in-progress work, accepting that a running
browser may remain on an older release until it exits; automatic routine
updates do not restart those browsers or migrate their profiles.

Accepted in Plan 0005 interview round 1. Round 2 explicitly extends this rule
to urgent security releases: deploy the qualified fix for new launches and
prominently report older running browsers, without forcing their restart.
Local activation rollback is covered separately by ADR 0003.
