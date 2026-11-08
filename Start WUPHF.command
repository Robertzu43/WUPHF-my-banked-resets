#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' >/dev/null 2>&1; then
  printf 'WUPHF needs Python 3.11 or newer. Install it from python.org/downloads, then reopen WUPHF. See README.md.\n'
  read -r -p 'Press Return to close... ' _
  exit 1
fi
if ! command -v codex >/dev/null; then
  printf 'WUPHF needs the Codex CLI. Install it and sign in, then reopen WUPHF. See README.md.\n'
  read -r -p 'Press Return to close... ' _
  exit 1
fi
python3 -m wuphf.web
