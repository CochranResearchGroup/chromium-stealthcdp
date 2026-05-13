#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/smoke-windows.sh --chrome PATH [--output PATH] [--remote-debugging-address ADDR]

Launches a Windows chrome.exe from WSL through PowerShell, then validates over
CDP that navigator.webdriver evaluates to false.

By default Chrome binds CDP to 127.0.0.1 on the Windows host. If this WSL setup
cannot reach that loopback path, rerun with --remote-debugging-address 0.0.0.0
on a trusted machine/network.
EOF
}

chrome=""
output=""
remote_debugging_address="127.0.0.1"

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
    --remote-debugging-address)
      remote_debugging_address="${2:-}"
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

if [[ ! -f "$chrome" ]]; then
  echo "chrome.exe not found: $chrome" >&2
  exit 2
fi

powershell_cmd=""
for candidate in \
  powershell.exe \
  pwsh.exe \
  powershell \
  pwsh \
  "/mnt/c/Program Files/PowerShell/7/pwsh.exe" \
  /mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe; do
  if command -v "$candidate" >/dev/null 2>&1; then
    powershell_cmd="$candidate"
    break
  elif [[ -x "$candidate" ]]; then
    powershell_cmd="$candidate"
    break
  fi
done
if [[ -z "$powershell_cmd" ]]; then
  echo "required tool not found: powershell.exe or pwsh.exe" >&2
  exit 2
fi

for tool in wslpath node; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "required tool not found: $tool" >&2
    exit 2
  fi
done

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
chrome_abs="$(realpath "$chrome")"
chrome_dir="$(dirname "$chrome_abs")"
output="${output:-$repo_root/smoke-win.json}"
mkdir -p "$(dirname "$output")"

windows_temp="$("$powershell_cmd" -NoProfile -Command '[Console]::Out.Write($env:TEMP)')"
windows_temp_wsl="$(wslpath -u "$windows_temp")"
tmpdir="$(mktemp -d "$windows_temp_wsl/chromium-stealthcdp-smoke.XXXXXX")"
stage="$tmpdir/chrome-win64"
user_data="$tmpdir/user-data-win"
log="$tmpdir/chrome-win.log"
launch_json="$tmpdir/launch.json"
mkdir -p "$stage" "$user_data"
chrome_pid=""
cleanup() {
  if [[ -n "$chrome_pid" ]]; then
    "$powershell_cmd" -NoProfile -ExecutionPolicy Bypass \
      -File "$(wslpath -w "$repo_root/scripts/smoke-windows.ps1")" \
      -Mode Cleanup \
      -ProcessId "$chrome_pid" >/dev/null 2>&1 || true
  fi
  rm -rf "$tmpdir"
}
trap cleanup EXIT

runtime_files=(
  chrome.exe
  chrome.dll
  chrome_elf.dll
  chrome_100_percent.pak
  chrome_200_percent.pak
  d3dcompiler_47.dll
  dxcompiler.dll
  dxil.dll
  headless_command_resources.pak
  icudtl.dat
  libEGL.dll
  libGLESv2.dll
  resources.pak
  snapshot_blob.bin
  v8_context_snapshot.bin
  vk_swiftshader.dll
  vk_swiftshader_icd.json
  vulkan-1.dll
  msvcp140.dll
  msvcp140_atomic_wait.dll
  vccorlib140.dll
  vcruntime140.dll
  vcruntime140_1.dll
)

runtime_dirs=(
  locales
  resources
  MEIPreload
  PrivacySandboxAttestationsPreloaded
  hyphen-data
  IwaKeyDistribution
  swiftshader
)

for file in "${runtime_files[@]}"; do
  if [[ -e "$chrome_dir/$file" ]]; then
    cp -a "$chrome_dir/$file" "$stage/"
  fi
done

