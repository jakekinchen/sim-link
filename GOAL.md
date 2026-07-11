# GOAL

## Active Mission

Complete the SceneSmith PI0.5 autonomous sorting program through a bounded,
Git-tracked goal loop. Before any further training, qualify the simulation
structure and build an Experience Compiler that turns immutable raw rollouts
into semantically valid segments, action windows, mixture plans, and provenance-
bound training views. Continue through cheap policy falsification, curriculum,
reward-aware cloning, and competence-gated residual learning only after those
prerequisites pass. Update the active ledger at every verified slice and continue
until the acceptance criteria are met or a genuine human-authority blocker is recorded.

The physical SO-101 follower must never be opened before verified T16.5a or
commanded outside the exact verified T16.6 session permit. The final owner
confirmation covers only the initial no-op-equivalent then one-small-joint-
delta-and-return permit under an active owner-presence lease. Neural-policy,
contact-stabilized, controller-assisted, supervised-motion, and physical-robot
proof states must remain distinct.

## Active Run Window

- Actual start: `2026-07-11T02:14:07-05:00`.
- No new major slice after: `2026-07-11T11:44:07-05:00`.
- Hard closeout: `2026-07-11T12:14:07-05:00`.
- Closeout recorded: `2026-07-11T11:44:39-05:00`, after the no-new-major-
  slice cutoff and before the hard deadline.
- New owner-triggered continuation: `2026-07-11T12:52:56-05:00`, beginning
  from remotely preserved HEAD `32c2948`; no deadline was specified.

## Current Milestone

M16 - Hardware Twin Foundation And Qualification Contract

## Current Slice

T16.5b is `verified`, and T16.5c is `in_progress`. The following paragraphs
retain the T16.5b disconnect, rejected-attempt, correction, and acceptance
history that constrains later hardware work. Brief 043 implementation
`7ea26651e921eee55dad6fcbb26cb58c45c7b290` is remotely preserved. The tracked
disconnect proof identity is
`627de4fd5715e281007ab5f19a37b0cb610b4d3b637b7b37933a41396ba3859b`;
it binds the ignored private evidence, exact POST method/path/body, HTTP 200
response, before/after hardware and invariant snapshots, one observed call,
the consumed permit, zero additional calls, zero forbidden effects, and no
physical motion or follower command. Its provenance is explicitly labeled
reconstructed from executor operation output rather than a contemporaneous raw
HTTP transcript.

The signed serial identity now requires both canonical and paired TTY paths.
The latest all-alias holder snapshot at `2026-07-11T10:07:17-05:00` checked two
paths, observed counts `[0, 0]`, deduplicated to zero, and has identity
`b33a7cc062bc73c666031f6f5b36d5f0e142bea7f541d77a0754fe04ae1d689c`.
Future live evidence must bind full pre-open and post-close signed snapshots;
an alias holder or path-existence change fails closed.

`Torque_Enable` is now a source-bound one-byte read for all six servos. The
offline fixture requires six zero values, 54 successful reads plus one bounded
retry, zero configuration/torque/register writes, and
`physical_follower_commanded=false`. A live result must independently replay
the exact read trace and match all decoded values; no live six-servo torque
claim exists yet.

Brief 043 passed 50 focused and 229 broad tests,
both offline runtime verifiers, deterministic fixture and disconnect-proof
verification, compilation, privacy checks, and diff checks. No serial or camera
was opened, and no Studio request, reconnect, process signal, write, torque
change, motion, policy actuation, or training occurred. Reviewer 060 accepted
the offline boundary, and reviewer 061 opened one remotely preserved finite
session. Attempt 003 completed 54 allowlisted reads with zero retries/writes/
torque changes/motion, closed without torque change, and proved both aliases
holder-free before and after. The first named-camera subprocess then returned
251; the retained diagnostic shows AVFoundation selected unsupported 29.970030
fps while advertising 30.000030 fps. Release and process cleanup passed, no
success manifest was written, and the gate reclosed at
`2026-07-11T10:07:17-05:00`.

