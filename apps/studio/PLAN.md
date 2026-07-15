# SceneSmith Studio - Plan

## Shell Decision: Localhost Web Now, Tauri Wrap Optional

For the hackathon, a localhost web app wins over a native Mac app:

| Concern | Web (Vite + React) | Native Mac (Swift/AppKit) |
| --- | --- | --- |
| Iteration speed | Hot reload; agents build and verify headlessly | Xcode builds, signing, slow agent loop |
| 3D scene viewing | Three.js is mature; `threejs_export.py` already exists in-repo | SceneKit port from scratch |
| Video/trace display | Native `<video>` + canvas charts | AVKit plumbing |
| Hardware access | Irrelevant — Python backend owns serial/cameras either way | Same backend; native buys nothing |
| Demo/judging | Any browser, shareable, screenshots trivial | Install/run friction |
| "Feels like a product" | Tauri wrap at the end gives a real Mac app in hours | Native from day one costs the week |

The one real native advantage (device-permission UX and menu-bar polish) lives
in the Python backend regardless, because pyserial/AVFoundation access is
already implemented in the existing repo code. Decision: **FastAPI backend +
Vite/React/TypeScript/Tailwind frontend + Three.js**, with a Tauri wrap as the
final optional milestone.

## Architecture

```text
main checkout (live loop writes artifacts)
  /Users/kelly/Developer/sim-link
        │  read-only, path-whitelisted
        ▼
studio server (FastAPI, apps/studio/server)
  - artifact indexer: episodes, traces, mirrors, workcells, result gates
  - status: ledger front matter + project_state window/task parsing
  - media: mp4/png serving, base64-frame decoding on demand
  - actions (no-authority only): build workcell drafts, request mirror renders
  - MCP server: same registry exposed as typed tools
        │  REST + polling (WS later)
        ▼
studio web (Vite + React + TS + Tailwind, apps/studio/web)
  Dashboard | Event Ledger | Episodes | Tasks | Workcell Designer | Robot | Agent Feed
```

## Sections

1. **Dashboard** — current slice + brief objective, run-window countdown,
   capability-ladder gate states, last N reviewer decisions, commit ticker.
2. **Episodes** — filterable table (source: expert/recovery/policy; seed;
   task phase; outcome; strict-v2 gates) over the scripted store, recovery
   package, and closed-loop traces; detail view plays the mirror MP4, shows
   per-frame phase/contact timeline, joint-error sparklines, and links every
   identity hash back to its signed artifact.
3. **Tasks** — one card per task family/dataset: episode counts, campaign
   history from signed result gates (objective ratios, strict successes,
   before/after pairs), trend chart across campaigns.
4. **Workcell Designer** — form + JSON editor for
   `scenesmith.workcell_arrangement_spec.v1`; Build calls the existing
   builder; shows stability results and preview renders; Three.js orbit view
   of the compiled scene (via `threejs_export.py` output or glTF later).
5. **Robot** — registration/calibration surface. v0 renders existing evidence
   only: discovery/census artifacts, camera identity bindings, calibration
   profile, static-pose sessions. The "plug in and register" flow stays
   disabled until a separately reviewed owner-present permit slice exists;
   the panel must say exactly that.
6. **Agent Feed** — live tail of briefs, session logs, and reviewer decisions
   rendered as a conversation; this is the multimodal-agent window.
7. **Event Ledger & Inspector** — read-only observed chronology across briefs,
   reviewer decisions, session logs, and manager interventions. The split-pane
   inspector renders exact source text plus filename, byte count, and SHA-256;
   filesystem time is labelled as observation order and never promoted into
   evidence time or authority.

## MCP Surface (server milestone S4)

Tools mirroring the REST API: `loop_status`, `list_episodes`, `get_episode`,
`list_tasks`, `list_workcells`, `build_workcell(spec)`, `render_mirror(trace)`.
Same whitelists, same no-authority rule. This lets any MCP client (Claude,
etc.) drive the studio programmatically — the "agent workspace" contract.

## Collision Contract With The Goal Loop

- Branch `studio/app-shell`, worktree `../sim-link-studio`, footprint
  `apps/studio/**` only (plus `docs/studio-track.md` on main, owned by the
  coordinator). Governed prefixes listed in the charter are never touched.
- The studio server treats the main checkout as read-only except
  `outputs/robot_lab/workcells/` and `outputs/robot_lab/rollout_mirror/`
  (both gitignored), written only through the two existing no-authority CLIs.
- Merges to main are path-disjoint from loop commits by construction.

## Milestones

- **S1 (today):** server v0 — status, episodes, workcells, media endpoints
  against live data; web v0 — Dashboard + Episodes list/detail with mirror
  video playback.
- **S2 (today):** Tasks progress view from signed result gates; Agent Feed.
- **S3 (tonight):** Workcell Designer with build action + preview images;
  Three.js orbit view if `threejs_export` output slots in cleanly.
- **S4:** MCP server exposing the tool surface.
- **S5:** Robot panel rendering existing hardware evidence read-only.
- **S6 (stretch):** Tauri wrap for the native Mac shell; episode compare view
  (two mirrors side by side); live WS push instead of polling.
