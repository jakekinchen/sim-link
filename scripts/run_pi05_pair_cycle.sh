#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="/tmp/autonomous-project-workflow/scenesmith-pi05"
BASELINE="${PI05_WORKTREE_BASELINE:-$RUNTIME_DIR/protected-worktree-baseline.json}"
GUARD="$ROOT/scripts/robot_lab/scoped_worktree_guard.py"
SCOPE="$ROOT/configurations/robot_lab/pi05_goal_loop_scope.json"
RUNNER="$ROOT/docs/autonomous-workflow/reusable/scripts/run-codex-pair-cycle.sh"

mkdir -p "$RUNTIME_DIR"
python3 "$GUARD" verify --repo-root "$ROOT" --scope "$SCOPE" --baseline "$BASELINE"

set +e
"$RUNNER" "$@" --root "$ROOT" --allow-dirty
runner_status=$?
set -e

python3 "$GUARD" verify --repo-root "$ROOT" --scope "$SCOPE" --baseline "$BASELINE"
exit "$runner_status"