Live attempts 001-003 remain rejected and grant no proof label. Attempt 003
retained private failure identity `e7f8eb21...` and diagnostic `482064ad...`,
but failure schema v2 stores only the servo-result identity/counts rather than
the complete decoded result. Brief 044 implementation `4ae0521c` is now remotely
preserved: the v2 execution contract requires integer 30 fps, the ffmpeg command
places exactly one `-framerate 30` before its input, audits and tracked/private
v3 success evidence bind the mode, and v3 private failures embed and replay the
complete signed contract and servo result. Legacy attempt-003 v1/v2 evidence
remains verifiable. Reviewer 064 authorizes exactly one fresh finite v2-contract
session after its gate-transition commit is confirmed on origin. Attempt 004
used that session and is rejected. Its v3 private artifact verifies the full v2
contract, 54 successful reads, all six `Torque_Enable=0` values, zero writes,
zero torque changes, zero motion, one no-torque close, and zero holders across
both signed aliases before and after. The first exact-name camera returned zero
but emitted 339 stderr bytes because AVFoundation defaulted to unsupported
`yuv420p`; it advertised `uyvy422`, `yuyv422`, `nv12`, `0rgb`, and `bgr0`.
Release and process cleanup passed, no success manifest or proof label was
written, and the live gate reclosed at `2026-07-11T10:37:42-05:00`. Brief 045
implementation `820a40f` is remotely preserved. Discovery v2 binds normalized
pixel format, dimensions, and rate ranges from AVFoundation device metadata
without a capture session or frame stream. Contract v3 selects the smallest
reviewed per-camera mode that supports integer 30 fps within 0.01 fps and places
exact `-pixel_format`, `-video_size`, and `-framerate` options before input.
Diagnostics v3, private success/failure v4, and tracked manifest v4 bind the
same mode; legacy attempt-003/004 failures still verify. The live gate remains
closed until reviewer 067's scoped transition is remotely confirmed, then
exactly one fresh discovery-v2/contract-v3 session is permitted from
`2026-07-11T11:04:00-05:00` through `2026-07-11T11:34:00-05:00`. It must reclose
on every outcome. Attempt 005 consumed that session and is rejected in post-run
adversarial review: camera 0 matched its signed 160x90 mode, but camera 1's
424x240 contract silently produced two 640x480 PNGs and the current verifier
incorrectly accepted them. The candidate manifest `0d7b4400...` was removed;
private candidate `ebb4934c...` is retained only as rejected diagnostic evidence,
and no proof label is granted. The gate reclosed at
`2026-07-11T11:05:47-05:00`. Brief 046 is active offline to enforce captured
frame dimensions against the signed per-camera mode. Implementation `6eb5f89`
is remotely preserved and the corrected capture/private/manifest verifiers
reject the actual attempt-005 candidate. Both cameras' signed discovery sets
contain 640x480 modes at 30.000030 fps. Brief 047 is active offline to require
at least 640x480 and choose the smallest qualifying signed mode, avoiding the
already disproven sub-640 RealSense selection. Implementation `e68068a` is
remotely preserved: actual discovery now resolves C922 YUYV 640x480 and
RealSense UYVY 640x480 at integer 30 fps, and sub-floor-only cameras reject.
The live gate remains closed pending a separate review commit. Sequential
capture is not synchronized or policy-input-valid. Studio reconnect remains
deferred unless exact device, calibration, and current-pose evidence proves it
mechanically no-motion-safe.

Reviewer 071 permits exactly one final finite read-only session only after its
transition commit is confirmed on origin. The window is
`2026-07-11T11:23:00-05:00` through `2026-07-11T11:38:00-05:00`, the session
limit is one, both selected modes must be signed 640x480 or larger, decoded
dimensions must match exactly, and the gate must reclose on every outcome.

