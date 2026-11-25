# Use neutral chromiumQ descriptions

State: CLOSED

Replace product descriptions in the README, desktop metadata, Debian metadata
and future updater-generated GitHub copy. Refer readers to the actual patch
queue for source changes rather than repeating launch-mode details in the
patch boundary overview. The GitHub repository description is already empty.
Preserve patch bytes, compatibility identifiers, operational evidence and
historical records.

Base 32a55848f9e55afa7a3c18403766cea987420a3a. Local checks passed with
`PYTHONPATH=tests python3 -m unittest test_automation test_codec_continuity`
(30 tests), separate `bash -n` invocations for both modified shell scripts,
and `git diff --check`. Hosted Actions were skipped.
