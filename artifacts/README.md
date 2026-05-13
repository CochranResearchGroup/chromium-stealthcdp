# Artifacts

This directory documents the artifact contract. Large promoted Chromium builds
are not tracked in git.

Default local artifact root:

```text
/home/ecochran76/workspace.local/chromium/artifacts/chromium-stealthcdp/
```

The stable executable path for local consumers is:

```text
/home/ecochran76/workspace.local/chromium/artifacts/chromium-stealthcdp/current/chrome-linux/chrome
```

Every promoted artifact must include:

- `manifest.json`
- `smoke.json`
- `patches/`
- `patches.sha256`