Attempt 006 consumed that session and is accepted. Fresh discovery tolerated
numeric index churn while preserving exact identities; contract `cf1ad99c...`
selected RealSense UYVY 640x480 and C922 YUYV 640x480. Manifest
`eff3c824...` independently verifies four matching PNGs, 54 allowlisted reads,
all six `Torque_Enable=0`, zero writes/torque changes/motion, no-torque close,
zero holders across both aliases, and complete cleanup. The gate reclosed at
`2026-07-11T11:24:24-05:00`. T16.5b grants only
`live_read_only_census_observed` and `physical_observation_capture`. Its
sequential host-timestamp evidence is not synchronized or policy-shadow-input-
valid. T16.5c remains a separate no-actuation prerequisite; no motion or
physical qualification is granted.

T16.5c remains `in_progress`. Brief 048 implementation `700be05` is remotely
preserved and independently verifies signed CalibrationProfile `b360b4f6...`.
The profile binds pinned calibration `192404b6...`, accepted manifest
`eff3c824...`, and the six exact live servo identities; it validates signed
STS3215 homing-offset bounds, raw position ranges, drive mode zero, body-degree
normalization, and gripper range-min=0/closed to range-max=100/open semantics.
Six focused tests, the offline artifact verifier, compilation, and the
238-test authority/twin regression gate passed. No hardware was accessed and
no policy was run. Static-pose bracketing, policy-input validity,
preprocessing/shadow/replay, actuation, and physical qualification remain
unverified; the live gate and training lock stay closed.

Brief 049 implementation `4fd1f3a` is remotely preserved. Signed contract
`90e7baea...` binds the accepted camera modes and CalibrationProfile, exact
`q_before -> finite camera batch -> q_after` time enclosure, 0.5-degree body
and 0.5-percent gripper drift limits, stable all-alias zero-holder requirements,
and a teardown that cannot write, change torque, or command motion. Fixture
observation `84d0aa12...` and result `6ebb9bd6...` verify only
`fixture_static_pose_bracket_conformant`. Eleven focused tests pass in both
robotics runtimes and the 249-test offline authority/twin gate passes. No
hardware or policy ran; no physical, policy-input-valid, shadow, motion, or
qualification label is granted.

## Durable State

- Goal-loop mandate: `docs/autonomous-workflow/pi05-autonomous-sorting-goal-loop.md`
- Active overnight loop: `docs/autonomous-workflow/overnight-authority-twin-goal-loop.md`
- Active execution ledger: `docs/autonomous-workflow/experience-compiler-twin-task-ledger.md`
- Authoritative machine-readable state: `docs/autonomous-workflow/project_state.json`
- Rebased loop prompt: `docs/autonomous-workflow/experience-compiler-twin-goal-loop.md`
- Incremental task ledger: `docs/autonomous-workflow/pi05-autonomous-sorting-task-ledger.md`
- Invariant milestones: `docs/autonomous-workflow/09-autonomous-milestones.md`
- Active slice brief: latest numbered file in `docs/briefs/`
- Execution evidence: `docs/session-logs/`
- Review decisions: `docs/reviewer-messages/`
- Accepted checkpoint pointer: `experiments/pi05_autolearn/accepted.json`

## Execution Mandate

1. Read root `AGENTS.md`, the active overnight loop, canonical state, ledger,
   current brief, latest reviewer decision, and Git state.
2. Select the smallest useful unchecked task in the active milestone.
3. Add deterministic tests first where practical.
4. Implement only that slice and run its verification gate.
5. Update the task ledger with status, evidence, commit, and next action.
6. Write an executor log and reviewer decision.
7. Commit only explicitly staged robotics/workflow files at the slice boundary.
8. Push only to `origin/codex/pi05-autolearn-loop` and confirm the remote commit.
9. Continue immediately to the next dependency-ready task unless a stop
   condition applies.

No optimizer run is authorized while the active ledger says `training_lock: closed`.

## Stop Conditions

- Stop before any live hardware path until T16.5a is verified and remotely
  preserved.
- Stop before any write, torque change, or motion unless it is the exact
  owner-authorized one-call follower disconnect recorded above, or T16.5a-
  T16.5c and the exact signed/content-addressed T16.6 session permit, owner-
  presence lease, watchdog, stop, and shutdown gates all validate.