shopt -s nullglob
for manifest in "$chrome_dir"/*.manifest; do
  cp -a "$manifest" "$stage/"
done
shopt -u nullglob

for dir in "${runtime_dirs[@]}"; do
  if [[ -d "$chrome_dir/$dir" ]]; then
    cp -a "$chrome_dir/$dir" "$stage/"
  fi
done

stage_win="$(wslpath -w "$stage")"
"$powershell_cmd" -NoProfile -Command "\$path = '$stage_win'; icacls.exe \$path /grant '*S-1-15-2-1:(OI)(CI)(RX)' '*S-1-15-2-2:(OI)(CI)(RX)' /T /Q | Out-Null"

chrome_abs="$stage/chrome.exe"
if [[ ! -f "$chrome_abs" ]]; then
  echo "staged chrome.exe not found: $chrome_abs" >&2
  exit 1
fi

chrome_win="$(wslpath -w "$chrome_abs")"
user_data_win="$(wslpath -w "$user_data")"
log_win="$(wslpath -w "$log")"
script_win="$(wslpath -w "$repo_root/scripts/smoke-windows.ps1")"

started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

"$powershell_cmd" -NoProfile -ExecutionPolicy Bypass \
  -File "$script_win" \
  -Mode Launch \
  -ChromePath "$chrome_win" \
  -UserDataDir "$user_data_win" \
  -LogPath "$log_win" \
  -RemoteDebuggingAddress "$remote_debugging_address" > "$launch_json"

chrome_pid="$(node -e 'const fs=require("fs"); const j=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); console.log(j.processId || "");' "$launch_json")"
version="$(node -e 'const fs=require("fs"); const j=JSON.parse(fs.readFileSync(process.argv[1],"utf8")); console.log((j.chromeVersion || "").trim());' "$launch_json")"

for _ in $(seq 1 150); do
  if [[ -s "$user_data/DevToolsActivePort" ]]; then
    break
  fi
  sleep 0.1
done

if [[ ! -s "$user_data/DevToolsActivePort" ]]; then
  echo "timed out waiting for DevToolsActivePort" >&2
  cat "$launch_json" >&2 || true
  cat "$log" >&2 || true
  exit 1
fi

port="$(sed -n '1p' "$user_data/DevToolsActivePort")"
windows_host="$(awk '/^nameserver / { print $2; exit }' /etc/resolv.conf 2>/dev/null || true)"
connect_hosts="127.0.0.1,localhost"
if [[ -n "$windows_host" ]]; then
  connect_hosts="$connect_hosts,$windows_host"
fi

eval_json="$(node - "$port" "$connect_hosts" <<'NODE'
const port = process.argv[2];
const hosts = process.argv[3].split(',').filter(Boolean);
const timeout = setTimeout(() => {
  console.error('timed out waiting for CDP evaluation');
  process.exit(3);
}, 10000);

async function fetchTargets() {
  const errors = [];
  for (const host of hosts) {
    try {
      const response = await fetch(`http://${host}:${port}/json/list`, { signal: AbortSignal.timeout(1500) });
      if (!response.ok) {
        errors.push(`${host}: /json/list returned ${response.status}`);
        continue;
      }
      return { host, targets: await response.json() };
    } catch (error) {
      errors.push(`${host}: ${error.message}`);
    }
  }
  throw new Error(`unable to reach CDP: ${errors.join('; ')}`);
}

async function main() {
  const { host, targets } = await fetchTargets();
  const target = targets.find((item) => item.type === 'page') || targets[0];
  if (!target || !target.webSocketDebuggerUrl) {
    throw new Error('no CDP page target with a WebSocket URL');
  }

  const wsUrl = target.webSocketDebuggerUrl.replace(/127\.0\.0\.1|localhost/, host);
  const ws = new WebSocket(wsUrl);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = () => reject(new Error(`WebSocket connection failed: ${wsUrl}`));
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
  console.log(JSON.stringify({ value, host }));
}

main().catch((error) => {
  clearTimeout(timeout);
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
NODE
)"

value="$(node -e 'const input = JSON.parse(process.argv[1]); console.log(String(input.value));' "$eval_json")"
cdp_host="$(node -e 'const input = JSON.parse(process.argv[1]); console.log(input.host || "");' "$eval_json")"
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
CDP_HOST="$cdp_host" \
WEBDRIVER_VALUE="$value" \
SUCCESS="$success" \
REMOTE_DEBUGGING_ADDRESS="$remote_debugging_address" \
node - "$output" <<'NODE'
const fs = require('fs');
const output = process.argv[2];
const data = {
  schema: 'chromium-stealthcdp.smoke.v1',
  platform: 'win',
  success: process.env.SUCCESS === 'true',
  chromePath: process.env.CHROME_PATH,
  chromeVersion: process.env.CHROME_VERSION,
  startedAt: process.env.STARTED_AT,
  finishedAt: process.env.FINISHED_AT,
  checks: {
    versionRuns: Boolean(process.env.CHROME_VERSION),
    cdpReachable: true,
    navigatorWebdriver: process.env.WEBDRIVER_VALUE,
    navigatorWebdriverExpected: 'false',
  },
  devtoolsPort: Number(process.env.DEVTOOLS_PORT),
  cdpHost: process.env.CDP_HOST,
  remoteDebuggingAddress: process.env.REMOTE_DEBUGGING_ADDRESS,
};
fs.writeFileSync(output, JSON.stringify(data, null, 2) + '\n');
NODE

if [[ "$success" != "true" ]]; then
  echo "windows smoke failed: navigator.webdriver=$value" >&2
  exit 1
fi

echo "windows smoke passed: navigator.webdriver=false"
echo "wrote $output"
