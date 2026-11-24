# Adopt chromiumQ product branding

State: CLOSED

Use the spelling chromiumQ in current product documentation, Linux desktop
entries, Debian package presentation, updater service descriptions, future
GitHub release titles and updater notifications. Keep the current command,
package ID, service IDs, artifact identities and on-disk locations compatible
with existing installations. Historical releases and receipts retain the names
recorded when they were created.

Validation on base 9f16c5f16b9d0fe57dc312ea468b272ea4c86097 used local Linux/WSL
fixtures. All 40 tests passed with
`PYTHONPATH=tests python3 -m unittest test_install_automation test_automation test_automation_notify test_codec_continuity`.
Shell syntax checks passed with
`bash -n scripts/install-linux-user.sh scripts/package-deb.sh`.
Hosted CI, provider publication and installed-browser changes were outside
this validation.
