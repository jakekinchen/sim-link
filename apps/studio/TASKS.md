# Studio Task Queue

States: `pending`, `in_progress`, `done`. One owner per task; update this file
in the same commit as the work.

| ID | Task | State | Notes |
| --- | --- | --- | --- |
| ST1 | FastAPI server v0: `/api/status`, `/api/episodes`, `/api/episodes/{id}`, `/api/workcells`, `/api/tasks`, whitelisted `/api/media` | done | coordinator bootstrap |
| ST2 | Web scaffold: Vite + React + TS + Tailwind, layout shell, API client, dev proxy | done | design system in `web/src/components/ui.tsx` + `index.css` |
| ST3 | Dashboard page: current slice, window countdown, ladder gates, reviewer ticker | done | polls /api/status every 5s |
| ST4 | Episodes page: filter table + detail with mirror video, phase timeline, hash links | done | v0; expert frame scrubber included |
| ST5 | Tasks page: campaign history + before/after trend from result gates | done | live SVG trend: signed measured ratios only, task order, 0.10 Gate B objective threshold |
| ST6 | Workcell Designer: spec form/editor, Build button (server action), preview images, stability report | done | live API + browser verified: synced form/JSON, inline 400/422 faults, stable previews, settle report, hashes |
| ST7 | Agent Feed: briefs/session-logs/reviewer-decisions live tail | done | regex filename-only brief/reviewer reads; live full-text safe Markdown feed browser-verified |
| ST8 | MCP server exposing status/episodes/tasks/workcells/build/render tools | done | official SDK stdio verified: 7 tools, 5 live reads, fail-closed guards, stable workcell build; REST parity exact |
| ST9 | Robot panel: render discovery/census/calibration evidence read-only with permit-gated registration stub | done | fixed signed-artifact whitelist; 2 cameras/6 servos/6 calibration joints; disabled permit stub; no device access or registration endpoint |
| ST10 | Three.js orbit viewer for compiled workcells | done | live lazy Three.js viewer: whitelisted XML, 14 boxes/2 cubes/2 trays, orbit/reset, canvas cleanup |
| ST11 | Tauri wrap (native Mac shell) | done | signed `.app` verified: fixed loopback Python sidecar, live API/AX render, shutdown cleanup; webview has no shell capability |
| ST12 | Episode compare: two mirrors side-by-side, synced scrub | done | live browser verified: distinct pickers, side-by-side mirrors, shared play/end, exact 4.2s dual scrub |

Rules: never touch governed paths (see GOAL.md), never push to
`codex/pi05-autolearn-loop`, commit small and often to `studio/app-shell`.
