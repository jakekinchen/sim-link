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
| ST7 | Agent Feed: briefs/session-logs/reviewer-decisions live tail | done | all promised channels plus manager interventions; filename-only full-text safe Markdown feed browser-verified |
| ST8 | MCP server exposing status/episodes/tasks/workcells/build/render tools | done | official SDK stdio verified: 7 tools, 5 live reads, fail-closed guards, stable workcell build; REST parity exact |
| ST9 | Robot panel: render discovery/census/calibration evidence read-only with permit-gated registration stub | done | fixed signed-artifact whitelist; 2 cameras/6 servos/6 calibration joints; disabled permit stub; no device access or registration endpoint |
| ST10 | Three.js orbit viewer for compiled workcells | done | live lazy Three.js viewer: whitelisted XML, 14 boxes/2 cubes/2 trays, orbit/reset, canvas cleanup |
| ST11 | Tauri wrap (native Mac shell) | done | signed `.app` verified: fixed loopback Python sidecar, live API/AX render, shutdown cleanup; webview has no shell capability |
| ST12 | Episode compare: two mirrors side-by-side, synced scrub | done | live browser verified: distinct pickers, side-by-side mirrors, shared play/end, exact 4.2s dual scrub |
| ST13 | Event Ledger & Inspector: canonical workflow timeline, provenance, filters, full-text source inspection | done | 656 live docs across 4 channels; search/filter, rendered/raw source, SHA-256 consistency, and observation-time disclaimer browser-verified |
| ST14 | Native shell lifecycle diagnostics: visible sidecar startup, health, logs, and exit state | done | signed app/AX verified: exact ready/fault/exit states, bounded lifecycle logs, named port conflict, and shutdown cleanup; no webview process capability |
| ST15A | Event-sourced simulation spine: approve architecture and authority boundary | pending | planning only; requires an explicit owner-approved charter expansion before any command endpoint or runtime mutation is implemented |
| ST15B | Event contracts, SQLite append-only store, and deterministic replay | pending | blocked by ST15A; programmatic writes only, agent-facing MCP/API tools, generated Markdown summaries, retention, migrations, ordering, and replay tests first |
| ST15C | Deterministic simulated machines, state machines, and command router | pending | blocked by ST15B; simulation-only actors and commands; no hardware, training, promotion, or goal-loop authority |
| ST15D | Runtime REST/WebSocket transport and 5-10 Hz telemetry | pending | blocked by ST15C; cursor catch-up plus live push; no Kafka/Redpanda until the end-to-end local loop is proven |
| ST15E | World-first Studio Operations canvas and runtime-event projection | pending | blocked by ST15D; interactive 3D actors, lifecycle motion, spatial HUD, replay timeline, and inspector drawer; operational stream stays separate from signed evidence |
| ST15F | End-to-end replay/idempotency/staleness demo and proof package | pending | blocked by ST15E; browser demo, restart/replay equality, regression gate, documented limits, scoped commits, and remote preservation |
| ST16 | Foundry Stage visual shell reframe over existing read-only artifacts | in_progress | world-first home, always-on 3D workcell, useful replay projection, spatial workflow ribbon, direct manipulation, responsive/reduced-motion proof; no new server mutation |

Rules: never touch governed paths (see GOAL.md), never push to
`codex/pi05-autolearn-loop`, commit small and often to `studio/app-shell`.

## ST15 - Event-Sourced Command And Telemetry Spine

### Why this is queued

The proposed feature is the strongest next backend/system-design interview
signal: a live operational runtime where commands, state transitions, and
telemetry are represented as durable events and the current state can be
rebuilt by replay. It is a genuinely new capability, not a rename or minor
upgrade of ST13.

The external feature proposal described a repository with a Hydra-style batch
runner and no FastAPI or streaming dependency. That premise is not fully
current for SceneSmith Studio: `apps/studio/server/main.py` is already a
FastAPI transport and `apps/studio/server/pyproject.toml` already includes
FastAPI and Uvicorn. The important capability gap is still real: Studio has no
database event store, command router, simulated-machine state machines,
durable command lifecycle, replay engine, or WebSocket telemetry stream.

### What ST13 implemented - and what it did not

ST13 is a repository-backed evidence projection and source inspector:

- It indexes four canonical Markdown stores: briefs, reviewer decisions,
  session logs, and manager interventions.
- Its identifier is `kind/filename`; the three-digit filename number is local
  to a document channel, not a global runtime sequence.
- It computes exact source SHA-256, byte count, title, optional decision, and
  optional recorded date.
- It orders the combined rail by filesystem modification time and explicitly
  labels that value `filesystem_mtime_observation_not_evidence_time`.
