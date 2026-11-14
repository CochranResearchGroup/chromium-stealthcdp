#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/build.sh [--src PATH] [--out OUT] [--target TARGET] [--target-os linux|win] [--depot-tools PATH] [--gn-args TEXT]

Generates GN args when needed and builds a patched Chromium checkout.
Chrome for Testing is prohibited; both testing flags must resolve to false.

Defaults:
  linux: --out out/Default --target chrome
  win:   --out out/WinStealthCDP --target chrome
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
src="$repo_root/../src"
out=""
target="chrome"
target_os="linux"
depot_tools="${DEPOT_TOOLS:-}"
gn_args=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --src)
      src="${2:-}"
      shift 2
      ;;
    --out)
      out="${2:-}"
      shift 2
      ;;
    --target)
      target="${2:-}"
      shift 2
      ;;
    --target-os)
      target_os="${2:-}"
      shift 2
      ;;
    --depot-tools)
      depot_tools="${2:-}"
      shift 2
      ;;
    --gn-args)
      gn_args="${2:-}"
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

if [[ ! -d "$src/.git" ]]; then
  echo "Chromium src checkout not found: $src" >&2
  exit 2
fi

if [[ -z "$depot_tools" ]]; then
  for candidate in \
    "$repo_root/../../depot_tools" \
    "$HOME/workspace.local/depot_tools" \
    "$HOME/.config/depot_tools"; do
    if [[ -d "$candidate" ]]; then
      depot_tools="$candidate"
      break
    fi
  done
fi

if [[ -n "$depot_tools" ]]; then
  export PATH="$depot_tools:$PATH"
fi

if [[ -d "$src/buildtools/linux64" ]]; then
  export PATH="$src/buildtools/linux64:$PATH"
fi

for tool in gn autoninja; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "required Chromium build tool not found: $tool" >&2
    exit 2
  fi
done

case "$target_os" in
  linux)
    out="${out:-out/Default}"
    gn_args="${gn_args:-is_debug=false symbol_level=0 is_component_build=false}"
    ;;
  win)
    out="${out:-out/WinStealthCDP}"
    gn_args="${gn_args:-target_os=\"win\" target_cpu=\"x64\" is_debug=false symbol_level=0 is_component_build=false}"
    ;;
  *)
    echo "unsupported target OS: $target_os" >&2
    exit 2
    ;;
esac

gn_args="$gn_args is_chrome_for_testing=false is_chrome_for_testing_branded=false"

out_dir="$src/$out"

if [[ ! -f "$out_dir/args.gn" ]]; then
  (
    cd "$src"
    gn gen "$out" --args="$gn_args"
  )
else
  echo "using existing GN args: $out_dir/args.gn"
fi

# Query resolved GN values, including imported args and Chromium defaults.
# Refuse unsafe existing outputs rather than silently rewriting their configuration.
for flag in is_chrome_for_testing is_chrome_for_testing_branded; do
  resolved="$(cd "$src" && gn args "$out" "--list=$flag" --short)"
  if [[ ! "$resolved" =~ ^[[:space:]]*$flag[[:space:]]*=[[:space:]]*false[[:space:]]*$ ]]; then
    echo "Chrome for Testing is prohibited: $flag must resolve to false in $out_dir" >&2
    exit 2
  fi
done

(
  cd "$src"
  autoninja -C "$out" "$target"
)
