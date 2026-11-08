#!/bin/sh
set -eu
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null || ! command -v codex >/dev/null; then
  printf '%s\n' 'WUPHF needs Python 3.11+ and the signed-in Codex CLI. See README.md.'
  exit 1
fi
python3 -c 'import sys; assert sys.version_info >= (3,11), "Python 3.11 or newer is required"'
if [ ! -x .venv/bin/python ]; then python3 -m venv .venv; fi
if ! .venv/bin/python -c 'import keyring' >/dev/null 2>&1; then
  .venv/bin/python -m pip install -r requirements.txt
fi
exec .venv/bin/python -m wuphf.web
