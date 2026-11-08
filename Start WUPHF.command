#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
fail() {
  printf '%s\n' "$1" >&2
  if [ -t 0 ]; then read -r -p 'Press Return to close... ' _; fi
  exit 1
}
version_check='import sys; sys.exit(sys.version_info < (3, 11))'
if [ -n "${WUPHF_PYTHON:-}" ]; then
  if ! "$WUPHF_PYTHON" -c "$version_check" >/dev/null 2>&1; then
    fail 'WUPHF_PYTHON must name one working Python 3.11+ executable (a path may contain spaces). Correct or unset it, then reopen. See README.md.'
  fi
fi
if [ -e .venv ] || [ -L .venv ]; then
  if ! .venv/bin/python -c "$version_check" >/dev/null 2>&1; then
    fail 'The existing .venv is old, broken, or moved. Keep this source folder in its final location; rename .venv to preserve it, then reopen with Python 3.11+. No files were removed. See README.md.'
  fi
  runtime=.venv/bin/python
else
  runtime=${WUPHF_PYTHON:-}
  if [ -z "$runtime" ]; then
    for candidate in python3 python3.13 python3.11 python3.14 python3.12 python3.15 python; do
      if "$candidate" -c "$version_check" >/dev/null 2>&1; then
        runtime=$candidate
        break
      fi
    done
  fi
  [ -n "$runtime" ] || fail 'WUPHF source needs an existing Python 3.11+ runtime. Use a compatible WUPHF bundle, or install Python separately and set WUPHF_PYTHON to its executable. See README.md.'
fi
if ! command -v codex >/dev/null 2>&1; then
  fail 'WUPHF needs the Codex CLI. Install it and sign in, then reopen WUPHF. See README.md.'
fi
exec "$runtime" -m wuphf.web
