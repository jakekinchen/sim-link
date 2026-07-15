# Studio Track Pointer

A second, parallel work track builds the visual control layer ("SceneSmith
Studio"): live loop dashboard, episode browser with mirror videos, per-task
progress, declarative workcell designer, robot evidence panel, and an MCP tool
surface.

- Branch: `studio/app-shell`; worktree `../sim-link-studio`; footprint
  `apps/studio/**` only.
- Charter, plan, and task queue: `apps/studio/{GOAL,PLAN,TASKS}.md` on that
  branch.
- The studio never modifies goal-loop governed paths, never pushes to
  `codex/pi05-autolearn-loop`, and treats this checkout as a read-only data
  root except the gitignored `outputs/robot_lab/{workcells,rollout_mirror}/`
  written through the existing no-authority CLIs.
- The goal loop should ignore `apps/**` and this file; no loop task depends on
  the studio, and no studio surface can grant training, hardware, transfer, or
  promotion authority.
