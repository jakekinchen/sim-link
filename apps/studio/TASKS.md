# Studio Task Queue

States: `pending`, `in_progress`, `done`. One owner per task; update this file
in the same commit as the work.

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| ST1 | FastAPI server v0: `/api/status`, `/api/episodes`, `/api/episodes/{id}`, `/api/workcells`, `/api/tasks`, whitelisted `/api/media` | done | coordinator bootstrap |
| ST2 | Web scaffold: Vite + React + TS + Tailwind, layout shell, API client, dev proxy | done | design system in `web/src/components/ui.tsx` + `index.css` |
| ST3 | Dashboard page: current slice, window countdown, ladder gates, reviewer ticker | done | polls /api/status every 5s |
| ST4 | Episodes page: filter table + detail with mirror video, phase timeline, hash links | done | v0; expert frame scrubber included |
| ST5 | Tasks page: campaign history + before/after trend from result gates | done | v0 table; trend chart still open |
| ST6 | Workcell Designer: spec form/editor, Build button (server action), preview images, stability report | done | live API + browser verified: synced form/JSON, inline 400/422 faults, stable previews, settle report, hashes |
| ST7 | Agent Feed: briefs/session-logs/reviewer-decisions live tail | done | v0: names only; full-text rendering still open |
| ST8 | MCP server exposing status/episodes/tasks/workcells/build/render tools | pending | |
| ST9 | Robot panel: render discovery/census/calibration evidence read-only with permit-gated registration stub | pending | |
| ST10 | Three.js orbit viewer for compiled workcells | pending | reuse `threejs_export.py` |
| ST11 | Tauri wrap (native Mac shell) | pending | stretch |
| ST12 | Episode compare: two mirrors side-by-side, synced scrub | pending | stretch |

Rules: never touch governed paths (see GOAL.md), never push to
`codex/pi05-autolearn-loop`, commit small and often to `studio/app-shell`.
