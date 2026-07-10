#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="/tmp/autonomous-project-workflow/scenesmith-pi05"
BASELINE="${PI05_WORKTREE_BASELINE:-$RUNTIME_DIR/protected-worktree-baseline.json}"
PID_FILE="$RUNTIME_DIR/goal-loop.pid"
LOG_FILE="$RUNTIME_DIR/goal-loop.log"
GUARD="$ROOT/scripts/robot_lab/scoped_worktree_guard.py"
SCOPE="$ROOT/configurations/robot_lab/pi05_goal_loop_scope.json"

mkdir -p "$RUNTIME_DIR"
if [ -f "$PID_FILE" ]; then
  old_pid="$(cat "$PID_FILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    printf 'PI0.5 goal loop already running with pid %s\n' "$old_pid" >&2
    exit 1
  fi
  rm -f "$PID_FILE"
fi

python3 "$GUARD" snapshot --repo-root "$ROOT" --scope "$SCOPE" --baseline "$BASELINE"
nohup "$ROOT/scripts/run_pi05_pair_cycle.sh" --loop "$@" >> "$LOG_FILE" 2>&1 &
pid="$!"
printf '%s\n' "$pid" > "$PID_FILE"

printf 'Started scoped PI0.5 goal loop\n'
printf 'pid: %s\n' "$pid"
printf 'log: %s\n' "$LOG_FILE"
printf 'ledger: %s\n' "$ROOT/docs/autonomous-workflow/experience-compiler-twin-task-ledger.md"