- It serves a bounded, filename-only, path-whitelisted read API and verifies
  that the indexed hash still matches the document opened in the inspector.
- The web client refreshes `/api/events` every five seconds. This is 0.2 Hz
  REST polling of workflow documents, not 5-10 Hz machine telemetry.
- Its tests cover source fidelity, bounded limits, malformed paths, symlink
  escape rejection, and whitelisted document access.

ST13 does **not** append events, persist operational state, accept machine
commands, assign command IDs, expose command lifecycle events, maintain a
per-machine sequence, reject stale telemetry, publish over WebSocket, or
rebuild state by replay. Its signed-artifact provenance and fail-closed access
controls should be preserved as strengths, but they do not constitute event
sourcing.

### Authority decision required before implementation

This queue entry is a design record, not implementation authority. The current
Studio charter permits only two no-authority writes: workcell fixture builds
and mirror renders. Adding `start`, `pause`, `resume`, `reset`, `estop`,
`move_object`, or `run_task` as mutating Studio endpoints would violate that
charter unless the owner explicitly approves a new slice and amends the
boundary.

If approved, the safe architecture is a separate **simulation-only runtime
producer** with Studio as a read-only subscriber/projection:

```text
simulation runtime (new authority-owning service)
  commands -> router -> machine state machines -> append-only SQLite events
                               |                         |
                               |                         +-> deterministic replay
                               +-> 5-10 Hz telemetry -> WebSocket
                                                            |
                                                            v
SceneSmith Studio (read-only consumer)
  Operations view + runtime inspector     existing signed-evidence Event Ledger
              operational data            repository evidence / authority records
```

Non-negotiable proof separation:

- Every runtime event must say `source: simulation`.
- Operational events must never be relabelled as signed repository evidence,
  physical proof, policy success, promotion evidence, or authority.
- Physical robot access, serial/camera access, optimizer training, checkpoint
  promotion, calibration mutation, and the autonomous goal loop remain out of
  scope and closed.
- The existing `/api/events` evidence registry remains repository-backed and
  read-only. Runtime events receive a separate route and UI lane.
- The existing two Studio actions remain the only writes until ST15A records a
  reviewed replacement boundary.

### Proposed code footprint after ST15A approval

Keep the capability isolated rather than folding command state into the
artifact registry:

```text
apps/studio/runtime/
  simulator/
    machine_sim.py
    scenarios.py
  control/
    command_models.py
    state_machine.py
    command_router.py
  events/
    event_store.py
    schemas.py
    replay.py
  api/
    server.py
    websocket.py
  tests/
    test_command_idempotency.py
    test_state_transitions.py
    test_stale_telemetry.py
    test_event_ordering.py
    test_replay.py
    test_websocket_catchup.py
```

The exact footprint is part of ST15A. No file in this proposed tree should be
created before the authority decision is recorded.

### Minimum worthwhile runtime

1. Run three deterministic simulated workcell/robot actors concurrently.
2. Emit telemetry at a configured 5-10 Hz per actor.
3. Support exactly these commands for the first slice:
   `start`, `pause`, `resume`, `reset`, `estop`, `move_object`, and
   `run_task`.
4. Give every submitted command a UUID `command_id`. A repeated ID with the
   same payload returns the prior result without another state transition; a
   repeated ID with a different payload is rejected as a conflict.
5. Represent every command outcome with durable lifecycle events:
   `command.accepted`, `command.rejected`, `command.executing`,
   `command.succeeded`, or `command.failed`.
6. Persist all command, transition, and telemetry events in SQLite. Use WAL
   mode and transactions; keep Postgres as a later adapter, not an MVP
   dependency.
7. Stream new events and latest derived machine state over WebSocket, with a
   durable cursor so reconnecting clients fetch the missed range before
   resuming live delivery.
8. Rebuild the same machine state deterministically from sequence zero after a
   process restart.

Do not add Kafka, Redpanda, RabbitMQ, a schema registry, distributed workers,
or cloud infrastructure to the minimum slice. The interview story is the
working operational loop, failure behavior, and replay proof; an installed
broker without an end-to-end demo is weaker evidence.

### Event and command contracts

Every stored event should use one versioned envelope:

```text
schema_version
event_id
event_type
machine_id
sequence
occurred_at
ingested_at
source                 # always simulation in this slice
command_id             # nullable only for autonomous telemetry/ticks
correlation_id
causation_id
payload
```

Required invariants:

- `event_id` is globally unique.
- `(machine_id, sequence)` is unique and strictly increasing without duplicate
  application.