- Under the initial confirmed permit, stop before any second joint, gripper,
  reach, contact, task primitive, policy-proposed actuation, or other material
  expansion.
- Stop before destructive dataset replacement without an explicit overwrite flag.
- Stop training if coordinate transforms, normalization, preprocessing, task
  labels, temporal continuity, source weighting, or dataset identity are not
  versioned and validated.
- Stop training if the structural twin pin, compiled window index, or reproducible
  mixture manifest is missing, stale, or fails its qualification gate.
- Never promote from training seeds, incomplete evaluation, assisted completion,
  or an uncommitted learning-loop implementation.
- Never call contact-stabilized or controller-assisted success `strict pure`.
- Stop/delete paid Brev resources after a bounded training stage finishes or
  fails and record the final inventory.
- Escalate only for missing authority, external spend/credentials, destructive
  action, physical-hardware risk, or a blocker proven across three attempts.

## Current Proof State

- PI0.5 inference, five-step LoRA training, save, finalize, reload, evaluation,
  and rollback are proven on an MPS-backed runtime.
- Hybrid controller-assisted sorting is proven; strict autonomous sorting is not.
- M10 now rejects the malformed bootstrap aggregate and proves a corrected
  12-episode canary merge with exact frame tasks and pinned normalization.
- `cycle-001-mps` is interrupted and must not resume under its current recipe.
- The corrected 250-step rung is retained as historical evidence of a narrow
  reach improvement; rungs 500/1,000 are suspended behind M16-M19.
- The current T16.3 artifact proves deterministic source/hash plumbing,
  TwinProfile binding, effective solver defaults, full comparison-time
  quaternion semantics, explicit inertial unknown evidence, and effective
  friction/contact attachment truthfulness.
- Independent reviewer reruns now confirm the v2 unnamed-geom identity
  strategy closes the quaternion-spelling and sibling-order gaps, with tracked
  structural artifact identity
  `fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9`.
- Reviewer decision 039 reopens T16.1, T16.2, and T16.4 at their production
  authority boundaries. T16.1 retains a verified dependency inventory but not
  a unified executable stack; T16.2 retains a verified schema scaffold but not
  mechanically computed qualification decisions; T16.4 retains a verified
  synthetic compiler scaffold and truthful blocked real template but not a
  production measured-input path or downstream authority. T16.5 is pending.
- Reviewer decision 040 verifies T16.1b at commit `dca2b45`: collection,
  training, finalization, inference, and LeLab now share one pinned base plus
  tracked patch-set identity. This grants executable-stack reproducibility only;
  the training lock remains closed.
- Commit `69df54d` and reviewer decision 041 establish the strict finite artifact,
  content-addressed evidence, physical inertia, graph-link, and scoped-gate
  layer. T16.4b remains partial at `3cd142e`.
- Reviewer decision 042 keeps T16.4b open but makes T16.2b-A the active first
  slice. Component artifacts may report local capabilities only; the central
  composer owns global readiness. No optimizer, hardware, transfer, or
  promotion authority is granted.
- Reviewer decision 043 verifies T16.2b-A at `c0b9629`: the central composer is
  the only global-decision path, assembly-inertials v2 carries local capability
  facts only, and the checked-in fixture composition mechanically withholds all
  global decisions. The remote preserves the implementation and review through
  `e1d59ca`; `training_lock` remains closed.
- Reviewer decision 045 verifies Brief 036 implementation `7d05629`:
  deterministic normalized Jacobi convergence, eigenpair residuals,
  scale-relative physical-inertia tolerances, and the adversarial NumPy corpus
  pass. The implementation and review are preserved on the named remote through
  `dbdd1ef`; T16.4b is closed on declared fixture evidence only.
