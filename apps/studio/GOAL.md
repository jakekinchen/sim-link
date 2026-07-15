# SceneSmith Studio - Track Charter

## Mission

Build the visual control layer for the SceneSmith workcell foundry: one local
app where an operator can watch live training/diagnostic activity, browse and
inspect every episode ever run, design new workcell arrangements visually,
track per-task learning progress, and (later) register and calibrate physical
robots. The studio is an agent workspace viewer first and a control surface
second.

## Non-Negotiable Boundaries

1. **The repository is the source of truth.** Signed artifacts under
   `configurations/robot_lab/`, episode stores and renders under
   `outputs/robot_lab/`, and the canonical docs (`GOAL.md`, ledger,
   `project_state.json`, briefs, reviewer messages) are authoritative. The
   studio renders them; it never re-signs, relabels, or reinterprets them.
2. **Read-only by construction, with two no-authority actions.** The studio
   may (a) write workcell arrangement drafts and invoke
   `scripts/robot_lab/build_workcell_from_spec.py`, and (b) request mirror
   renders via `scripts/robot_lab/render_rollout_mirror.py`. Both produce
   labelled fixtures/visualizations with zero authority. Training, hardware,
   promotion, and calibration actions remain exclusively owned by the
   executor/reviewer goal loop and the central authority composer.
3. **No collision with the autonomous loop.** Studio work happens only on the
   `studio/app-shell` branch in the `sim-link-studio` worktree, and only under
   `apps/studio/`. Studio code and agents never modify governed paths
   (`GOAL.md`, `configurations/robot_lab/`, `docs/autonomous-workflow/`,
   `docs/briefs/`, `docs/reviewer-messages/`, `docs/session-logs/`,
   `docs/manager-log/`, `scenesmith/robot_lab/`, `scripts/robot_lab/`, the
   goal-loop scripts, or the guarded tests) on any branch, and never push to
   `codex/pi05-autolearn-loop`.
4. **Live data comes from the main checkout.** The studio server reads
   `SIM_LINK_DATA_ROOT` (default `/Users/kelly/Developer/sim-link`) so the
   running loop's artifacts appear live. All reads are path-whitelisted; no
   file outside the data root is served.

## Done Means

An operator can open `localhost` and: see the loop's current slice, window
countdown, and capability-ladder state; browse expert/recovery/policy episodes
with mirror videos and trace summaries; design and build a new workcell from a
form or JSON and orbit its 3D preview; see per-task before/after progress from
signed result gates; and reach the same data through MCP tools. A Tauri wrap
of the same app is the optional native-Mac finish.
