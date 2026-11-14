# H.264/AAC configuration qualification

Date: 2026-11-13
Status: configuration, candidate qualification and installed adoption accepted.
Codec-preserving updater defaults are deployed through
[plan0016](../plans/0016-2026-11-14-codec-updater-continuity.md). The known strict
license-metadata blocker is repaired and passes in
[plan0017](../plans/0017-2026-11-14-strict-license-metadata.md). A new public codec
release still requires the full normal build/decoder/package/release pipeline.


Follow-up: [plan0015](../plans/0015-2026-11-13-codec-enabled-candidate.md) records
the built/staged Chromium157 candidate, actual H264/AAC/WebM decoder passes,
80 focused regressions and exact staged-byte smoke. The configuration-only
evidence below is retained as its original checkpoint.

## Outcome

The observed MP4 capability gap has a concrete build-configuration route that
retains Chromium StealthCDP and excludes Chrome for Testing. A fresh GN output
successfully resolves all five intended values:

```gn
proprietary_codecs = true
ffmpeg_branding = "Chrome"
is_chrome_branded = false
is_chrome_for_testing = false
is_chrome_for_testing_branded = false
```

The FFmpeg configuration name selects additional codec sources; it does not
select Google Chrome assets or the Chrome for Testing build flavor. There is
no reason to enable either testing flag to obtain this media configuration.
This is configuration proof, not a claim that the installed browser now decodes
H.264/AAC or that redistribution requirements have been established.

## Evidence

The [controlled comparison](0004-2026-11-13-presentation-comparison-results.md)
found actual H.264/AAC MP4 decoding failed in both manual and managed StealthCDP,
while the existing Chrome reference decoded the clip. WebM decoded in all modes.
This isolates the missing capability from the ordinary popup-launcher repair.

Retained Chromium source at 15a1e89 shows these defaults:
`build/config/features.gni` derives proprietary_codecs from Chrome/Cast/testing
branding; `third_party/ffmpeg/ffmpeg_options.gni` chooses the Chromium FFmpeg
configuration when Chrome and testing branding are false. The controller's
current GN_ARGS omits explicit codec overrides. The original installed 156.73
output's complete GN metadata was not recovered, so this does not claim a fresh
resolved-argument readback for those original installed bytes.

Configuration generation used a clean verified automation checkout at
`e71aaa2a1effe15abe00fc43fc712acc961a28d4` (Chromium 157.0.8103.78), matching the
last controller context. Existing build outputs were preserved. The isolated
`out/CodecConfigProbe-20261113` uses the controller's official release GN_ARGS
plus only the two media overrides. `gn gen ... --fail-on-unused-args` exits 0;
`gn args ... --list --short` exits 0 and resolves the five values above exactly.
GN args SHA256: `4d636b9e7f9c86341d78a920fdb8c4e1b07c9b3eee82222db8df78d735047c89`.
No compiler, installer, release publication or activation was invoked.

Private request, GN log and qualification receipts are retained under
`~/.local/state/chromium-stealthcdp/popup693/codec-*`. An older qualification
checkout first failed Git preflight because its gitdir points at a removed
worktree record. That attempt stopped before GN generation; no source repair or
output overwrite was attempted. The succeeding check used the exact currently
verified source instead. A separate old-output metadata read was unavailable;
it is not presented as a passing installed configuration check.

The updater's existing 157.0.8103.78 run is failed at publish. This observation
neither invalidates the new GN configuration result nor establishes why publish
failed. The service, failed receipt and current installed activation are left
untouched; there was no automatic retry or requeue.

## Remaining acceptance

1. Build a new isolated candidate with the explicit codec settings while
   querying both testing flags false before compilation. Preserve the existing
   release, failed run, retained source and profiles.
2. Exercise actual AAC and H.264 decoding, not only canPlayType answers;
   replay the silent MP4/WebM fixtures and verify relevant media regressions.
3. Re-run StealthCDP active-CDP smoke, navigator.webdriver=false, source/queue
   identity and ordinary release acceptance on those exact candidate bytes.
4. Review component/distribution requirements before publication or automatic
   updater adoption. Widevine/CDM integration is a separate capability: the
   earlier CENC/H.264 EME rejection cannot distinguish missing codecs from CDMs.

At this original configuration checkpoint, the full build and adoption were
unexecuted. Candidate build/playback is now qualified in plan0015; installed
adoption was subsequently accepted after explicit operator cutover in plan0015.
Do not flip
release-controller defaults or claim MP4 support from GN generation alone.
The immediate Agent Browser popup repair is tracked separately in
[issue693](https://github.com/CochranResearchGroup/agent-browser/issues/693).

## Primary sources

- [Chromium media configuration](https://www.chromium.org/audio-video/).
- [Codec feature defaults](https://chromium.googlesource.com/chromium/src/+/main/build/config/features.gni).
- [FFmpeg configuration selection](https://chromium.googlesource.com/chromium/src/+/main/third_party/ffmpeg/ffmpeg_options.gni).
- [Local release configuration](../../../scripts/automation_pipeline.py).

External source mechanisms were researched in the prior cited research note;
this qualification reads exact local source and actual GN results. No new
claims about patent eligibility, Google branding rights or distribution terms
are inferred from build success.