- `command_id` is the idempotency boundary for command submission.
- `occurred_at` records simulated/event time; `ingested_at` records store time.
  Neither may be inferred from filesystem metadata.
- All timestamps are timezone-aware UTC values and all schemas carry an
  explicit version.
- Non-finite pose, health, or numeric payload values fail validation.
- Unknown event versions and unknown state transitions fail closed.

Every telemetry payload must include:

```text
machine_id
sequence
timestamp
mode
pose
health
source                 # simulation
```

The initial machine modes are `idle`, `running`, `paused`, `estopped`, and
`faulted`. Transition rules must be explicit and tested. At minimum, pause is
valid only from running, resume only from paused, estop preempts any active
mode, and an estopped actor cannot run or move until a successful reset.
Rejected commands are terminal and must not mutate actor state.

### Persistence and replay contract

- SQLite tables and rows are created programmatically by migrations, the
  command router, state machines, and simulator ticks. Agents never author SQL
  or individual lifecycle/telemetry rows.
- Agents operate through compact MCP/API tools such as `list_machines`,
  `get_machine_state`, `run_task`, `tail_runtime_events`, `explain_command`,
  and `replay_machine`. The adapter owns UUID generation and retry reuse.
- Important runtime boundaries may produce generated Markdown summaries for
  agent and reviewer consumption, but Markdown is a projection rather than the
  5-10 Hz persistence mechanism.
- SQLite is authoritative only for the new simulation runtime. It does not
  supersede signed repository artifacts or `project_state.json`.
- The `events` table is append-only. State is a projection, not a mutable
  substitute for the log.
- A transaction allocates the next per-machine sequence and appends the event
  atomically.
- Replay starts from sequence zero for the MVP. Snapshots may be added only
  after plain replay is correct and measured to need optimization.
- A process restart followed by replay must produce byte-equivalent normalized
  machine state to the pre-restart projection.
- Command and state-transition history is durable. High-rate telemetry is
  session-scoped with an explicit rotation/retention policy so a continuously
  running local demo does not grow without bound.
- Corrupt, duplicated, missing, out-of-order, or unknown-version events fail
  replay closed with a named diagnostic; they are never silently skipped.

### Proposed transport after approval

The transport contract should remain small:

- `POST /runtime/commands` - submit one versioned command with `command_id`.
- `GET /runtime/machines` - current derived state for all simulated actors.
- `GET /runtime/events?after=<cursor>&limit=<n>` - bounded ordered catch-up.
- `GET /runtime/replay/{machine_id}` - read-only replay result and diagnostics.
- `WS /runtime/stream?after=<cursor>` - missed-event catch-up followed by live
  events and latest-state projections.

These routes are proposals only. They must not be added to the current FastAPI
app until ST15A approves the new mutation boundary. Validation errors,
transition rejection, duplicate command IDs, and stale cursors must have
stable typed responses rather than generic 500 errors.

### Studio Operations view

ST15E should extend the world-first Foundry Stage rather than turn runtime
events into another card-and-table dashboard:

- A large interactive 3D stage is the primary surface, with three selectable
  simulated actors visibly moving through their workcells.
- One obvious plus/run control launches a simulation-only episode and keeps
  its `command_id` and lifecycle visible without exposing SQL or raw transport.
- Robot motion, objects, targets, contact, trajectory, success, failure,
  pause, and simulated estop are expressed spatially and through purposeful
  motion before they are expressed as text.
- Camera, orbit, focus, and replay-scrub controls stay attached to the world.
- Mode, health, sequence, freshness, and command lifecycle appear in a compact
  spatial HUD; an event ribbon provides machine/type/correlation filters.
- Raw/structured payloads and replay position live in a secondary inspector
  drawer rather than occupying the main canvas.
- Reconnect state, cursor lag, stale telemetry, and server fault indicators.
- Persistent `SIMULATION ONLY - OPERATIONAL DATA, NOT REPOSITORY EVIDENCE`
  labelling.
- No physical robot controls and no implication that `estop` affects real
  hardware. The demo estop is a simulated state transition only.

The existing Event Ledger continues to inspect briefs, reviews, session logs,
and manager interventions. Cross-links may connect a runtime command to a
later signed artifact by explicit identifier, but neither side may manufacture
or infer the other's authority.

### Required tests

Tests are part of the feature, not follow-up polish:

- **Command idempotency:** identical `command_id` and payload apply once and
  return the original lifecycle; conflicting reuse is rejected.
- **State transitions:** every valid and invalid mode/command pair, including
  estop preemption and reset recovery.
- **Stale telemetry:** duplicate or lower sequences do not regress current
  state and produce a named rejection/diagnostic.
