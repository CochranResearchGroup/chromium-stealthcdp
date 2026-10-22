# Run initial release automation on the operator workstation

The initial automation builds Linux x86_64 releases in a dedicated managed
checkout on the operator workstation and deploys to that user's browser
consumers. This reuses the qualified Linux environment and avoids adding a
cloud builder or fleet before those targets are qualified, at the cost of
depending on workstation availability and sharing its resource budget.

Daily detection and manual triggering lead to unattended build, qualification,
publication and deployment for routine updates. Patch conflicts or failed
qualification stop release and produce a repair proposal for review; they do
not grant automatic acceptance of changed patches. Windows is a separate later
lane. Accepted in Plan 0005 interview round 1; implementation is pending final
design confirmation.
