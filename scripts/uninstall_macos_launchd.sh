#!/bin/sh
set -eu

target="$HOME/Library/LaunchAgents/com.dealwatcher.agent.plist"
if [ -f "$target" ]; then
  launchctl bootout "gui/$(id -u)" "$target" 2>/dev/null || true
  rm -f "$target"
fi
