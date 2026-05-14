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

Promoted Windows artifacts may be stored here for packaging, but installed
Windows executables should be copied to the Windows filesystem before use. The
default user-scoped install path for this WSL tenant is:

```text
/mnt/c/Users/ecoch/AppData/Local/chromium-stealthcdp/current/chrome.exe
```

Every promoted artifact must include:

- `manifest.json`
- `smoke.json`
- `patches/`
- `patches.sha256`
