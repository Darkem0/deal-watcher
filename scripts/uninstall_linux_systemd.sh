#!/bin/sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
project_root=${1:-$(dirname -- "$script_dir")}
exec "$project_root/.venv/bin/python" "$script_dir/manage_service.py" uninstall --platform linux --project-root "$project_root"
