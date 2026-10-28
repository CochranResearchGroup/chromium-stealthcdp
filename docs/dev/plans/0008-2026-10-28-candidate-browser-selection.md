# Plan 0008: Diagnose candidate browser qualification failure

State: OPEN

## Current State

Operator reports upgrade failed at prepare and invokes diagnosing-bugs.
Clean patch repo dd7d0d4; operator Chromium source clean15a1e89. Failed target
156.0.8078.73, upstream2f9a11097447f226133bc1a31c787291a5eeab98.
Run receipt says Fresh selected browser binary does not match qualified artifact.
Candidate journal is built; staged candidate manifest exists. Controller prepare
covers the full candidate pipeline, so stage label alone is not source failure
proof. Existing installed156.0.8078.47 is preserved.

## Bounds and authority

Primary builds and minimises a deterministic qualification repro, presents
3-5 falsifiable hypotheses before testing, fixes the proven cause with a red
regression, then retests original scenario. One fix/review pass; no blind rebuild
or upgrade requeue. Existing goal authorizes bounded qualification and routine
release/deployment after all gates; no profile/live-peer mutation. Preserve
failed logs/artifacts and do not weaken executable hash gate. Graph indexing
is prohibited by repo-specific guidance; use exact targeted source paths.
No graph memory group; supplied/current repo evidence is authoritative.

Delegation decision: repro is initially serial and urgent; independent review
will follow a proven bounded fix. Stop if repro cannot establish exact symptom.

## Reproduction and hypotheses

Original live qualification reproduced the exact hash-mismatch failure with
all15 owned browser PIDs gone after close. Minimized regression command:
python3 -m unittest discover -s tests -p test_automation_deploy.py -k private_runtime -v
failed in0.1sec with the same DeploymentError, before the fix. It exercises
qualify -> real command adapter -> stateful shared-runtime selection fixture.

Three ranked hypotheses were presented before probing: shared runtime ignores
client candidate config; build selector overrides explicit executable; staged
artifact hash mismatch. Actual staged hash equals manifest36294494abee9f0e304793797c8ebe8c70a65814f0924abf05b21a5511d12eaa.
Indexed Agent Browser source confirms named sessions map to the shared runtime
endpoint. A fresh candidate-only HOME/socket/runtime isolates startup config.
No Agent Browser repository changes or index initialization were performed.

## Fix and validation checkpoint

Candidate-only private runtime consistently selects156.0.8078.73 at exact
expected hash with webdriver=false. Installed acceptance continues using the
shared consumer configuration. Candidate cleanup closes the positively owned
private daemon (UID, exact socket env, PID start) and verifies descendants gone;
legacy close-by-session is not assumed to own a managed-session record. The
idle timer must leave enough startup time;60sec used after1sec proved too short.
Live receipt automation/candidate-selection-fixed.json records16 owned runtime
processes and ownedProcessesRemaining=[]. No peer/profile was modified.

Recovery found a second deterministic obstacle: qualification had promoted the
candidate before failing, so promotion on retry refused artifact already exists.
A second red0.02sec qualify seam fixture reproduced this. Qualification now
reconciles exact version/queue directory, full existing provenance and binary
hash against rebuilt output without replacing it, then reruns qualification.
45 fixtures pass. /root/review_selection_fix independently reviewed candidate
routing/custody and ran8 deployment tests, no material findings. Primary accepts
its bounded evidence; new recovery guard review pending. No debug logging or
throwaway source artifacts retained.