- **Ordering:** concurrent commands preserve unique monotonic per-machine
  sequence numbers.
- **Replay:** full replay equals the live projection before and after restart.
- **Failure replay:** rejected and failed commands remain visible but do not
  apply successful state changes.
- **WebSocket catch-up:** disconnect, produce events, reconnect from cursor,
  receive each missing event exactly once in order, then continue live.
- **Validation:** malformed IDs, timestamps, poses, non-finite values, unknown
  actors, unknown schemas, and oversized payloads fail closed.
- **Proof boundary:** every actor/event is simulation-labelled and no runtime
  path invokes hardware, training, promotion, existing no-authority scripts,
  or governed goal-loop writes.

### ST15F acceptance and demo proof

The umbrella feature is complete only when all of the following agree:

1. Three actors run together for at least 60 seconds at the configured rate
   without sequence collisions or unbounded memory growth.
2. The UI visibly demonstrates start, pause, resume, move, task success, task
   failure, estop rejection behavior, reset, and command-ID deduplication.
3. The database contains every demonstrated command lifecycle and telemetry
   event in ordered form.
4. A WebSocket disconnect/reconnect visibly catches up from its cursor without
   gaps or duplicates.
5. The runtime is stopped and restarted; replay reconstructs the same
   normalized state and the test asserts equality.
6. The existing `/api/events` signed-artifact ledger and the two existing
   no-authority actions remain behaviorally unchanged.
7. Focused runtime tests, full Studio server tests, `bun run build`, browser
   inspection with real runtime data, and an adversarial same-agent review are
   green.
8. `TASKS.md` states, schema documentation, demo commands, limits, and failure
   semantics match the implementation.
9. Each verified phase is committed in a small scoped commit, pushed only to
   `studio/app-shell`, and confirmed present on the remote branch.

### Explicit non-goals for the first slice

- Kafka, Redpanda, RabbitMQ, or another external broker.
- Physical robot, camera, serial, servo-bus, or leader/follower access.
- Real emergency-stop or safety certification claims.
- Optimizer training, dataset mutation, checkpoint promotion, or authority
  composition.
- Replacing the repository/signed-artifact source of truth.
- Authentication, multi-tenant deployment, high availability, or cloud
  infrastructure.
- Native Mac packaging work; the target surface is the localhost web app.

## ST16 - Foundry Stage Visual Shell Reframe

ST16 repairs the experiential gap without waiting for or implying authority to
implement ST15. It consumes only existing read-only APIs and the two existing
no-authority visualization surfaces.

### Visual thesis

The foundry is the interface. Opening Studio should first show the robot world,
its current replay/evidence state, and an obvious way to explore an episode.
Documents, hashes, forms, and tables remain available as workbenches, but they
must not be the dominant first impression.

### Required experience

- Rename the home navigation concept from Dashboard to Foundry while keeping
  the stable `/` route.
- Make a compiled workcell the largest element above the fold with orbit,
  zoom, focus/reset, scene selection, and clear simulation-fixture labelling.
- Provide a prominent plus control that launches a **recorded replay** in the
  stage. It must never imply that it starts training, hardware, or a new goal
  loop episode.
- Project available mirror video into the same stage with play/pause, replay
  selection, native scrub, outcome, seed, frames, and provenance link.
- Show current slice, simulation-only state, API freshness, workcell health,
  and authority closure as a compact spatial HUD rather than a grid of cards.
- Convert recent briefs, reviews, sessions, and manager interventions into a
  compact activity ribbon/timeline with visual channel and recency cues.
- Keep next step, blockers, run window, and verified boundary accessible in a
  quiet mission drawer/rail.
- Use purposeful scene and lifecycle motion, keyboard-visible focus, useful
  hover states, and `prefers-reduced-motion` fallbacks.
- Work at desktop and narrow laptop widths; no essential control may be hidden
  behind hover alone.

### Acceptance

1. The first viewport communicates “robot-learning foundry” without requiring
   the operator to read raw JSON, a document table, or a hash.
2. From `/`, one obvious action shows a real recorded episode replay and its
   outcome; returning to the 3D scene is equally obvious.
3. The 3D scene is visible and interactive without expanding an accordion or
   scrolling below an intake form.
4. Scene selection, orbit/reset, replay selection, play/pause, scrub, camera or
   mirror projection, and evidence ribbon navigation are browser-verified.
5. The shell labels recorded replay, simulation fixture, and signed evidence
   honestly and adds no new mutating endpoint.
6. Existing pages and routes remain reachable; `bun run build`, lint, server
   tests, live API checks, console inspection, and responsive screenshots are
   green before ST16 is marked done.
