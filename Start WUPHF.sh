#!/bin/sh
set -eu
cd "$(dirname "$0")"
fail() {
  printf '%s\n' "$1" >&2
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
if [ "$runtime" != .venv/bin/python ]; then
  if ! "$runtime" -m venv .venv; then
    fail 'Could not create .venv in this source folder. Check folder permissions and install your distribution Python venv package if needed; preserve/rename any partial .venv before retrying. See README.md.'
  fi
  runtime=.venv/bin/python
  "$runtime" -c "$version_check" >/dev/null 2>&1 || fail 'The new .venv could not run Python 3.11+. Preserve/rename it before retrying. See README.md.'
fi
if ! "$runtime" -c 'import keyring' >/dev/null 2>&1; then
  if ! "$runtime" -m pip install -r requirements.txt; then
    fail 'Could not install requirements with .venv pip. Check the error above, network access, and Python pip/venv support; then reopen. See README.md.'
  fi
fi
exec "$runtime" -m wuphf.web
