#!/bin/sh
set -eu

project_root=${1:?usage: install_macos_launchd.sh PROJECT_ROOT}
if [ ! -f "$project_root/src/deal_watcher/scheduler.py" ]; then
  echo "Scheduler is not implemented yet; launchd installation is intentionally blocked." >&2
  exit 1
fi
template="$project_root/deployment/macos/com.dealwatcher.agent.plist.example"
target="$HOME/Library/LaunchAgents/com.dealwatcher.agent.plist"
mkdir -p "$HOME/Library/LaunchAgents"
sed "s|__PROJECT_ROOT__|$project_root|g" "$template" > "$target"
launchctl bootstrap "gui/$(id -u)" "$target"
