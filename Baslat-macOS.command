#!/bin/bash
set -eu
dw_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec bash "$dw_root/scripts/start_unix.sh" "$dw_root" "$@"
