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

has_model=0
for argument in "$@"; do
  if [ "$argument" = "--model" ]; then
    has_model=1
  fi
done
model_args=()
if [ "$has_model" -eq 0 ]; then
  model_args=(--model "${PI05_CODEX_MODEL:-gpt-5.4}")
fi

set +e
"$RUNNER" "$@" "${model_args[@]}" --ignore-user-config --root "$ROOT" --allow-dirty
runner_status=$?
set -e

python3 "$GUARD" verify --repo-root "$ROOT" --scope "$SCOPE" --baseline "$BASELINE"
exit "$runner_status"