- Reviewer decision 046 verifies Brief 037 implementation `710960b`:
  caller-declared execution is closed, v2 qualification results are generated
  and independently recomputed, freshness is bounded by source evidence, and
  fixture numeric passes remain authority-withheld. Implementation and review
  are preserved on the named remote through `383557b`; T16.2b is closed on
  declared fixture evidence only.
- Reviewer decision 047 verifies Brief 038 implementation `f200087`:
  the injected census surface is read-only, lifecycle and retries are bounded,
  partial-connect cleanup closes without torque writes, exact follower and six-
  servo identity are checked, and the signed fixture remains
  `census_trace_conformant` with no hardware opened or follower commanded.
  Implementation and review are preserved on the named remote through
  `d002c80`; T16.5a is closed on declared fixture evidence only.
- Reviewer decision 048 supersedes that closeout after a pre-live source audit
  found protocol `1` in the fixture versus protocol `0` in the pinned STS3215
  runtime. T16.5a is reopened, `census_trace_conformant` is withdrawn, and
  T16.5b remains closed until Brief 040 is reviewed and remotely preserved.
- Reviewer decision 049 accepts the Brief 040 correction locally: the v2
  contract uses protocol 0 and independently verifies exact runtime source
  hashes and semantics, including no-write open/close guards. T16.5a remains
  correction and review are preserved on the named remote through `2407299`;
  T16.5a is reclosed as corrected `census_trace_conformant` fixture evidence.
- The owner is physically present and has granted conditional read-only
  hardware/camera authority after verified T16.5a plus final operator
  confirmation for exactly one initial session-scoped `supervised_micro_motion`
  permit after T16.5a-T16.5c. No second prompt is required; every permit and
  lease check remains mandatory, and any expansion remains unauthorized.
- Reviewer decision 052 rejects T16.5b live attempt 001: the no-write serial and
  finite-camera path reached post-close discovery, but AVFoundation swapped the
  two index-to-name mappings and a pre-existing July 8 Studio server still held
  the follower serial device. No evidence bundle, tracked manifest, live proof
  label, write, torque change, or motion claim survived. Brief 041 keeps all
  further live access closed while the camera path is corrected offline.
- Reviewer decision 053 accepts the Brief 041 offline correction at commits
  `ea99ec9`/`66003d8`/`fd13bf6`/`01802a0`: exact-name ffmpeg capture replaces
  OpenCV indexes, PNG framing and pixel streams are finite and validated,
  subprocess/evidence counts are content-bound, and zero-holder checks run
  immediately before and after the serial census. The live gate remains closed
  because exclusive ownership has not been re-established after the
  pre-existing Studio server was observed holding the follower device.
- Reviewer decision 055 resumes T16.5b after the owner explicitly authorized
  virtual disconnect/reconnect. The accepted immediate action is one exact
  follower disconnect call plus response/status/zero-holder proof; reconnect is
  deferred unless it can be proven no-motion-safe. No live proof label, motion,
  general register-write authority, or physical qualification is granted by
  the resumption itself.
- Reviewer decision 056 verifies the one-call disconnect boundary: HTTP 200,
  follower disconnected, follower torque off, leader retained, unchanged
  safety/routing, zero jobs, and zero follower holders. The live gate remains
  closed pending remote preservation and a separate reopen decision.
- Reviewer decision 057 opens the T16.5b live gate after remote confirmation of
  `b211562` and a second zero-holder/torque-off check. The grant is one fresh
  session under the existing finite lease/contract and no-write guards; it does
  not itself grant a live proof label or any write/motion authority.
- Reviewer decision 058 rejects live attempt 002 and recloses the gate. The
  exact follower census closed with zero holders before exact-name camera
  capture returned a nonzero ffmpeg status. No evidence bundle, manifest,
  label, write beyond the earlier authorized disconnect, motion, or physical
  qualification survived the attempt.
- Reviewer decision 059 accepts Brief 042 implementation `2d1cd97` on offline
  evidence only. Manager intervention 015 applies the owner review: canonical
  disconnect proof, consumed-permit state, all-alias holder coverage, and
  `Torque_Enable` evidence are mandatory before another live-gate review.
