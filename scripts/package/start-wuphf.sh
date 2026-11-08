#!/bin/sh
set -eu
# Launch the unsigned bundle in place; operating-system approval is still required.
bundle=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
if [ ! -f "$bundle/WUPHF" ] || [ ! -d "$bundle/_internal" ]; then
    printf '%s\n' 'WUPHF bundle is incomplete. Extract the whole WUPHF folder again, including WUPHF and _internal. Keep it together in a permanent location before enabling checks.' >&2
    exit 1
fi
if [ ! -x "$bundle/WUPHF" ]; then
    printf '%s\n' 'WUPHF is not executable. Extract the original tar.gz archive with tar to preserve permissions; review the user guide and your system security policy.' >&2
    exit 1
fi
cd -- "$bundle"
exec "$bundle/WUPHF" "$@"
