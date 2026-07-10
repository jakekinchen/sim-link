#!/usr/bin/env bash
set -euo pipefail

RUNTIME_DIR="/tmp/autonomous-project-workflow/scenesmith-pi05"
PID_FILE="$RUNTIME_DIR/goal-loop.pid"

if [ ! -f "$PID_FILE" ]; then
  printf 'No scoped PI0.5 goal loop pid file found.\n'
  exit 0
fi

pid="$(cat "$PID_FILE")"
if kill -0 "$pid" 2>/dev/null; then
  kill "$pid"
  printf 'Stopped scoped PI0.5 goal loop pid %s.\n' "$pid"
else
  printf 'Scoped PI0.5 goal loop pid %s was not running.\n' "$pid"
fi
rm -f "$PID_FILE"
