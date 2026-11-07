#!/bin/bash
cd "$(dirname "$0")" || exit 1
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
if ! command -v python3 >/dev/null || ! command -v codex >/dev/null; then
  printf 'WUPHF needs Python 3 and the signed-in Codex CLI. See README.md.\n'
  read -r -p 'Press Return to close... ' _
  exit 1
fi
python3 -m wuphf.web
