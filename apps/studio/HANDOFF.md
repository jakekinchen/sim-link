# Studio Continuation Prompt

Paste everything below the line to the next agent.

---

You are continuing "SceneSmith Studio" — a local control-room web app over a
robot-learning foundry. The previous agents built a working v0; your job is to
extend it without breaking its boundaries.

## Ground rules (non-negotiable)

- Work EXCLUSIVELY in `/Users/kelly/Developer/sim-link-studio` (a git worktree
  on branch `studio/app-shell`). Commit small and often; push only to
  `studio/app-shell`.
- Read `apps/studio/GOAL.md`, `PLAN.md`, `TASKS.md` first — charter, plan, and
  live task queue. Update TASKS.md states in the same commits as the work.
- Never modify anything outside `apps/studio/**`. Never push to
  `codex/pi05-autolearn-loop` (an autonomous loop owns that branch in the
  sibling checkout `/Users/kelly/Developer/sim-link`, which you treat as a
  READ-ONLY data root).
- The repo's signed artifacts are the source of truth. The UI renders them.
  Only two write actions exist (workcell build, mirror render) and both go
  through the existing no-authority server endpoints. Do not add server
  endpoints that mutate the data root in any other way.

## Running the stack

- Backend: `cd apps/studio/server && .venv/bin/uvicorn main:app --port 8321`
  (FastAPI; reads live data from `SIM_LINK_DATA_ROOT`, default
  `/Users/kelly/Developer/sim-link`).
- Frontend: `cd apps/studio/web && bun install && bun run dev` → 5173, with a
  `/api` proxy to 8321. `bun run build` must stay green (tsconfig uses
  `erasableSyntaxOnly` — no TS parameter properties/enums).

## What exists (working, verified in browser)

- Server (`apps/studio/server/main.py`): `/api/status`, `/api/episodes`,
  `/api/episodes/{id}`, `/api/episodes/expert/<hash>/frame/{i}/{top|wrist}`,
  `/api/workcells`, `/api/tasks`, whitelisted `/api/media?path=...`,
  `POST /api/actions/build-workcell`, `POST /api/actions/render-mirror`.
- Web (`apps/studio/web/src/`): dark control-room design system
  (`components/ui.tsx`: Panel/Tag/PassFail/KV/Hash/Led/EmptyState/ErrorState;
  `lib/format.ts`: sci/fmtLocal/countdown/phaseColor/parseDocName/gateLabel;
  `api/client.ts`: typed client + `usePoll`; `state/StatusContext.tsx`).
  Pages: Dashboard (live slice + window countdowns + run state + feeds),
  Episodes (filter table), EpisodeDetail (mirror video player, phase-strip
  timeline, anchor-z sparkline, expert frame scrubber, signed-field grid),
  Tasks (result-gate table), Workcells (previews + stability), AgentFeed (v0).
  Match this idiom exactly — no component libraries, no light theme.

## Priority queue (see TASKS.md for the full list)

1. **ST6 Workcell Designer**: form + JSON editor for
   `scenesmith.workcell_arrangement_spec.v1` (see
   `configurations/robot_lab/workcell_spec_example.json` in the data root and
   the validator `scenesmith/robot_lab/workcell_spec_intake.py` — colors
   red/blue/green/yellow/purple/orange, cubes/trays with positions on the
   desk, task_prompt). Submit via `POST /api/actions/build-workcell`, then
   show the returned manifest: previews, per-cube settle stability, hashes.
   Handle 400/422 errors inline (the server returns the validator message).
2. **ST8 MCP server**: expose the same registry as MCP tools
   (`loop_status`, `list_episodes`, `get_episode`, `list_tasks`,
   `list_workcells`, `build_workcell`, `render_mirror`) via the official
   Python MCP SDK, stdio transport, as `apps/studio/server/mcp_server.py`;
   reuse the functions in `main.py` (refactor shared logic into a module both
   import — keep FastAPI behavior identical).
3. **ST7 upgrade**: Agent Feed should fetch and render brief/reviewer markdown
   full text (add a whitelisted server endpoint that serves only
   `docs/briefs/*.md` and `docs/reviewer-messages/*.md` file contents by
   name — filename regex-validated, no paths).
4. **ST5 upgrade**: campaign trend — small SVG chart of
   `final_to_baseline_objective_ratio` across gates ordered by task id, with
   the 0.10 Gate B threshold line.
5. **ST12 Episode compare**: route with two episode pickers, mirrors side by
   side, synced play/scrub.
6. **ST10 Three.js orbit viewer** for compiled workcells (the data root has
   `scenesmith/robot_lab/threejs_export.py`; if its output doesn't slot in
   cleanly, parse the workcell `scene.xml` boxes yourself — desk, trays,
   cubes as colored boxes is enough; the SO-101 can be a placeholder mesh).
7. **ST9 Robot panel** (read-only): render discovery/census/calibration
   evidence found under the data root's `configurations/robot_lab/`
   (calibration profile, camera identity bindings, static-pose sessions) with
   an explicitly disabled "register robot" flow labelled: requires a
   separately reviewed owner-present permit slice.
8. **ST11 Tauri wrap** (stretch, only if everything above is done).

## Verification bar for every task

`bun run build` green; page renders real data from the live API (curl the
endpoint and eyeball the page — screenshots if you have a browser tool);
TASKS.md updated; committed to `studio/app-shell` and pushed.
