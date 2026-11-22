# Preserve the libsync checkout during upstream transitions

State: CLOSED

Handle the Chromium 158 source layout transition in candidate preparation.
The old upstream revision stores libsync as a gitlink. The new revision tracks
the files directly, so Git refuses to switch revisions while the nested
checkout occupies those paths.

The local acceptance criterion is that candidate preparation reaches dependency
sync at the pinned revision and retains the prior nested checkout, including its
Git history. Source preparation remains fail-closed for a changed or dirty
nested checkout. This change covers the libsync path in the managed checkout.
A Chromium compile, downstream patch replay on Chromium 158, publication, and
deployment are outside the local fixture.

Base controller commit: b27198e985d2d9b2e50627a57985ad0aa88579c6.

Red and green command:

```sh
PYTHONPATH=tests python3 -m unittest test_automation_pipeline.PipelineSafetyTests.test_prepare_preserves_libsync_when_upstream_replaces_gitlink
```

Red failed at the real Git checkout. Green reached the dependency-sync boundary
and verified both the incoming tracked file and preserved dependency checkout.
The fixture uses local Git repositories and stops before invoking gclient or
other upstream services.

Local validation also passed with `python3 -m unittest discover -s tests` (119
tests) and `git diff --check`. Hosted CI was skipped under repository policy.
