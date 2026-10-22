# Preserve active browser sessions during automated activation

Activating a newly deployed browser changes the version used for subsequent
launches while already-running sessions continue until closed normally. This
preserves tabs, authentication and in-progress work, accepting that a running
browser may remain on an older release until it exits; automatic routine
updates do not restart those browsers or migrate their profiles.

Accepted in Plan 0005 interview round 1. Urgent security-update exceptions and
failure recovery remain separate, unsettled decisions.
