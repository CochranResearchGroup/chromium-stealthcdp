# Use the existing gh authentication for the update controller

The operator's final credential instruction is to use `gh`, replacing the
earlier preference for a dedicated repository credential. The updater therefore
uses the installed GitHub CLI and its existing authenticated account without
requiring a new GitHub App or token-provisioning workflow.

This avoids an additional credential lifecycle, accepting that the existing
login has broader permissions than a repository-only credential. The controller
targets the configured repository explicitly, checks authentication before
remote effects, and never copies tokens into source, build metadata, logs or
repair prompts. Authentication failures stop remote advancement and are recorded
locally if issue creation is also unavailable. Accepted in Plan 0005 round 3.
