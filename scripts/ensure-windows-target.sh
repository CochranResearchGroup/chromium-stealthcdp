#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/ensure-windows-target.sh [--workspace PATH]

Ensures the Chromium .gclient file includes target_os = ['win'] so gclient can
sync the Windows cross-build dependencies from WSL.
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="$repo_root/.."

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace)
      workspace="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

gclient_file="$workspace/.gclient"
if [[ ! -f "$gclient_file" ]]; then
  echo ".gclient not found: $gclient_file" >&2
  exit 2
fi

python3 - "$gclient_file" <<'PY'
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
text = path.read_text()

match = re.search(r"(?m)^target_os\s*=\s*(\[[^\n]*\])\s*$", text)
if match:
    try:
        values = ast.literal_eval(match.group(1))
    except Exception as exc:
        raise SystemExit(f"could not parse existing target_os: {exc}")
    if "win" in values:
        print(f"{path}: target_os already includes win")
        raise SystemExit(0)
    values.append("win")
    replacement = "target_os = " + repr(values)
    text = text[: match.start()] + replacement + text[match.end() :]
else:
    if not text.endswith("\n"):
        text += "\n"
    text += "target_os = ['win']\n"

path.write_text(text)
print(f"{path}: added win to target_os")
PY
