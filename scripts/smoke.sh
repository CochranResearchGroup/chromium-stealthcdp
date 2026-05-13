#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/smoke.sh --chrome PATH [--output PATH]

Runs the chromium-stealthcdp promotion smoke:
  - launch Chromium headless with an ephemeral CDP port
  - evaluate navigator.webdriver through CDP
  - write machine-readable smoke JSON
EOF
}

chrome=""
output=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --chrome)
      chrome="${2:-}"
      shift 2
      ;;
    --output)
      output="${2:-}"
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

if [[ -z "$chrome" ]]; then
  echo "--chrome is required" >&2
  exit 2
fi

if [[ ! -x "$chrome" ]]; then
  echo "chrome is not executable: $chrome" >&2
  exit 2
fi

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chrome_abs="$(realpath "$chrome")"
output="${output:-$repo_root/smoke.json}"
mkdir -p "$(dirname "$output")"

tmpdir="$(mktemp -d)"
log="$tmpdir/chrome.log"
chrome_pid=""
cleanup() {
  if [[ -n "$chrome_pid" ]] && kill -0 "$chrome_pid" 2>/dev/null; then
    kill "$chrome_pid" 2>/dev/null || true
    wait "$chrome_pid" 2>/dev/null || true
  fi
  rm -rf "$tmpdir"
}
trap cleanup EXIT

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
version="$("$chrome_abs" --version | sed 's/[[:space:]]*$//')"

"$chrome_abs" \
  --headless=new \
  --disable-gpu \
  --no-sandbox \
  --disable-dev-shm-usage \
  --remote-debugging-port=0 \
  --user-data-dir="$tmpdir/user-data" \
  about:blank >"$log" 2>&1 &
chrome_pid=$!

for _ in $(seq 1 100); do
  if [[ -s "$tmpdir/user-data/DevToolsActivePort" ]]; then
    break
  fi
  if ! kill -0 "$chrome_pid" 2>/dev/null; then
    echo "chrome exited before DevToolsActivePort was written" >&2
    cat "$log" >&2 || true
    exit 1
  fi
  sleep 0.1
done

if [[ ! -s "$tmpdir/user-data/DevToolsActivePort" ]]; then
  echo "timed out waiting for DevToolsActivePort" >&2
  cat "$log" >&2 || true
  exit 1
fi

port="$(sed -n '1p' "$tmpdir/user-data/DevToolsActivePort")"

eval_json="$(node - "$port" <<'NODE'
const port = process.argv[2];
const timeout = setTimeout(() => {
  console.error('timed out waiting for CDP evaluation');
  process.exit(3);
}, 5000);

async function main() {
  const listResponse = await fetch(`http://127.0.0.1:${port}/json/list`);
  if (!listResponse.ok) {
    throw new Error(`/json/list returned ${listResponse.status}`);
  }
  const targets = await listResponse.json();
  const target = targets.find((item) => item.type === 'page') || targets[0];
  if (!target || !target.webSocketDebuggerUrl) {
    throw new Error('no CDP page target with a WebSocket URL');
  }

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = () => reject(new Error('WebSocket connection failed'));
  });

  const result = await new Promise((resolve, reject) => {
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.id === 1) {
        resolve(message);
      }
    };
    ws.onerror = () => reject(new Error('WebSocket evaluation failed'));
    ws.send(JSON.stringify({
      id: 1,
      method: 'Runtime.evaluate',
      params: {
        expression: 'navigator.webdriver',
        returnByValue: true,
      },
    }));
  });

  ws.close();
  clearTimeout(timeout);
  const value = result.result && result.result.result
    ? result.result.result.value
    : undefined;
  console.log(JSON.stringify({ value }));
}

main().catch((error) => {
  clearTimeout(timeout);
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
NODE
)"

value="$(node -e 'const input = JSON.parse(process.argv[1]); console.log(String(input.value));' "$eval_json")"
finished_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

success=false
if [[ "$value" == "false" ]]; then
  success=true
fi

CHROME_PATH="$chrome_abs" \
CHROME_VERSION="$version" \
STARTED_AT="$started_at" \
FINISHED_AT="$finished_at" \
DEVTOOLS_PORT="$port" \
WEBDRIVER_VALUE="$value" \
SUCCESS="$success" \
node - "$output" <<'NODE'
const fs = require('fs');
const output = process.argv[2];
const data = {
  schema: 'chromium-stealthcdp.smoke.v1',
  success: process.env.SUCCESS === 'true',
  chromePath: process.env.CHROME_PATH,
  chromeVersion: process.env.CHROME_VERSION,
  startedAt: process.env.STARTED_AT,
  finishedAt: process.env.FINISHED_AT,
  checks: {
    versionRuns: true,
    cdpReachable: true,
    navigatorWebdriver: process.env.WEBDRIVER_VALUE,
    navigatorWebdriverExpected: 'false',
  },
  devtoolsPort: Number(process.env.DEVTOOLS_PORT),
};
fs.writeFileSync(output, JSON.stringify(data, null, 2) + '\n');
NODE

if [[ "$success" != "true" ]]; then
  echo "smoke failed: navigator.webdriver=$value" >&2
  exit 1
fi

echo "smoke passed: navigator.webdriver=false"
echo "wrote $output"
