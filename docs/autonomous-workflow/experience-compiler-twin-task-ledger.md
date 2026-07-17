# Experience Compiler And Hardware Twin Task Ledger

Updated: 2026-07-17

```text
training_lock: closed; T20.43c-R2 completed its sole authorized attempt as a verified terminal negative and no retry is authorized
run_window: closed after 10,000 finite optimizer updates, seven checkpoints, and 14 rollouts; hardware, network, external compute, and Brev remained closed
run_state: Reviewer 318 verifies exact zero-update equivalence and a clean completed campaign; chunk-50 learned grasp-lift-hold-lower but never clean release, so Gate C is false and the result is not an infrastructure failure
current_milestone: M20 simulation-only clean supervision
current_task: F0 verified under Brief 230 and Reviewer 320; F0a is the next eligible model-free audit
support_task: K2 verified under Brief 226 and Reviewer 319; W3 remains an unintegrated 0-of-3 handoff and W5 remains unintegrated transport/replay evidence
completed: T16.0 guard; T16.1 dependency inventory; T16.1b unified executable stack; T16.2/T16.2b mechanically computed qualification; T16.2b-A central authority composition; T16.3 structural baseline; T16.4/T16.4b production measured-inertial compiler and numerical hardening; corrected T16.5a offline no-write census preflight; T20.1 source-bound simulation training specification and central authority
evidence: processor 59827b3d...; fixture normalization bundle dea3ff8c... binds 94,568-sample MEAN_STD statistics, actual cached processor/tokenizer parity, camera order, revisions, and tensor hashes while remaining production-ineligible; T17.4 emitted 2 source-bound frames, 0 eligible frames, 0 segments, and 2 quarantines; T17.5 emitted 0 unpadded windows across 5/10/15/50 horizons; T17.5b emitted 8/8 strict scripted episodes, 1,952 eligible frames, 88 hard-boundary segments, 0 quarantines, and 3,744 unpadded windows including 120 horizon-50 windows; T17.6 inventory bound 3 legacy canary descriptors, accepted 0, and emitted a source-bound empty view because no source met the current raw-record contract; T17.7 verified 100 raw-to-compiler-to-window replay selections (25 per horizon) with all eight rollouts covered and no model call; T18.1 selected 192 unique valid windows across 24 complete source/task-phase/control-mode/horizon buckets, one per each of 8 episodes; T18.2 froze 192 exact IDs as immutable logical cycle 0001; T18.3 compiled 1,345 actor-safe exact-state records; T18.4 froze 192 snapshots with zero source corrections; T20.1 binds 488 training and 244 held-out simulation frames plus tensor hash eca512ab...; T20.2 ACT run 003 used 100 finite MPS updates and recorded train L1 1.0217 -> 0.1682, held-out L1 0.2213; policy-owned rollout made zero strict contacts and 0.2023 mm lift; T20.3 PI0.5 run 002 used 20 finite local-MPS LoRA updates with train loss 100.8441 -> 100.0873 and held-out loss 130.0066 -> 128.4057 but zero strict contacts; T20.4's 250-update rung reduced held-out loss to 31.4226 but retained zero strict contacts; T20.5 horizons 5/10/15 produced distinct action hashes but identical zero-contact outcomes; T20.6 binds all eight capability stages and eight semantic adversarial traces; T20.7 gave every model the same 20 samples and fixed seed-2 rollout, yielding no strict contact or winner; T20.9 exact source replay exposed only a release semantic mismatch; T20.10 corrected that mismatch without rewriting history; T20.11 localized all model divergence to frame zero; T20.12 proves 3.606e-9 rad conversion round-trip and equal six-way loss weights but finds shoulder lift, wrist flex, wrist roll, and gripper outside checkpoint-normalizer min/max, including open gripper 92.4302% versus 81.0264% max; T20.16 proves the gripper-only hybrid matches frame zero but fails closed loop with zero conversion clipping, zero projected frames, zero strict contacts, and a -24.9997 mm lift margin
remaining: learned strict-v2 policy success, real Robo Scan metric bundle and sim-link I5 compile, and a separately authorized physical canary; T19.2 physical calibration remains under fresh permits
owner_authority: owner-direction-2026-07-17-final-overnight.md opens model-free F0 release-gap diagnosis and permits at most one separately reviewed corrective ACT rung; it separately bounds optional F1 Brev work but grants no automatic training, hardware, transfer, promotion, or tag
blockers: learned strict-v2 task completion and Gate C remain scientifically unmet; corrective training, F1/Brev, hardware, transfer, promotion, and the freeze tag remain closed at the F0 boundary
next_step: open a fresh model-free F0a brief to test chunk timing, phase observability, and observation aliasing before any corrective ACT proposal
```

## 2026-07-17 - Reviewer 318 closes T20.43c-R2 as a terminal negative

Replacement marker `dfe3ff05...` is consumed. Equivalence receipt
`fdc06297...` proves exact equality across 234 float32 tensors and 51,617,414
elements, empty AdamW state, an unadvanced sampler, and zero maximum absolute
error before update 1. The unchanged ACT recipe completed 10,000 finite updates,
seven checkpoints, and 14 frozen strict-v2 rollouts. Final receipt
`be11a258...` verifies the compact result set and records no infrastructure or
terminal failure artifact.

No rollout passed Gate C. Chunk-50 at updates 2500, 5000, 7500, and 10000 did
learn strict grasp, unassisted lift, unsupported hold, support-free stable hold,
and lower. The final checkpoint lifted 37.655 mm and failed only
`release_final_contact_clear`; update 7500 lifted 40.025 mm with the same sole
failure, and update 5000 retained 183 strict-v2 frames while failing release and
retreat clearance. The campaign maximum was 45.674 mm. Final receding-10
execution had no grasp hold and only 0.502 mm lift. Reviewer 318 therefore
classifies ACT-on-R0 as a verified terminal negative with a concrete
release-phase counterexample. Training closes; no retry, Gate C, hardware,
network, external compute, Brev, transfer, or promotion authority follows.

## 2026-07-16 - Reviewer 317 restores a drifted pre-marker scoped input

The final pre-marker gate caught that Brief 229 belongs to
`IMPLEMENTATION_SCOPED_PATHS`, but authority and acceptance commits had appended
status prose after required source `1bc1c773...`. The runner would have failed
closed before marker creation. Brief 229 is restored byte-for-byte to the
reviewed source; all other scoped inputs were already unchanged. Authority
`391811e...`, acceptance `a61b23eb...`, and Reviewer 316 bytes remain unchanged.
No marker, checkpoint read, model, optimizer, rollout, Gate C action, hardware,
network, external compute, or Brev action occurred. Reviewer 317 requires the
correction on origin and a fresh full pre-marker check before execution.

## 2026-07-16 - Reviewer 316 accepts T20.43c-R2 pre-run authority

Authority commit `391811e...` is exact on origin. Reviewer 316 independently
reconstructs all six artifacts, confirms the signed actual R2 trace-schema
smoke, re-verifies the immutable update-728 interruption, observes more than
27,800 seconds remaining against the 14,400-second minimum, and passes 19
focused tests. Acceptance `a61b23eb...` (file SHA `4f89c16f...`) binds permit
`f063e034...`, Reviewer file SHA `ad8d00b1...`, and zero pre-marker model
action. No marker, checkpoint read, model, optimizer, rollout, Gate C action,
hardware, network, external compute, or Brev action occurred. Once this
boundary is exact on origin, the sole replacement may run once; no retry.

## 2026-07-16 - T20.43c-R2 model-free authority materialized

Origin source `1bc1c773...` produced owner `d95ddd8a...`, central request
`1f528d2e...`, decision `bf7908b5...`, runtime `79689c7f...`, and permit
`f063e034...`. The central decision grants only
`simulation_training_ready`; physical transfer and promotion remain withheld,
and runtime fields keep hardware, network, external compute, and Brev false.
The 23:07-07:00 CDT window has at least the required four-hour completion
budget. All acceptance, marker, checkpoint/model, optimizer, rollout, result,
and failure paths were absent and unaliased at materialization. Training stays
closed pending origin preservation and a separate pre-run review.

## 2026-07-16 - Reviewer 315 accepts T20.43c-R2 implementation

Brief 229 implements one separately rooted manual replacement because optimizer
state at update 728 was not retained and exact resume is impossible. The first
marker, equivalence, terminal receipt, and partial tree remain immutable. Seven
focused tests and 67 selected tests plus 15 subtests pass; a model-free central
preview grants only `simulation_training_ready`. The four-hour completion
budget precedes the new marker, and any marked failure authorizes no retry.
Training remains locked. Only model-free authority materialization may follow
after Reviewer 315 and commits `75647da9...` through `d0e2b2b9...` are exact on
origin.

## 2026-07-16 - Reviewer 314 closes T20.43c interruption

Marker `e086c293...` is consumed. Equivalence receipt `85087b2a...` proves
bit-exact fresh-ACT/checkpoint tensors, zero AdamW state, an unadvanced sampler,
and actual-schema mirror success before update 1. The fixed recipe reached
optimizer update 728 and retained checkpoint-500 dual-cadence evidence before
a sibling thread sent SIGINT under a superseded scheduling instruction.
Terminal artifact `d848a1a8...` and partial-tree identity `e0aea95f...` verify
with exit 0. Reviewer 314 classifies the result as an inconclusive
owner-directive interruption—not a trained negative, infrastructure failure,
Gate C pass, or retry grant. ACT-on-R0 remains unresolved and training closes.

## 2026-07-16 - Reviewer 310 accepts T20.43c pre-run authority

Origin authority commit `02496f0...` reconstructs exactly and grants only
`simulation_training_ready`. Acceptance `010d0a43...` binds permit
`166a6cd0...`, Reviewer 310, and the authority commit. Training opens only for
the single local-simulation continuation; the marker remains absent, and update
1 remains barred until fresh seeded ACT/checkpoint tensor equality, empty
AdamW state, and zero consumed batches are signed. Retry, replacement,
hardware, network, external compute, and Brev remain closed.

## 2026-07-16 - T20.43c model-free authority materialized

The resumed smoke receipt `9e8783dc...` binds unchanged MP4 SHA `955ad918...`
and records its post-render recovery. Owner `315aef82...`, central request
`bf53bcc0...`, decision `c316bf01...`, runtime `8d4fbf89...`, and permit
`166a6cd0...` reconstruct exactly. The composer grants only
`simulation_training_ready`; all output paths were absent and unaliased, MPS
and dependency pins passed, and no tensor/model/optimizer action occurred.
Training remains locked until the authority commit is exact on origin and a
separate signed acceptance is preserved.

## 2026-07-16 - Reviewer 309 accepts model-free materialization recovery

The actual-schema smoke completed with MP4 SHA `955ad918...` and manifest
identity `00494310...`; dependency inventory then imported an obsolete
Python-3.11 MuJoCo path under Python 3.12. No authority artifact, permit,
marker, tensor read, model, or optimizer exists. The correction re-verifies and
reuses those exact smoke bytes, records the resume in the signed receipt,
inserts the bound Python-3.12 support path, and retains partial-tree alias
hardening. The selected recovery regression set passes 58 tests and 15
subtests. Training remains locked.

## 2026-07-16 - Reviewer 308 hardens T20.43c terminal preservation

The model-free continuation package now hashes an absent, empty, or partially
populated T20.43c run root without weakening symlink rejection. This closes the
post-marker edge where an infrastructure failure during initial directory
creation could otherwise consume the marker before a signed terminal receipt
was written. Seven focused tests and 70 selected T20.43/T20.43b/T20.43c/T20.44,
authority-composer, and pointer regressions pass. No authority artifacts,
checkpoint tensor reads, model construction, optimizer, rollout, hardware,
network, external compute, or Brev action occurred.

## 2026-07-16 - Reviewer 307 accepts T20.43c implementation

T20.43c now has a separately rooted, fail-closed zero-update continuation
implementation. It preserves the entire signed T20.43b failure tree, pins the
actual trace-schema renderer smoke, requires the central composer to grant only
`simulation_training_ready`, and gates update 1 on bit-exact checkpoint/fresh
ACT equality plus empty optimizer and unadvanced sampler state. Six focused and
57 selected regressions with 15 subtests pass. Reviewer 307 authorizes only the
next model-free authority materialization; training remains locked.

## 2026-07-16 - Brief 227 opens T20.43c ACT resolution

The owner explicitly authorizes further actions to resolve the still-unanswered
ACT-on-R0 question. Brief 227 opens implementation and model-free tests for one
separately reviewed recovery boundary. The preferred route continues the
original marker only if checkpoint-0 bytes equal fresh seed-20260801 ACT,
optimizer state is empty, the episode sampler is unadvanced, and the actual
T20.43b trace renders through the immutable-safe v2 entrypoint. Original marker,
failure, checkpoint, and trace bytes may not change. Model action, authority
materialization, hardware, network, external compute, and Brev remain closed
until implementation and a later pre-run boundary are exact on origin.

## 2026-07-16 - T20.43b sole epoch-2 attempt terminal runtime failure

Marker `d67cf38e...` consumed the one accepted epoch-2 attempt. Fresh ACT and
AdamW construction, checkpoint 0, and one untrained chunk-50 rollout completed,
but the required mirror renderer rejected
`scenesmith.t20_43b_r1_act_closed_loop_trace.v1` before the first optimizer
update. Terminal receipt `89b6dbff...` binds zero updates, one checkpoint, one
rollout, no Gate C pass, no retry, and the exact partial tree. The renderer
dispatches original T20.43 and T20.44 schemas; the pre-run smoke replayed an
original-T20.43 trace and therefore missed this new-schema integration gap.
Reviewer 306 accepts the deterministic terminal-verifier repair after 6
focused and 35 T20.43/T20.43b/T20.44 tests plus live verifier exit 0. This is a
verified infrastructure failure, not a trained-ACT negative: ACT-on-R0 remains
unresolved, and no further attempt or T20.45 activation is authorized.
Closeout commit `4d8f951` is exact on origin.

## 2026-07-16 - T20.43b epoch-2 refresh implementation accepted

Brief 225 and Reviewer 304 accept a separately named administrative epoch-2
wrapper around the still-unconsumed ACT replacement. It re-hashes immutable
epoch 1, fixes replacement/attempt ordinal 1, retains the original marker and
output paths, and rejects windows longer than eight hours, marker/output
presence, base drift, authority escalation, or retry encoding. Commit
`10df153...` is exact on origin after 4 refresh, 34 T20.43/T20.43b/T20.44, and
42 artifact/composer/pointer/receipt tests. No model, optimizer, rollout,
hardware, network, external compute, or Brev action occurred. Only model-free
epoch-2 materialization opens next.

## 2026-07-16 - K1 portable reconstruction kit verified

Brief 224 and Reviewer 303 accept the non-authorizing `reconstruction-kit/`.
Portable source commit `605e4d3...` is exact on origin. Manifest
`5067d1c2...` selects 321 tracked implementation/evidence files (8,614,788
bytes) and records five explicit hashed omissions (22,811,274 bytes), including
live repository state. A fresh 336-file export verifies as receipt
`729addbb...` before and after 31 dependency-light clean-room tests. Six kit
tests, 153 focused source regressions, strict JSON, compilation, link checks,
and manifest rebuild/verification pass. The T20.42 original route decision is
now read from an exact `e9d0507` snapshot, preventing a later addendum at the
living path from invalidating signed R0 history. No model, optimizer, rollout,
marker, hardware, network, external compute, Brev, or authority transfer
occurred. T20.43b remains the next policy task and is still unconsumed.

## 2026-07-16 - T20.43b window closed before marker

Acceptance commit `5f2abf3` is exact on origin, but only 6,353 seconds remained
to hard close at the final start decision. The closest completed standardized
campaign consumed 7,506 seconds for 5,000 updates and 10 rollouts; this is not
an ACT speed estimate, but it leaves no evidence that the 10,000-update,
14-rollout T20.43b campaign can finish safely. Reviewer 302 stops before the
one-use marker. No model/optimizer/rollout path exists, the replacement remains
unconsumed, and T20.43b is not a negative. A future owner window must refresh
only the expired administrative authority epoch after proving marker absence.

## 2026-07-16 - T20.43b pre-run authority accepted

Authority commit `5f8a31e` preserves fresh stable renderer smoke `35224058...`,
Gate A `ea65f3d1...`, owner grant `09111fcb...`, request `fd13930f...`, central
decision `3b534f91...`, runtime preflight `549c0db2...`, and one-use permit
`c7e8e1ca...`. All seven reconstruct exactly; the renderer emits a valid
745,243-byte MP4 from retained trace `6133ce58...`, Gate A verifies exact
129-episode R0 and held-out exclusion, and every attempt/result path is absent.
Reviewer 301 accepts signed pre-run receipt `525de8dc...` for preservation on
origin. No marker or model/optimizer/rollout action has occurred; after origin,
only the unchanged 10,000-update replacement may run once.

## 2026-07-16 - T20.43b stable-runtime implementation accepted

Spec `13c5bb4b...` preserves the exact signed T20.43 ACT campaign, policy
configuration, dataset, and dual-semantics evaluation while binding owner
addendum `8b4a206`, T20.44 terminal state, the stable LeRobot interpreter,
cached MuJoCo support tree, and a fresh real renderer smoke. The smoke freezes
trace identity `6133ce58...` and exact file SHA `f9dc0e6d...`; generic
post-marker failure signing replaces the retired missing-dependency-specific
writer. Eleven focused, 30 targeted/regression, and 34 pointer/composer/receipt
tests pass with offline lint/format and compilation. Reviewer 299 opens only
model-free materialization after origin; model, optimizer, rollout, retry,
hardware, network, external compute, and Brev remain closed.

## 2026-07-16 - T19.2e WCW-1A batched replacement verified and delivered

Brief 223/Reviewer 300 accepts the geometry-preserving WCW-1A-R1.1 packaging
at `fb0800e`. Five standard millimetre 3MF files provide a two-job 256 mm route
(coupon, then all 12 production parts together) and a four-job 180 mm fallback.
Every named object binds to its source STL and passes OPC/XML, CRC, triangle,
z=0, bed, spacing, margin, and exact-part-set checks; canonical comparison
proves all 13 STLs are geometrically unchanged. ZIP `553e8c63...` is 5,959,684
bytes with 54 CRC-valid entries and 52 manifest artifacts. Gmail replacement
message `19f6d4d052383966` tells the owner-named printer to disregard the older
ZIP and attaches the new ZIP plus README. Native Bambu Studio slice and all
physical print/QC evidence remain open and grant no T19.2c or robot authority.

## 2026-07-16 - T19.2d WCW-1A print package verified and delivered

Brief 221/Reviewer 298 accepts the offline WCW-1A-R1 printer package preserved
at `b24ac30`. The corrected parametric source separates nominal 20.0 mm ball
diameter from 0.8 mm diametral FDM allowance, preserves C0-C4 at body-frame
`y={empty,0,+15,+/-11,+/-15}` mm, and needs six of ten owned balls. All 13
binary STLs open, are outward-wound/watertight/manifold, and have zero Blender
BVH self-intersection pairs. Five tag36h11 labels decode as unique IDs 0-4 at
Hamming 0; the two-page 1:1 PDF and five required renders pass visual review.
ZIP `b650af2a...` is 5,455,354 bytes, has 42 CRC-valid entries, and matches its
40-artifact manifest. Gmail sent the ZIP plus separate printing README from
the authenticated owner account to the owner-named printer as message
`19f6d356a4121193`. This is software/manufacturing-preflight proof only; coupon,
printed-fit, retention shake, dimensions, label scale, and weigh-back remain
physical QC and do not open T19.2c or any robot/camera authority.

## 2026-07-16 - Brief 222 opens one stable-runtime ACT replacement

T20.44 result/review commit `9869cba` and synchronized state `b24ac30` are exact
on origin. Owner addendum `8b4a206` therefore activates one fresh T20.43b
implementation brief. The slice must preserve original ACT spec `b3a510f8...`
and its 10,000-update/checkpoint/dual-semantics recipe while replacing only the
failed renderer boundary with the stable T20.44 interpreter, cached MuJoCo
support tree, and a real-entrypoint smoke before any marker. Brief 222 grants
implementation/tests only; live smoke, authority, model, optimizer, rollout,
retry, hardware, network, external compute, and Brev remain closed.

## 2026-07-16 - T20.44 sole SmolVLA attempt verified terminal negative

Marker `cb01bcfb...` consumed the one-use permit. The fixed run completed 5,000
finite updates, all five checkpoints, and ten 244-frame chunk-50/receding-10
rollouts. Producer and independent verifier agree on result `9d916206...` and
run `3d49f4df...`; all ten strict-v2 outcomes are false and the first-pass
selector is null. Checkpoint 1,000/receding-10 reached the strongest partial
interaction at 73 strict-contact frames and 18.061 mm lift but still missed
the unchanged 25 mm and phase-duration conjunction. Reviewer 297 closes R2
with no retry. After origin preservation, owner addendum `8b4a206` routes to
one fresh T20.43b ACT replacement brief using the stable T20.44 renderer
runtime and unchanged ACT recipe; T20.45 remains pending.

## 2026-07-16 - T20.44 stable pre-run authority accepted

Authority commit `37ae581` preserves stable renderer smoke `11cbcca3...`, Gate
A `ef79292d...`, owner `6cc7f650...`, request `4a5163c1...`, central decision
`f9e817c4...`, runtime `7a3231a3...`, and permit `5301aa32...`. The stable
LeRobot Python and cached MuJoCo support tree reproduce the renderer, exact
R0 processor parity passes, snapshot/dependency hashes are exact, MPS is
available, 66.8 GB is free, and all run outputs are absent. Reviewer 296
accepts one fixed 5,000-update R2 attempt; signed acceptance `6e84de9e...`
must be origin-preserved before the marker. No model action or retry exists.

## 2026-07-16 - T20.44 stable interpreter correction accepted

The first model-free renderer smoke passed but recorded a deleted temporary uv
interpreter, so its untracked authority boundary is rejected. No marker, tensor
deserialization, model, optimizer, or rollout occurred. Spec `ec45331c...`
binds stable `external/lerobot/.venv/bin/python` plus an existing cached MuJoCo
3.3.5 support tree and requires that exact pair for preflight, run, and mirror
subprocesses. Twenty-two focused/pointer tests and direct stable imports pass.
Reviewer 295 opens only bounded rejected-artifact cleanup and stable
rematerialization after origin; Reviewer 296 remains required before the run.

## 2026-07-16 - T20.44 implementation accepted for model-free materialization

Spec `ec45331c...` binds exact R0, pinned SmolVLA/VLM snapshots, validated
expert-plus-state-projection scope, official batch-8 AdamW/cosine recipe for
5,000 updates, and five dual-semantics rollout checkpoints. The implementation
adds model-free Gate A, recursive dependency/cache checks, exact-runner-
interpreter renderer smoke, central/preflight/permit/marker contracts,
deterministic decode noise, complete trace/video/result evidence, and signed
terminal failure handling. Ten focused and 80 broader tests plus 30 subtests
pass. Reviewer 294 opens only live model-free materialization after origin;
weights, model, optimizer, rollout, retry, hardware, network, external compute,
and Brev remain closed.

## 2026-07-16 - Brief 220 opens T20.44 R2 SmolVLA standard rung

Origin commit `2e6a3e3` preserves Reviewer 293 and T20.43 terminal receipt
`b64ec6d0...`. Brief 220 opens tests-first implementation of exact R0 Gate A,
cached-base SmolVLA with the validated expert-plus-state-projection scope,
official batch-8 AdamW/cosine training for 5,000 updates, checkpoints
`[0,500,1000,2500,5000]`, dual-semantics strict-v2 rollouts, central authority,
and one-use terminal evidence. Before any future marker, the exact runner
interpreter must execute the real renderer on trace `6133ce58...` and preserve
a valid nonempty MP4/manifest. Live smoke, model weights, optimizer, rollout,
hardware, network/install, external compute, and Brev remain closed.

## 2026-07-16 - T20.43 consumed on renderer child dependency failure

The sole marker `064e5650...` consumed permit `7530e79d...` at 15:11:58 CDT.
Full ACT construction, cached backbone deserialization, optimizer creation,
checkpoint 0, and one chunk-50 policy-owned rollout completed. Zero optimizer
updates ran. Trace `6133ce58...` fails strict-v2 with zero strict contacts and
`3.0422519e-7` m lift; it is an untrained checkpoint-0 diagnostic, not trained
ACT evidence. Mirror rendering then launched the pinned LeRobot venv, whose
`import mujoco` exits 1, while the parent runtime has preflighted MuJoCo 3.3.5.
Terminal receipt `b64ec6d0...` binds the attempt, 206 MB checkpoint hash,
complete trace, missing mirror/full outputs, exact child probe, zero updates,
and no retry. Reviewer 293 closes R1 as a consumed infrastructure failure and
routes to a fresh T20.44 brief with an exact renderer-entrypoint smoke gate.

## 2026-07-16 - T20.43 pre-run authority accepted

Implementation `9a03a86` and compact-authority commit `2f2a2ca` are exact on
origin. Gate A `90217d2b...`, owner `60b3b8cb...`, request `79e190dd...`,
decision `6da74892...`, runtime preflight `860fabd7...`, and one-use permit
`7530e79d...` reconstruct with exact offline dependencies, MPS, cached
ResNet-18 bytes, zero scoped dirt, more than 10 GiB free, and all ten run paths
absent/unaliased. Reviewer 292 accepts one marker-bound full 10,000-update ACT
attempt and signed acceptance `7d742980...` binds its bytes. Model, optimizer,
inference, rollout, hardware, network, external compute, Brev, and retry remain
unused; the run opens only after this acceptance boundary is exact on origin.

## 2026-07-16 - T20.43 implementation accepted for compact materialization

Spec `b3a510f8...` fixes the full 10,000-update ACT recipe and seven dual-
semantics rollout checkpoints. Gate A probe `90217d2b...` verifies the R0
package, processors, training-only statistics, held-out exclusions, and
coordinate round trip without constructing a model. The central authority,
runtime, permit, marker, complete trace/T20.38/amended-report/mirror evidence,
first-pass selection, result, retention, and full verifier contracts pass nine
focused and 75 focused-plus-broad tests. Reviewer 291 opens only compact Gate A
and authority materialization after this implementation is exact on origin;
the marker and all model/optimizer/rollout actions remain closed.

## 2026-07-16 - Brief 219 opens T20.43 R1 ACT standard rung

Origin commit `f46c8aa` preserves Reviewer 290 and the verified R0 compact
boundary. Brief 219 opens only tests-first implementation of exact R0 Gate A,
the full official ACT recipe at 10,000 updates/batch 8, fixed checkpoints
`[0,500,1000,2500,5000,7500,10000]`, chunk-50 plus receding-10 rollout
semantics, strict-v2 traces/mirrors, central authority, preflight, one-use
permit, marker-first runner, and full verifier. No cached backbone tensor,
model, optimizer, checkpoint, inference, rollout, Gate C, hardware, network,
external-compute, or Brev action is authorized before the reviewed boundaries.

## 2026-07-16 - T20.42 R0 fixed generation verified

The sole marker-bound attempt completes all 128 fixed candidates exactly once:
119/119 training and 9/9 fresh-held-out candidates pass unchanged strict-v2,
with zero runtime or strict failures. The exact ten-episode T20.23 base appears
once, producing 129 training episodes, 31,366 frames, and 59,904 unpadded
windows. Held-out seeds 6-7 and all nine fresh-held-out successes contribute
zero training/statistics rows. Producer and independent full verification exit
0 with result `d238379b...`; mixture `37b30d34...`, statistics `02ba0e70...`,
and retention receipt `19d19fba...` reconstruct. Reviewer 290 verifies R0 and
routes to a fresh T20.43 ACT brief. No model, optimizer, learned rollout,
Gate C, hardware, network, external compute, or Brev action occurred.

## 2026-07-16 - T20.42b pre-run authority accepted

Five compact artifacts are exact at origin commit `93d7708`: owner grant
`b5d08b77...`, central request `5c5b99fc...`, decision `f6121762...`, runtime
preflight `ffa95218...`, and permit `94d7f2b2...`. Reviewer 289 confirms the
active owner window, unchanged `c435809` implementation, offline dependency
facts, 73.3 GB free, and all generation outputs absent. Signed acceptance
`97694eb5...` binds the reviewer bytes and authority commit. After its own
origin preservation, exactly one marker and the fixed 119+9 attempt may run.

## 2026-07-16 - T20.42b implementation accepted for authority materialization

Implementation `d24ad0e` plus docs-only-review ancestry correction `c435809`
are exact on origin. Reviewer 288 accepts the no-write live collector,
exclusive five-artifact materializer, fixed 119+9 runner, package dataset/
MEAN_STD path, terminal-negative route, full-output verifier, and signed
Reviewer 289 pre-run gate. Twenty-one focused, 82 broad, and eight MuJoCo
source tests pass; the live collector reports exact offline versions, zero
scoped dirt, ten absent/unaliased outputs, and 73.3 GB free. Only compact
authority materialization opens; marker and generation remain closed.

## 2026-07-16 - Brief 218 opens T20.42b materialization/fixed runner

The owner opens a fresh eight-hour simulation-only window at 12:35:56 CDT for
the one fixed 119-training plus nine fresh-held-out R0 attempt. Brief 218 first
implements and reviews the live runtime collector, exclusive compact-authority
materializer, and fixed scripted generation/compiler/dataset runner. Authority
artifacts remain absent until that implementation is reviewed on origin; the
marker and MuJoCo execution remain closed until a second pre-run review.
Hardware, network, external compute, Brev, model, optimizer, retry, and R1 stay
closed.

## 2026-07-16 - T20.42a generation-authority contracts verified

Implementation `c2a4512` plus marker-alias coverage `9530671` are exact on
origin. The construction-only module re-verifies exact T20.42 source/file
hashes and inherited central authority, composes only
`simulation_training_ready`, freezes the ordered 119+9 manifest and seeds 6-7
as references, requires a clean origin-bound offline runtime with 10 GiB free,
and writes the permit-consuming marker exclusively before the first candidate.
Nine focused, 70 broad, and eight MuJoCo source tests pass. Reviewer 287
accepts Brief 217 implementation only; no authority artifact or execution
exists, and expired owner/run windows cannot authorize materialization.

## 2026-07-16 - Brief 217 opens T20.42a generation-authority contract

Reviewer 286's accepted construction boundary is the sole source for a new
model-free authority-contract slice. Brief 217 may implement and fixture-test
an exact central request, runtime preflight, one-use permit, and marker-first
consumption contract bound to implementation `23cb5fb` and review `c87ee84`.
It may not materialize authority artifacts or execute the 119+9 manifest.

## 2026-07-16 - Brief 216 opens T20.42/R0 dataset expansion

The owner decision `ae75bb59...` closes the T20.41 route blocker and selects
dataset expansion by construction before any standard-recipe policy rung.
Brief 216 opens only tests-first implementation of the deterministic candidate,
split, generator, compiler, training-only statistics, and manifest contracts.
The fixed generation must eventually yield 64-128 new nominal strict-v2
successes; existing seeds 6-7 and a fresh disjoint pose band remain held out.
Actual generation requires a separately reviewed origin boundary, central
decision, preflight, and one-use permit. Hardware, network, optimizer,
external compute, and Brev remain closed, and T19.2c stays a separate pending
physical side lane.

Implementation `23cb5fb` then freezes construction spec `b58a6b31...`,
admission fixture `b7b1eb77...`, and fail-closed preflight `5ff8c5cc...`.
Reviewer 286 accepts the contract implementation only: 119 unique training
candidates, nine disjoint fresh-held-out specs, the exact T20.23 base once,
and training-only MEAN_STD fixture membership verify. Generation remains
closed pending a fresh central decision, runtime preflight, one-use permit,
and separate pre-run review.

## 2026-07-16 - Brief 211 opens additive receipt/archive hardening

Independent closeout review found that T20.38 lacked explicit missing-source
and genuine contradiction tests and could name a numeric bottleneck while an
actor/evidence guard was the effective blocker. T20.39's generic archive index
did not cross-check every top-level authority flag against routing and allowed
a non-active same-fingerprint duplicate to drift outside its semantic core.
Brief 211 opens a model-free additive correction only. Historical results,
policy routing, Gate C, replay, training, hardware, network, external compute,
and Brev remain closed.

## 2026-07-16 - T20.39a receipt/archive hardening verified

Implementation `83d51c5` is exact on origin. T20.38 receipt `042bf0be...`
adds explicit hard-guard blockers, guard-preempting effective bottleneck, and
missing-source/genuine-contradiction coverage. T20.39 receipt `60babc53...`
and index `043d45b3...` bind top-level authority to routing/source proof,
reject conflicting inactive duplicates, and deterministically require invalid,
replay-ineligible, history-preserving disposition for stale sources. Twenty-
four contract tests, 12 pointer tests, and both exact CLIs pass. Reviewer 280
amends Reviewer 278/279's completeness claims without changing their proof
boundaries or the blocked T20.41 route.

## Rules

- Update this ledger at task start and after every verification boundary.
- After every ledger or per-task `project_state.json` update, run
  `python3 scripts/robot_lab/sync_project_state_pointers.py --apply` so the
  top-level `current_task`, `next_eligible_task`, and
  `latest_verified_task_implementation_boundary` pointers never lag the
  per-task entries; the pair-cycle wrapper fails closed on `--check` drift.
- Commit feature, compiler-run, training, and evaluation boundaries separately.
- Raw rollout bytes are append-only and never reinterpreted without a new compiled view.
- `recovery` is a control mode, never a task phase.
- Unknown coordinate, owner, prompt, or temporal semantics are quarantined.
- No M20-M22 task may start while `training_lock` is `closed`.
- Live read-only census/camera capture is conditionally owner-authorized only
  after verified T16.5a while the owner-presence lease is active.
- The latest owner message is final confirmation for one exact initial
  no-op-equivalent then one-joint displacement-and-return permit. No second
  prompt is required, but no write or motion occurs unless the signed,
  content-addressed, session-scoped permit and every prerequisite validate.
- Any additional joint, gripper, reach, contact, task, policy actuation, or
  material permit expansion is unauthorized.
- States are `pending`, `in_progress`, `verified`, `blocked`, `deferred`, and `superseded`.

## 2026-07-16 - T20.36o bounded optimizer runner accepted

Implementation `9f3538e` is exact on origin. The runner creates the attempt
marker before tensor/model/optimizer access; binds five masked correction
contexts, 250 retained paths, 1:1 unique replay, five registered probe points,
base-noise verification, exact repeats, full tracked tensors, and the
first-pass-or-2,500-update stop. Thirty-six combined tests pass. A live
non-consuming preflight returned permit `f9bad1ae...` and spec `50e0569d...`
with every output still absent. Reviewer 276 authorizes the sole attempt only
after this review boundary is confirmed on origin. Gate C, hardware, network,
external compute, and Brev remain closed.

## 2026-07-16 - T20.36o terminal bounded negative

The sole attempt completed exactly 2,500 finite updates and all five registered
probe checkpoints. Source-objective ratios pass throughout, but amended action
violations remain 2,045/2,010/1,368/1,738/1,677 and the final checkpoint passes
0/25 probes. Update 2,000 briefly passes only start zero. Result `ec7fb323...`,
probe artifact `ea56b602...`, uniform supplement `70e98c06...`, and local
checkpoint tree `6e202dc5...` verify; bundle `f1744a0` is on origin. Reviewer
277 closes the X/current-candidate Gate C route without a rollout or retry and
activates model-free Brief 209 / T20.38.

## 2026-07-16 - T20.38 quantitative strict-v2 receipt verified

Historical receipt `02268a1a...` first bound the immutable strict-v2 analytic fixture and
evaluator source into 33 direction-correct, actor/evidence-guarded predicate
margins with hard conjunction and deterministic bottleneck semantics. It
agrees with source semantic success while explicitly withholding policy,
actual-MuJoCo, physical, and training claims. Twenty-four tests pass;
implementation `f9c3682` is on origin. Reviewer 280 amends the current derived
receipt to `042bf0be...` through hardening implementation `83d51c5`.

## 2026-07-16 - T20.39 archive verified and window closed

Historical receipt `8277b09f...` and index `05908b6d...` first bound one active, evidence-only
T20.19 source-controller boundary negative with replay/training/policy-blame
denied. The full trace is not remotely retained, so replay remains ineligible.
Fifteen tests pass and implementation `80d2992` is on origin. Reviewer 280
amends the current derived receipt/index to `60babc53...`/`043d45b3...`
through hardening implementation `83d51c5`; T20.40 remains deferred. The later
owner decision `ae75bb59...` resolves T20.41 and routes to Brief 216/T20.42.

## 2026-07-15 - Owner continuation resumes T20.35 capability ladder

The owner resumed the existing durable MVP objective and opened a fresh
simulation-only eight-hour window from 07:27 through hard closeout 15:27 CDT,
with no new major slice after 14:42. The active prompt is
`t20-capability-ladder-goal-loop.md`. T20.35 remains the sole current task under
Brief 166: implement, test, centrally authorize, review, commit, push, and
remotely confirm the exact rank-16 pre-run boundary before any model load or
optimizer creation. Hardware, cameras, serial devices, external compute, Brev,
promotion, and physical transfer remain closed. Session Log 200 records the
resume, and Reviewer 197 permits only T20.35 preflight implementation.

## 2026-07-15 - T20.35 rank-capacity pre-run boundary accepted

Implementation `579855f` mechanically derives the rank-16 spec from the
archived T20.33 spec, rejecting any campaign, batch, seed, processor, gate, or
authority drift. The signed spec is `ccd6ef2b...`; central composition
`0cd37ea2...` grants only `simulation_training_ready` through the current hard
closeout. Fifty-eight relevant tests pass. An adversarial review closed the
inherited retry hole by requiring an immutable attempt marker before model
construction. Session Log 201 and Reviewer 198 authorize exactly one local-MPS
run after this review is confirmed on origin. No model or optimizer has run.

## 2026-07-15 - T20.35 rank-capacity discriminator verified negative

The sole counted attempt `f58f435a...` completed all 500 updates with finite
objectives and gradients. Run `6e0dd4e2...`, checkpoint `0dea38b3...`, and
result `99538521...` are exact. Rank 16 exposes 1,287,168 trainable parameters,
exactly four times rank 4, and cuts the five-seed objective ratio from 0.528248
to 0.155307. It still misses the 0.10 gate; all five decoded maximum errors
miss 0.05 rad at 0.708520-1.467995 rad. Reviewer 199 accepts a verified Gate B
failure. There is no retry, Gate C route, campaign, or policy acceptance.
T20.35a is next as an optimizer-free exact module/tensor coverage audit.

## 2026-07-15 - Brief 167 opens T20.35a PEFT module coverage audit

T20.35a binds the immutable rank-16 adapter and enumerates actual saved LoRA
module pairs, tensor shapes, dtypes, elements, and nonzero counts without model
construction, inference, or an optimizer. The five required action/state
pathways must be present as actual `lora_A`/`lora_B` pairs; the configured
target regex alone cannot pass. Missing coverage routes to a separately
reviewed expert-only unfreeze capacity ceiling. No training or broader
authority is granted.

## 2026-07-15 - T20.35a PEFT module coverage verified

Audit `d1109ae8...` binds the exact T20.35 run and checkpoint and enumerates 76
finite saved tensors totaling 1,287,168 elements. They form 38 complete LoRA
pairs: 36 q/v projections across all 18 expert-attention layers, plus
`action_in_proj` and `action_out_proj`. `state_proj`,
`action_time_mlp_in`, and `action_time_mlp_out` are absent even though the
declared regex names them. Reviewer 200 accepts a real target-coverage failure
and routes T20.35b to the planned no-LoRA expert-only capacity ceiling. No
model, inference, optimizer, hardware, external compute, or Brev ran.

## 2026-07-15 - Brief 168 opens T20.35b PI0.5 coverage correction

Pinned source review shows that PI0.5 intentionally has no `state_proj` and
uses `time_mlp_in/out`, while its default PEFT regex requests the stale names
`action_time_mlp_in/out`. T20.35a therefore found a genuine missing time-MLP
coverage fault but used one impossible state requirement and stale MLP names.
Brief 168 corrects the signed audit semantics without changing the immutable
adapter or running a model, inference, or optimizer. The no-LoRA capacity
ceiling remains closed until the correction is verified and remotely saved.

## 2026-07-15 - T20.35b PI0.5 coverage correction verified

Corrected audit `446a0686...` binds stack `c8e903e7...` and pinned PI0.5
source `b05b6afe...`. PI0.5 intentionally has no `state_proj`; its four real
modules are action in/out and `time_mlp_in/out`. The default PEFT regex instead
names nonexistent `state_proj` and stale `action_time_mlp_in/out`. The saved
adapter therefore genuinely misses both real time-MLP layers. Reviewer 201
supersedes only T20.35a's generic pathway decision while preserving its exact
tensor enumeration, and routes T20.35c to the no-LoRA expert-only capacity
ceiling. No model, inference, optimizer, or authority change occurred.

## 2026-07-15 - Brief 169 opens T20.35c expert-only capacity ceiling

T20.35c preserves the exact T20.33 batch, processors, constant `2.5e-5`
learning rate, 500 updates, seeds, and Gate B thresholds while removing PEFT as
the only adaptation-boundary change. PaliGemma must be entirely frozen; the
complete Gemma action expert plus action in/out and real `time_mlp_in/out`
projections must be the only trainable parameters. A new signed central
training-only decision and same-agent pre-run review must be remotely preserved
before a signed one-attempt marker permits model construction. Retry, Gate C,
hardware, external compute, and Brev remain closed.

## 2026-07-15 - T20.35c expert-only pre-run boundary accepted

Implementation `82614ec` derives expert-only spec `6c10a1c7...` from the frozen
T20.33 contract and binds corrected audit `446a0686...`. Central decision
`75dc9c7d...` grants only `simulation_training_ready` through the current hard
closeout. Sixty-nine relevant tests pass. Reviewer 202 confirms that the
runner rejects PEFT, any trainable PaliGemma parameter, incomplete Gemma/action/
time-MLP coverage, non-finite values, checkpoint drift, and forbidden
authority. Its immutable attempt marker precedes model construction. Exactly
one local-MPS run is next; no model or optimizer has run.

## 2026-07-15 - T20.35c expert-only capacity ceiling verified mixed-negative

The sole attempt `43b2b721...` completed 500 finite updates. Run `9b1af8ee...`
binds 693,422,112 trainable expert/projection elements, zero trainable
PaliGemma elements, and checkpoint `439ae119...`. Result `f6f6b024...` cuts the
objective ratio from rank 16's 0.155307 to 0.004252 and passes the 0.10 gate.
All five decoded mean and maximum errors improve, but maximum errors remain
0.091908-0.150321 rad and fail the 0.05 gate. Reviewer 203 keeps Gate B closed
and routes T20.35d to optimizer-free exact checkpoint replay plus joint/time
residual localization. No retry, Gate C work, policy acceptance, hardware,
external compute, or Brev occurred.

## 2026-07-15 - Brief 170 opens T20.35d residual localization

T20.35d is an optimizer-free deterministic replay of the immutable T20.35c
expert-only checkpoint. It must reproduce all five decoded hashes and metrics
before retaining the full action/residual matrices and localizing every 0.05
rad threshold exceedance by seed, timestep, and joint. A separately reviewed
evaluation-only boundary must be remotely preserved before model construction
or inference. Training, checkpoint mutation, Gate C work, policy acceptance,
hardware, external compute, and Brev remain closed.

## 2026-07-15 - T20.35d replay boundary accepted

Implementation `7162497` and spec `b083c593...` bind the exact T20.35c result,
run, 2.77 GB checkpoint tree, dataset target, seeds, hashes, and metrics.
Permit `bd3b0933...` narrows the active authority to one model-load/inference
replay with no optimizer or checkpoint mutation. Seventy-six relevant tests
pass. Reviewer 204 requires exact reproduction before any residual
interpretation. No T20.35d model construction or inference has occurred.

## 2026-07-15 - T20.35d residual localization verified

Attempt `d3b3ff43...` reproduces all five expert-only decoded hashes exactly.
Report `13b08e70...` retains the target, decoded, and residual matrices plus 366
threshold-exceedance coordinates. Only 34/366 (9.29%) occur at chunk
boundaries. Wrist roll has 164, gripper 121, wrist flex 52, shoulder lift 29,
and shoulder pan/elbow zero; wrist roll plus gripper hold 77.87%. Reviewer 205
accepts the measurements but routes T20.35e to a model-free top-two-channel
semantic correction because the predeclared single-joint classifier labels the
pattern distributed. No optimizer, Gate C work, hardware, external compute, or
Brev occurred.

## 2026-07-15 - Brief 171 opens T20.35e classification correction

T20.35e preserves report `13b08e70...` unchanged and adds a deterministic 75%
top-two-joint concentration test to the original single-joint/boundary
classifier. It runs no model, inference, optimizer, or checkpoint operation.
A positive multi-channel result routes only to a separately reviewed
normalized-space residual and target-saturation audit before any action or
training correction.

## 2026-07-15 - T20.35e multi-channel correction verified

Correction `f2a8aa80...` binds report `13b08e70...` without changing its
matrices, coordinates, counts, original class, or original route. The
deterministic ranking selects wrist roll (164) and gripper (121); together they
hold 285/366 exceedances (77.87%), above the declared 75% top-two threshold,
while single-joint and boundary thresholds remain false. Reviewer 206 accepts
the derived `multi_joint_output_channel_concentrated` semantic and routes only
to T20.35f's model-free normalized-space residual and target-saturation audit.
Verifier correction `3013ded` makes archive checking honor the same declared
`1e-15` metric tolerance used by replay construction while retaining exact
types, hashes, structure, counts, and non-float values. Four focused and 81
relevant tests pass. No model, inference, optimizer, checkpoint read, Gate C
work, hardware, external compute, or Brev occurred.

## 2026-07-15 - Brief 172 opens T20.35f normalized residual audit

T20.35f binds the exact T20.35d report, T20.35e channel correction, T20.17
dataset action statistics, PI0.5 QUANTILES implementation, 10-step sampler
default, and SceneSmith coordinate conversion. It distinguishes normalized
targets outside `[-1, 1]` from actual clipping, preserves the physical error
gate in normalized units, and decomposes retained five-seed squared error into
systematic bias and seed variance. A 75% bias-share discriminator may route a
separately reviewed inference-only cadence probe; it grants no model,
inference, optimizer, checkpoint, dataset, Gate C, hardware, external-compute,
or Brev authority.

## 2026-07-15 - T20.35f normalized residual audit verified

Audit `85c24c5c...` reproduces the 164 wrist-roll and 121 gripper physical
exceedances in exact PI0.5 QUANTILES space. The normalizer does not clip and
neither channel has any target or decoded physical-bound hit. Wrist roll has
39/50 target steps outside the q01-q99 range and an 84.81% systematic-bias
share; gripper has 32/50 and 82.33%. Reviewer 207 accepts the evidence and
routes T20.35g to an inference-only denoising-cadence discriminator against the
pinned 10-step default. Three focused and 84 relevant tests pass. No model,
inference, optimizer, checkpoint access, dataset write, Gate C work, hardware,
external compute, or Brev occurred.

## 2026-07-15 - Brief 173 opens T20.35g cadence discriminator

T20.35g freezes cadence values 10, 20, and 50 with the same expert-only
checkpoint, exact batch, and five initial-noise seeds. The 10-step baseline
must reproduce all T20.35d hashes before candidate interpretation. Gate B may
pass only if all five chunks meet 0.05 rad; otherwise cadence is directionally
positive only if both worst-seed maximum and aggregate mean error improve. One
separately reviewed local-MPS inference attempt is the entire runtime scope;
optimizer, training, checkpoint/data mutation, Gate C, hardware, external
compute, and Brev remain closed.

## 2026-07-15 - T20.35g pre-run boundary accepted

Implementation `88602b0`, spec `be1c50f3...`, and permit `ca3dbd3f...` freeze
the exact expert-only checkpoint, batch, five seeds, 10-step baseline hashes,
candidate cadences 20/50, metrics, gates, and fail-closed routes. Reviewer 208
authorizes one local-MPS model-load/inference attempt after remote preservation.
Four focused and 89 relevant tests pass. No model, checkpoint tensor, inference,
optimizer, training, mutation, Gate C, hardware, external compute, or Brev
activity occurred at this boundary.

## 2026-07-15 - T20.35g attempt 001 runtime failure and replacement

Attempt `788015fa...` consumed permit `ca3dbd3f...`, validated the checkpoint
tree and CPU tensor manifest, then failed while Python 3.14 parsed the cached
PI0.5 config. No model, inference, optimizer, mutation, or result exists.
Preflight `d476382b...` proves Python 3.12 parses the same pinned config without
checkpoint/model access. Correction `b077d19` creates distinct spec
`44076248...` and permit `b3078ea0...`, binds the consumed evidence, and rejects
any non-3.12 replacement runtime. Reviewer 209 authorizes one replacement
attempt. Five focused and 90 relevant tests pass; all other authorities remain
closed.

## 2026-07-15 - T20.35g cadence discriminator verified negative

Replacement attempt `83c215ca...` reproduced all five signed 10-step hashes.
Result `57f1f0dd...` records no Gate B pass and no positive cadence effect. The
baseline worst/aggregate errors are `0.150321`/`0.030990` rad; 20 steps worsen
them to `0.159251`/`0.033813`, and 50 steps worsen them to
`0.167722`/`0.035237`. Reviewer 210 rejects cadence expansion and routes
T20.35h to a model-free leave-one-seed-out output-bias correction ceiling.
The sole replacement permit is consumed. No optimizer, training, mutation,
rollout, Gate C, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 174 opens T20.35h decoded-action bias ceiling

T20.35h binds result `57f1f0dd...`, its exact 10-step five-seed chunks, and the
immutable target. For each held-out seed, calibration may use only the other
four seeds. It compares one six-channel offset averaged across calibration
time/seed positions with one 50-by-6 time-conditioned offset averaged across
calibration seeds. The gate remains 0.05 rad on every held-out element. This is
a post-hoc analytical ceiling only: it cannot pass Gate B, select a product
correction, load a model, create an optimizer, mutate evidence, or enter Gate C.

## 2026-07-15 - T20.35h decoded-action bias ceiling verified mixed-negative

Artifact `63e1181b...` reproduces the exact T20.35g baseline. Global-channel
bias reduces worst/aggregate error from `0.150321`/`0.030990` to
`0.113302`/`0.019781` rad but leaves 159 exceedances. Time-conditioned bias
reduces aggregate mean to `0.017710` and leaves 96 exceedances, but its worst
fold remains `0.136460` rad. Neither analytical ceiling passes. A verifier-only
`1e-15` tolerance preserves cross-runtime replay while identities, hashes,
types, counts, routes, and non-float claims remain exact. Reviewer 211 routes
T20.35i to model-free residual-variance localization. Six focused and 76
relevant tests pass. No model, checkpoint, inference, optimizer, mutation,
rollout, Gate C, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 175 opens T20.35i residual-variance localization

T20.35i binds T20.35h artifact `63e1181b...`, recomputes its exact
time-conditioned held-out corrected hashes from T20.35g, and localizes all
remaining `>0.05` rad elements. Seed and channel single/top-two concentration
thresholds are 50%/75%; the first/last-five-timestep boundary threshold is 60%.
A distributed result may route one separately reviewed inference-only
initial-noise-scale discriminator. No result may pass Gate B, select a
correction, load a model, create an optimizer, mutate evidence, or enter Gate C.

## 2026-07-15 - T20.35i residual-variance localization verified

Report `ac87de7b...` reconstructs all five corrected hashes and the exact 5/4
identity. Its 96 exceedances cover every seed; the top two seeds account for
56.25%, top two channels 67.71%, and first/last-five boundaries 31.25%. All are
below 75%/75%/60% gates, so the classification is
`distributed_seed_channel_variance`. Seventy-six unique timestep/channel
positions fail; maximum raw five-seed spread is `0.183018` rad. Reviewer 212
routes T20.35j to one separately reviewed inference-only initial-noise-scale
discriminator. Five focused and 81 relevant tests pass in addition to
cross-runtime verifier replay. No model, checkpoint, inference, optimizer,
mutation, rollout, Gate C, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 176 opens T20.35j initial-noise scale discriminator

T20.35j freezes scales `1.0`, `0.5`, and `0.0` while preserving 10 denoising
steps, the exact expert-only checkpoint, batch, five seeds, preprocessing,
postprocessing, and action gates. The same seed must generate the same standard
normal tensor before scale multiplication. Scale 1.0 must reproduce all five
T20.35g hashes exactly. A candidate is directionally positive only if worst
maximum, aggregate mean, and aggregate cross-seed spread all strictly improve.
One reviewed local-MPS inference attempt is the entire runtime scope; no model
access occurs before a remotely preserved one-use permit, and no optimizer,
mutation, Gate C, hardware, external compute, or Brev authority exists.

## 2026-07-15 - T20.35j pre-run boundary accepted

Implementation `ed05689`, spec `a3dc0acb...`, and permit `545a71c6...` bind
T20.35i, the exact expert-only checkpoint/batch, sampler source hash, scale-1
baseline hashes, scales `1.0/0.5/0.0`, five seeds, 10 steps, metrics, gates, and
routes. The runner regenerates each seed's standard-normal tensor for every
scale, records its hash, and fails unless hashes agree across scales. Reviewer
213 authorizes one Python 3.12 local-MPS model-load/inference attempt after
remote preservation. Five focused and 86 relevant tests pass. No model,
checkpoint tensor, inference, optimizer, mutation, rollout, Gate C, hardware,
external compute, or Brev action occurred at this boundary.

## 2026-07-15 - T20.35j initial-noise scale discriminator verified positive non-pass

The one consumed attempt `61eca0ab...` produced signed result `e9bbff84...`,
preserved at `06b3a0a`. Scale 1.0 exactly reproduced all five baseline action
hashes and recorded identical per-seed base-noise hashes across scales. Scale
0.5 improved worst maximum, aggregate mean, and raw cross-seed spread from
`0.150321`/`0.030990`/`0.046392` rad to
`0.084120`/`0.024630`/`0.018129`; scale 0.0 improved them to
`0.073360`/`0.024130`/`0.0`. Both candidates remain above the 0.05-rad action
gate, so Gate B and Gate C stay closed. Reviewer 214 routes T20.35k to a
model-free sampler/noise-distribution audit. The signed verifier, 38 relevant
tests, and 6 subtests pass under Python 3.12. No optimizer, training, mutation,
rollout, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 177 opens T20.35k sampler/noise-distribution audit

T20.35k binds the exact active runtime model/config source and T20.35j result,
then mechanically extracts the standard-normal sampler, training interpolation
and velocity target, inference initial state and Euler time grid, action padding,
and loss truncation semantics without importing or loading the model. The audit
must distinguish the six supervised action dimensions from the 26 padded
dimensions that enter the action projection. It may route a separately reviewed
active-versus-padded noise-mask discriminator, but cannot call a model, change a
sampler, pass Gate B, enter Gate C, create an optimizer, or grant broader
authority.

## 2026-07-15 - T20.35k sampler/noise-distribution audit verified

Signed audit `bc9f0845...`, preserved at `357cd6e`, mechanically parses the
exact active model/config sources without importing the model. Training and
inference both use standard-normal noise; training uses Beta(1.5,1.0) with
scale `0.999` and offset `0.001`, while inference follows the expected 10-step
Euler grid. The six action channels are padded to 32, random noise enters all
32 through `action_in_proj`, and direct loss plus returned actions are truncated
to six. Reviewer 215 accepts this as a plausible exposure mechanism, not causal
proof, and routes T20.35l. Forty-three relevant tests and 14 subtests pass;
cross-runtime verification is exact. No model, checkpoint, optimizer, training,
mutation, rollout, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 178 opens T20.35l active-versus-padded noise masks

T20.35l reuses T20.35j's signed all-normal and all-zero endpoints and the same
base-noise hash per seed. One reviewed inference-only attempt evaluates exactly
two new masks: normal noise in the six active dimensions with zeros in the 26
padded dimensions, and the complementary active-zero/padded-normal mask. It
must preserve checkpoint, batch, processors, five seeds, 10 steps, action gate,
and source hashes. No optimizer, training, rollout, Gate C, hardware, external
compute, or Brev authority exists.

## 2026-07-15 - T20.35l pre-run boundary accepted

Implementation `2f04395`, spec `4c346688...`, and permit `5b990e78...` bind
T20.35j/k, exact checkpoint/batch/processors, five base-noise hashes, 10 steps,
six active and 26 padded dimensions, both inherited endpoints, two mixed masks,
metrics, routes, and all closed authorities. The runner validates the same
base-noise hash before every new call and writes its immutable attempt marker
before model import or checkpoint tensor access. Reviewer 216 authorizes one
Python 3.12 local-MPS model-load/inference attempt after remote preservation.
Sixty relevant tests and 17 subtests pass. No model, checkpoint tensor,
inference, optimizer, mutation, rollout, Gate C, hardware, external compute, or
Brev action occurred at this boundary.

## 2026-07-15 - T20.35l active-versus-padded noise masks verified joint-positive

The one consumed attempt `adf33ca1...` produced signed result `b4fc6060...`,
preserved at `1040478`. All-normal worst/mean/spread are
`0.150321`/`0.030990`/`0.046392` rad. Active-normal/padded-zero improves them to
`0.114173`/`0.028504`/`0.034544`; active-zero/padded-normal improves them to
`0.066398`/`0.020908`/`0.009970`; all-zero gives
`0.073360`/`0.024130`/`0.0`. Both mixed masks are directionally positive, but
neither passes 0.05 rad. Reviewer 217 routes the model-free T20.35m factorial
interaction audit. No optimizer, training, mutation, rollout, Gate C, hardware,
external compute, or Brev action occurred.

## 2026-07-15 - Brief 179 opens T20.35m factorial interaction audit

T20.35m binds the four signed T20.35l conditions and computes active-noise and
padded-noise effects at both complementary settings plus the 2x2 interaction
contrast for worst error, aggregate mean, and raw spread. It is model-free and
cannot reinterpret a diagnostic mask as a policy. A dominant active-noise
effect may route one separately reviewed near-zero active-noise-scale
discriminator with padded noise held normal; no model, optimizer, Gate C, or
broader authority exists in this slice.

## 2026-07-15 - T20.35m factorial interaction audit verified

Signed audit `83105424...`, preserved at `2ba6d8e`, computes all 15 required
contrasts without model access. Active noise is harmful at both padded settings
for worst error, aggregate mean, and spread. Worst-error active effects are
`+0.040813` with padded zero and `+0.083923` with padded normal; interaction is
`+0.043111`. Padded-noise worst/mean effects are beneficial at active zero but
harmful at active normal. Reviewer 218 routes T20.35n to keep padded noise normal,
inherit active-scale endpoints 0 and 1, and evaluate only 0.25/0.5. Fifty-two
relevant tests and 24 subtests pass; no model, optimizer, Gate C, hardware,
external compute, or Brev action occurred.

## 2026-07-15 - Brief 180 opens T20.35n near-zero active-noise scales

T20.35n freezes padded dimensions at normal base noise and active dimensions at
scales `0.0`, `0.25`, `0.5`, and `1.0`. The 0 and 1 endpoints are inherited
from signed T20.35l chunks; exactly two new conditions are evaluated under one
reviewed inference-only permit. Checkpoint, batch, processors, base-noise hashes,
five seeds, 10 steps, and 0.05-rad gate remain fixed. No optimizer, training,
rollout, Gate C, hardware, external compute, or Brev authority exists.

## 2026-07-15 - T20.35n pre-run boundary accepted

Implementation `04f7d3b`, spec `155d9336...`, and permit `f821bd57...` bind
T20.35l/m, exact checkpoint/batch/processors, five base-noise hashes, 10 steps,
active-scale endpoints 0/1, new scales 0.25/0.5, padded scale 1, metrics, routes,
and all closed authorities. The runner validates the signed base-noise hash
before every new call and writes the immutable attempt marker before model
import or checkpoint tensor access. Reviewer 219 authorizes one Python 3.12
local-MPS model-load/inference attempt after remote preservation. Fifty-seven
relevant tests and 24 subtests pass. No model, checkpoint tensor, inference,
optimizer, mutation, rollout, Gate C, hardware, external compute, or Brev action
occurred at this boundary.

## 2026-07-15 - T20.35n active-noise scale discriminator verified endpoint-optimal

The one consumed attempt `c8eecd80...` produced signed result `d3e6e5d9...`,
preserved at `4e37e19`. With padded noise fixed normal, active scales
0/0.25/0.5/1 yield worst errors
`0.066398`/`0.082665`/`0.102040`/`0.150321` rad, aggregate means
`0.020908`/`0.022312`/`0.024290`/`0.030990`, and monotonically increasing
spread. No condition passes 0.05 rad. Reviewer 220 rejects further active-scale
refinement and routes T20.35o to trajectory-level flow-consistency
instrumentation. No optimizer, training, mutation, rollout, Gate C, hardware,
external compute, or Brev action occurred.

## 2026-07-15 - Brief 181 opens T20.35o flow-trajectory consistency audit

T20.35o freezes the active-zero/padded-normal condition, exact checkpoint,
batch, processors, five seeds, and 10-step path. A reviewed inference-only
runner must reproduce all five signed decoded chunks while recording each
pre-update state and learned velocity. For the deterministic memorized target,
the reference velocity at time `t>0` is `(x_t-target)/t`; the audit localizes
finite residual by step, active channel, and padded dimensions. No source
mutation, optimizer, training, action correction, rollout, or Gate C authority
exists.

## 2026-07-15 - T20.35o pre-run boundary accepted

Implementation `100a76e`, spec `c21c4d48...`, and permit `65c516f3...` bind
T20.35n's exact active-zero/padded-normal endpoint, checkpoint, batch,
processors, five seeds and base-noise hashes, 10-step grid, decoded endpoint
hashes, residual math, routing thresholds, and all closed authorities. The
runner captures but does not alter each denoise step and writes the immutable
attempt marker before model import or checkpoint tensor access. Reviewer 221
authorizes one Python 3.12 local-MPS model-load/inference attempt after remote
preservation. Eleven relevant tests pass; spec and permit verify under Python
3.11 and 3.12. No model, checkpoint tensor, inference, optimizer, mutation,
rollout, Gate C, hardware, external compute, or Brev action occurred at this
boundary.

## 2026-07-15 - T20.35o terminal flow residual verified

The sole consumed attempt `5161631f...` produced signed result `5c5b41b9...`,
preserved at `30b5b0a`. All five active-zero/padded-normal decoded endpoints
reproduce exactly. Aggregate active residual mean rises from `0.033131` at
time 1.0 to `0.368387` at time 0.1, with `62.8898%` of active residual mass in
steps 7-9. Channel 5 is largest but accounts for only `24.7865%`, so Reviewer
222 verifies a terminal-time distributed residual rather than a channel-only
fault. Gate B and Gate C remain closed. Brief 182 opens T20.35p for one bounded
expert-only correction on the exact 15 retained late-step state/time examples.
No optimizer, training, mutation, rollout, hardware, external compute, or Brev
action occurred in T20.35o.

## 2026-07-15 - T20.35p pre-run boundary accepted

Implementation `7ee3803`, spec `fd4f75f6...`, and central authority
`c69090da...` bind the exact T20.35c checkpoint, 15 signed T20.35o late-step
examples, reconstruction hashes and tolerances, a balanced 30-use-per-example
schedule, 450 constant-LR expert-only updates, complete optimizer settings,
and the five-seed active-zero/padded-normal evaluation. Gate B retains the
original standard-objective baseline as well as the 0.05-rad action gate.
Reviewer 223 authorizes exactly one Python 3.12 local-MPS training/evaluation
attempt after remote preservation. Thirty-six relevant tests pass. No model,
checkpoint tensor, optimizer, training, rollout, Gate C, hardware, external
compute, or Brev action occurred at this boundary.

## 2026-07-15 - T20.35p terminal correction verified objective-pass/action-fail

The sole consumed attempt `31be48e4...` completed 450 finite updates and
produced run `283c5745...`, checkpoint `9358cee4...`, and signed result
`cde1347f...`, preserved at `7dba33e`. The 15-example correction objective
falls from `0.089803` to `0.003965` (ratio `0.044154`); the original standard
objective remains inside Gate B at ratio `0.046483`. Nevertheless every
decoded chunk fails 0.05 rad with maxima `0.127310–0.157144`, worse than the
source active-zero endpoint. Reviewer 224 prohibits another training run and
routes T20.35q to compare the new self-generated path against T20.35o and the
target flow. Gate B and Gate C remain closed. No rollout, hardware, external
compute, or Brev action occurred.

## 2026-07-15 - T20.35q pre-run boundary accepted

Implementation `fbc1087`, spec `fdb2fe3e...`, and permit `ab85aede...` bind
the exact T20.35p checkpoint and endpoints, T20.35o source paths, target,
processors, five base tensors, 10-step grid, 0.01 material thresholds,
classification precedence, and all closed authorities. Reviewer 225 authorizes
exactly one Python 3.12 local-MPS inference-only attempt after remote
preservation. Forty relevant tests pass. No model, checkpoint tensor,
inference, optimizer, training, rollout, Gate C, hardware, external compute,
or Brev action occurred at this boundary.

## 2026-07-15 - T20.35q early/mid-path interference verified

The sole consumed attempt `57d0f2ec...` produced signed result `6ba4954c...`,
preserved at `21ced86`, and reproduced every T20.35p endpoint. Mean active
target residual worsens by `0.067819` at step 0, before the state paths differ,
and active displacement exceeds the material threshold at step 2. Maximum
active displacement `0.078061` exceeds padded displacement `0.060895`, so the
classification is early/mid-path interference rather than padded coupling or
terminal-only supervision. Reviewer 226 keeps Gate B and Gate C closed and
opens Brief 184 for one bounded 50-state full-path self-consistency correction.
No optimizer, training, mutation, rollout, hardware, external compute, or Brev
action occurred.

## 2026-07-15 - Brief 184 opens T20.35r full-path correction

T20.35r binds the exact T20.35p checkpoint and all 50 finite T20.35q
self-generated pre-update states and times. The planned signed spec freezes a
balanced 500-update expert-only correction at `2.5e-5`, exact state/velocity
reconstruction, unchanged standard-objective and 0.05-rad Gate B checks, and
one-use local-MPS semantics. Model load, optimizer creation, training, rollout,
Gate C, hardware, external compute, and Brev remain prohibited until a fresh
pre-run review is remotely preserved.

## 2026-07-15 - T20.35r full-path pre-run boundary accepted

Implementation `bac3877` plus wrapper normalization `ef90668`, spec
`70be21a2...`, and central authority `f4ef827b...` bind the exact T20.35p
checkpoint, all 50 signed T20.35q path states, exact reconstruction hashes and
tolerances, a balanced 10-use-per-example schedule, 500 constant-LR
expert-only updates, complete optimizer settings, and the five-seed
active-zero/padded-normal evaluation. Gate B retains the original
standard-objective baseline and 0.05-rad action gate. Reviewer 227 authorizes
exactly one Python 3.12 local-MPS attempt after remote preservation. Fifty-seven
relevant tests pass. No T20.35r model, checkpoint tensor, inference, optimizer,
training, rollout, Gate C, hardware, external compute, or Brev action occurred
at this boundary.

## 2026-07-15 - T20.35r full-path correction verified negative

The sole attempt `fbcc16a5...` completed 500 finite updates and produced run
`85826156...`, checkpoint `b73123dc...`, and signed result `52d4c9ed...`,
preserved at `c8f75a0`. Correction objective ratio passes at `0.095317`, but
the standard objective increases `3.23704x` from the source checkpoint and
fails its original-baseline gate at `0.150468`. All decoded chunks fail 0.05
rad with maxima `0.114470–0.197005`. Baseline objective values show steps 8–9
holding `90.2746%` of correction mass despite count-balanced sampling, but
Reviewer 228 requires a model-free audit before attributing causality. Gate B
and Gate C remain closed. No retry, rollout, hardware, external compute, or
Brev action occurred.

## 2026-07-15 - Brief 185 opens T20.35s objective-mass audit

T20.35s binds the exact T20.35r run/result and recomputes objective mass by
step and seed, individual improvement counts, standard-objective regression,
and unchanged Gate B ratios without loading a model. It may route one
time-normalized compatibility hypothesis but cannot select an action
correction or grant optimizer, Gate C, hardware, external-compute, or Brev
authority.

## 2026-07-15 - T20.35s objective-mass interference verified

Signed audit `113f72a9...`, preserved at `7242e98`, recomputes all 50 T20.35r
baseline/final correction objectives. Steps 8–9 hold `90.2746%` of baseline
mass and step 9 alone `77.5851%`, while the standard objective worsens
`3.23704x` to original-baseline ratio `0.150468`. Reviewer 229 verifies
terminal objective-mass dominance with standard interference and routes
T20.35t. Thirty-three relevant tests pass. No model, checkpoint, optimizer,
rollout, hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 186 opens T20.35t balanced correction

T20.35t starts from the pre-regression T20.35p checkpoint, reuses all 50 exact
T20.35q path examples, normalizes each step's correction loss to equal initial
objective mass, and pairs every one of 500 correction updates with one
deterministically seeded standard one-batch replay gradient before stepping.
The original objective and 0.05-rad action gates remain unchanged. Model load,
optimizer creation, training, Gate C, hardware, external compute, and Brev stay
closed pending a fresh remotely preserved pre-run review.

## 2026-07-15 - T20.35t balanced pre-run boundary accepted

Implementation `545a563`, spec `34881e21...`, and central authority
`8387945b...` bind the exact T20.35p checkpoint, all 50 T20.35q states,
T20.35s-derived time weights, 500 unique standard-replay seeds, a 10-use-per-
example schedule, complete optimizer settings, and the unchanged five-seed
Gate B evaluation. Reviewer 230 authorizes exactly one Python 3.12 local-MPS
attempt after remote preservation. Fifty-four relevant tests pass. No T20.35t
model, checkpoint tensor, inference, optimizer, training, rollout, Gate C,
hardware, external compute, or Brev action occurred at this boundary.

## 2026-07-15 - T20.35t balanced correction verified action-only negative

The sole attempt `1a94b476...` completed 500 finite paired updates and produced
run `b5da8ab3...`, checkpoint `aeef380b...`, and signed result `f63ee934...`,
preserved at `41238de`. Raw correction and original-baseline standard-objective
ratios pass at `0.051751` and `0.006245`. All five decoded means improve over
T20.35p, but every chunk still fails 0.05 rad with maximum errors
`0.084388-0.162008`. Reviewer 231 verifies a controlled action-only negative.
Gate B and Gate C remain closed. No retry, rollout, hardware, external
compute, or Brev action occurred.

## 2026-07-15 - Brief 187 opens T20.35u balanced path audit

T20.35u binds the exact T20.35t run, checkpoint, result, five seeds, and ten
denoise steps. It will reproduce all five endpoint hashes and compare every
intermediate active/padded state against the deterministic target and the
pre-correction T20.35p source paths. This is a one-use inference-only audit;
optimizer creation, training, rollout, Gate C, hardware, external compute,
and Brev remain closed pending a fresh remotely preserved pre-run review.

## 2026-07-15 - T20.35u balanced path pre-run boundary accepted

Implementation `5c99e79`, spec `2575861c...`, and permit `bda88c46...` bind
the exact T20.35q source paths, T20.35t run/checkpoint/result, all five
base-noise/source/new endpoint hashes, ten-step time grid, targets, processor,
and sampler. Reviewer 232 authorizes exactly one Python 3.12 local-MPS
inference-only audit after remote preservation. Nineteen relevant tests, exact
spec verification, and the Python 3.12 model-free preflight pass. No T20.35u
checkpoint tensor access, model construction, inference, optimizer, rollout,
Gate C, hardware, external compute, or Brev action occurred at this boundary.

## 2026-07-15 - T20.35u consumed by pre-model dependency failure

Attempt `179092b9...` was consumed once, then LeRobot dataset import failed
because the isolated Python 3.12 runtime lacked `datasets`. No checkpoint tensor
was read, no model was constructed, no inference ran, and no result exists.
The T20.35t checkpoint remains `aeef380b...`. Signed failure `0abd9650...` is
preserved at `5700fb0`. Reviewer 233 forbids retry or attempt deletion and
routes distinct T20.35v behind an exact dependency-complete no-attempt runtime
preflight. Gate B and Gate C remain closed; no optimizer, rollout, hardware,
external compute, or Brev action occurred.

## 2026-07-15 - Brief 188 opens T20.35v dependency-complete path audit

T20.35v will rebind the unchanged five-path comparison under distinct spec,
permit, attempt, and result identities. Before any attempt marker, its exact
Python 3.12 command environment must import every dataset/model/checkpoint
dependency and prove MPS plus the immutable checkpoint tree. Design and tests
only are open; inference, optimizer, rollout, Gate C, hardware, external
compute, and Brev remain closed pending a fresh remotely preserved review.

## 2026-07-15 - T20.35v runtime-complete pre-run boundary accepted

Implementation `d1861f3`, spec `a0b5c211...`, permit `304b956b...`, and signed
runtime preflight `59ecc86c...` are remotely preserved. The exact Python 3.12
environment imports LeRobot 0.6.1 `dataset,pi`, datasets 4.8.5, pyarrow 25.0.0,
torch 2.11.0, safetensors 0.8.0, and transformers 5.5.4 with MPS available.
Before creating a V marker, the normal path repeats all imports and requires
exact version equality. Reviewer 234 authorizes one distinct inference-only
attempt. Twenty-three relevant tests and all signed/model-free/runtime checks
pass. No V attempt, checkpoint tensor load, model, inference, optimizer,
rollout, Gate C, hardware, external compute, or Brev action occurred.

## 2026-07-15 - T20.35v active early/mid path interference verified

Distinct attempt `30df1e26...` reproduced all five T20.35t endpoint hashes and
emitted result `aad8a148...`, preserved at `d464e26`. Active target residual
improves through steps 0-2, then first worsens materially at step 3. Source-path
state displacement is material at step 1 and grows to `0.070391` active versus
`0.019197` padded. Reviewer 235 verifies active-dimension early/mid path
interference and routes one model-free decoded-action outlier audit. Gate B and
Gate C remain closed; no retry, optimizer, rollout, hardware, external compute,
or Brev action occurred.

## 2026-07-15 - Brief 189 opens T20.35w action outlier audit

T20.35w binds the exact five decoded chunks, 50-by-6 target, normalized target,
and final path states to localize error by seed, action index, and joint under
the unchanged 0.05-rad threshold. It is model-free and may route one smallest
correction hypothesis. Model/checkpoint access, inference, optimizer, rollout,
Gate C, hardware, external compute, and Brev remain closed.

## 2026-07-15 - T20.35w physical-gate joint dominance verified

Signed audit `e52d6d08...`, preserved at `99cbbc4`, recomputes all 1,500
decoded action errors. 370 exceed 0.05 rad. Shoulder lift carries `50.6574%`
of physical squared error and wrist roll `29.3595%`, while no last-captured
normalized joint or ten-action band reaches 50%. Reviewer 236 verifies a
physical-gate/normalization weighting mismatch and routes T20.35x. Twenty-seven
relevant tests pass. No model, checkpoint, inference, optimizer, rollout,
hardware, external compute, or Brev action occurred.

## 2026-07-15 - Brief 190 opens T20.35x physical-gate correction

T20.35x starts from the exact T checkpoint, uses all 50 current V path states,
derives active-joint weights from physical-radian normalizer Jacobians, then
equalizes time-step objective mass and pairs every correction gradient with
deterministic standard replay. The original Gate B thresholds remain unchanged.
Model/checkpoint access, optimizer, training, Gate C, hardware, external
compute, and Brev stay closed pending implementation, authority composition,
runtime preflight, and a fresh remotely preserved review.

## 2026-07-15 - Reviewer 237 authorizes one T20.35x attempt

Commits `1c0fc1a` and `ff36b1b` preserve the 50-state joint/time-weighted
correction, exact spec `96efc6d3...`, training-only authority `a3a4eee7...`,
runtime proof `292a5b10...`, and one-use permit `c497dbed...`. Twenty-two
lineage tests pass. The normal runner rejects PyArrow 24 before attempt
creation and passes on the reviewed PyArrow 25 surface. Exactly one local-MPS
attempt is authorized. Gate C, hardware, physical transfer, promotion,
external compute, and Brev remain closed.

## 2026-07-15 - T20.35x passes Gate B and opens T20.36 design

One consumed local-MPS attempt completed 500 finite paired updates and emitted
signed result `e79dacff...`, preserved at `afa421d`. The unchanged standard
objective is `0.00252212` of the original baseline, and all five decoded action
chunks pass the 0.05-rad gate with worst error `0.04478485`. The two weighted
correction ratios pass; raw unweighted correction remains above its auxiliary
target at `0.319203`. Reviewer 238 verifies the mechanical Gate B conjunction
and opens Brief 191 for T20.36 design and tests only. Gate C, further model or
optimizer work, rollout, policy acceptance, hardware, external compute, and
Brev remain closed pending a fresh remotely preserved pre-run review.

## 2026-07-15 - Reviewer 239 authorizes one T20.36 campaign

Commits `8da3cae` and `18f81e7` preserve spec `522a1e5a...`, central
training-only authority `25e63103...`, dependency/render/disk proof
`04f2ce56...`, and one-use permit `68d9042d...`. Thirty-two relevant tests
pass. The runner binds 500 unique official coverage samples, one X correction
per update, unchanged processor and Gate B, seed-0-before-held-out stop rules,
complete signed traces, and automatic content-addressed mirror MP4s. Runtime
preflight records 23.13 GB free against a repeated 6-GiB minimum and a real
one-frame render. Exactly one local-MPS attempt is authorized. No T20.36
attempt, model, optimizer, rollout, hardware, external compute, or Brev action
has occurred.

## 2026-07-15 - T20.36 regresses Gate B and stops before Gate C

The sole authorized local-MPS attempt completed 500 finite paired updates and
emitted signed result `02b543be...`, remotely preserved at `3e1f2bd`. The
unchanged standard-objective ratio passes at `0.0305642`, but every decoded
chunk misses 0.05 rad with maximum errors from `0.150601` to `0.187035` rad.
The joint-weighted correction objective improves from `0.00260035` to
`0.00133429` while the raw correction objective worsens from `0.0252181` to
`0.0389846`. Gate B is therefore not retained. The runner reaches no rollout
seed, creates no mirror, and keeps Gate C, held-out evaluation, policy
acceptance, hardware, external compute, and Brev closed. Reviewer 240 verifies
the negative boundary. Brief 192 opens T20.36a as an optimizer-free audit of
the existing signed objective histories and gate outcomes; no second campaign
or gate change is authorized.

## 2026-07-15 - T20.36a proves weighted correction is not Gate-B-equivalent

Signed audit `339a7229...`, remotely preserved at `3bbdc64`, verifies all X
and T20.36 artifact identities and 500 recorded update rows without reading a
checkpoint or loading a model. Relative to X, T20.36's standard objective is
`12.118449` times worse, its raw correction objective is `1.545902` times
worse, and its worst decoded error is `4.176295` times worse; every seed
regresses. Yet the joint-weighted correction objective improves to `0.513119`
of X. Coverage loss holds 97.23%-99.07% of recorded scalar objective mass per
25-update window, and 420/500 combined gradients exceed the 1.0 pre-clip
threshold. This proves the weighted mean was not a physical-maximum retention
guard in this campaign; it does not claim gradient-level causality. Reviewer
241 routes Brief 193 to a pure Gate B retention decision contract before any
new training proposal. No model, optimizer, rollout, gate change, hardware,
external compute, or Brev action is authorized.

## 2026-07-15 - T20.36b retains only X and rejects a coverage candidate

Pure contract spec `6e56f6ff...` and historical-fixture decision
`e709c30c...`, remotely preserved at `5fdc36c`, encode the unchanged 0.10
standard ratio plus five exact-seed 0.05-rad maxima. Proxy metrics are reported
but cannot participate. X is the sole retained checkpoint and is labelled only
as rollback capability. T20.36 is rejected; no post-source coverage candidate
or Gate C authority exists. The fixture explicitly does not claim its schedule
was pre-registered. Any future schedule must be remotely preserved before
optimizer creation and separately authorized. Reviewer 242 routes Brief 194 to
a read-only local ACT/SmolVLA capability preflight; no download, checkpoint
read, model, optimizer, policy selection, hardware, external compute, or Brev
action is authorized.

## 2026-07-15 - T20.36c routes exact ACT control design before SmolVLA

Signed preflight `61fcf124...`, remotely preserved at `139fe32`, binds the
exact local LeRobot source, canonical 10-episode/2,330-frame dataset metadata,
and local cache inventory without reading a checkpoint tensor. ACT has prior
100-update MPS evidence and the canonical six-joint/two-camera shape is usable,
but the cached ACT candidate expects different camera keys, resolution, and a
100-step chunk, so it is not a drop-in control. SmolVLA's base and VLM cache
metadata is complete and its six-joint/50-step horizon matches, but its cached
processor expects three cameras and no SmolVLA MPS runtime has been proven.
Twenty-three relevant tests pass, including a guarded tensor-read abort and
cache-alias rejection. Reviewer 243 verifies metadata readiness only and opens
Brief 195 to design the exact ACT Gate B control. No policy is selected and no
network, tensor read, model, inference, optimizer, rollout, gate change,
hardware, external compute, or Brev action occurred.

## 2026-07-15 - T20.36d exact ACT control design verified

Signed spec `45c90dc0...`, remotely preserved at `b8b19cd`, binds episode 0
frame 0 and its measured horizon-50 target to the canonical T20.23 dataset and
its 2,330-frame MEAN_STD state/action statistics. The future control uses a
fresh compact ACT with no pretrained backbone or cached checkpoint, one fixed
MPS batch, a 2,000-update ceiling, and evaluations at updates 0, 100, 250, 500,
1,000, and 2,000. Five deterministic action hashes must agree, and the
unchanged 0.05-rad physical maximum plus 0.10 supervised-objective ratio must
both pass. The first passing post-baseline checkpoint stops the sole run. A
pass exonerates only the shared one-batch/statistics/round-trip path; a fail
does not prove a dataset fault without separating ACT implementation and
optimization. Reviewer 244 routes Brief 196 to pre-run implementation only.
No attempt marker, model, optimizer, run, policy selection, gate change,
hardware, external compute, or Brev action occurred.

## 2026-07-15 - T20.36e exact ACT control pre-run verified

Implementation `0f0caa7` is remotely preserved. The signed central decision
`9c2a16d2...` grants only `simulation_training_ready`; model-free runtime
preflight `d29b93e7...` binds Python 3.12, pinned LeRobot/Torch dependencies,
MPS, 20.12 GiB free, remote source `0f0caa7`, two exact image tensor hashes,
physical action hash `5698babc...`, physical state hash `efd37887...`, source
errors below `7.11e-8` rad, and round-trip error `2.22e-16` rad. One-use permit
`75f5e163...` fixes the 0/100/250/500/1,000/2,000 schedule, first-pass stop,
and no retry. Rehearsal corrected unsupported ACTConfig arguments and the
horizon-action batch dimension before any model existed; explicit collation
produces the expected `(1,50,6)` action and `(1,50)` pad tensors. Thirty-five
T20.36 regressions pass. Reviewer 245 opens exactly one local-MPS attempt after
this evidence boundary is on origin. The attempt marker is absent; no model,
inference, optimizer, checkpoint tensor read, network, policy selection,
SmolVLA entry, Gate B change, Gate C, rollout, hardware, external compute, or
Brev action occurred.

## 2026-07-15 - T20.36e ACT control passes objective but fails physical maximum

The only permitted ACT attempt completed 2,000 finite local-MPS updates and
signed result `2ea2c246...` from run `9911e51c...`. The supervised objective
fell from `1.385815` to `0.0761061`, a passing `0.054918` ratio. All five final
decoded action hashes are the same (`ecaa2e4c...`) and mean physical error is
`0.0145525` rad, but maximum physical error is `0.442487` rad, so Gate B fails
its unchanged all-element 0.05-rad conjunct. The compact ACT checkpoint is
content-addressed as `01b57134...`; its safe tensor is 45,251,096 bytes. The
result does not prove a shared dataset fault or exonerate PI0.5: the run summary
does not expose which joint/time owns the isolated maximum, and pre-clip
gradient norms reached `320.081`. Reviewer 246 closes retries and routes Brief
197 to an exact checkpoint-reload, direct-versus-queue, normalized-versus-
physical, per-joint/time audit under a separately preserved inference boundary.
No policy is selected; SmolVLA entry, Gate B amendment, Gate C, rollout,
hardware, external compute, and Brev remain closed.

## 2026-07-15 - T20.36f decode localization pre-run verified

Implementation `489be59` is remotely preserved and 41 T20.36 regressions pass.
Central decision `de30947f...`, model-free preflight `40e24b5e...`, and one-use
permit `d9daae7b...` bind checkpoint `01b57134...`, its exact 1,684-byte config
and 45,251,096-byte safe tensor, the pinned local MPS stack, dependency versions,
source result/run/evaluation/action hashes, and remote source commit. The
preflight hashes checkpoint bytes but does not parse tensors. Reviewer 247 opens
one checkpoint load plus deterministic inference only after this boundary is
on origin. No model load, checkpoint tensor read, inference, optimizer, retry,
policy selection, SmolVLA entry, gate change, Gate C, rollout, hardware,
external compute, or Brev action occurred.

## 2026-07-15 - T20.36f localizes sparse ACT boundary underfit

Inference-only result `472e5ec5...` reproduces objective `0.0761061`, all five
queued action hashes `ecaa2e4c...`, and the same direct hash; direct-versus-
queue physical error is exactly zero. The error exists in normalized ACT output
before postprocessing: timestep-0 normalized maxima are `2.64747` on wrist flex
and `2.44484` on wrist roll, decoding to `0.366316` and `0.442487` rad. Shoulder
lift reaches `0.125317` rad at timestep 0, while gripper reaches `0.241636` rad
at timestep 49. Fourteen elements exceed 0.05 rad: 9 in steps 0-9, 1 in steps
30-39, and 4 in steps 40-49. Thus the shared dataset/statistics/coordinate and
ACT direct/queue paths reproduce faithfully; the miss is sparse boundary/
endpoint model underfit, not a decode or unit-scaling artifact. Reviewer 248
closes ACT retry and routes Brief 198 to design SmolVLA's exact Gate B entry.
Gate B remains unchanged because task-relevant shoulder and gripper errors are
among the failures. No optimizer, policy selection, SmolVLA model load, Gate C,
rollout, hardware, external compute, or Brev is authorized.

## 2026-07-15 - T20.36g exact SmolVLA Gate B entry design verified

Spec `fb217f3e...` and implementation `1c5faf3` bind the exact local policy and
VLM snapshots, pinned SmolVLA plus shared processor/checkpoint source files,
canonical episode-0 two-camera batch, T20.23 statistics, and physical round
trip. The cached third-camera expectation is replaced before construction;
empty, duplicate, synthetic, aliased, and silently dropped cameras are
forbidden. Pretrained expert-only plus state projection is the sole trainable
scope. The future runtime must remain offline and MPS-only, inventory dtype,
device, buffers, and trainable parameters, pass finite forward/backward smoke,
then follow one constant-`1e-4` 2,000-update schedule with the unchanged Gate B.
Forty-seven T20.36 tests pass. Reviewer 249 verifies design only and opens
Brief 199 for pre-run implementation and central authority. No attempt, tensor
deserialization, model, inference, optimizer, policy selection, Gate C,
hardware, network, external compute, or Brev action occurred.

## 2026-07-15 - T20.36h exact SmolVLA pre-run authorized

Implementation `29b9525`, central decision `b6b88518...`, static preflight
`b7e2938f...`, and one-use permit `5fa7c1d2...` agree. Raw-byte SHA-256 binds
the policy checkpoint (`7cd549ac...`), identical policy pre/post normalization
tensors (`490ab239...`), and VLM checkpoint (`b9bfd456...`) without safetensor
deserialization. The exact source equals origin, scoped paths are clean, the
canonical two-camera batch reproduces, MPS is available, and 17.0 GB free disk
exceeds the floor. The runner writes its attempt marker before model import,
forbids CPU/network fallback, verifies the complete expert/projection trainable
scope, signs consumed-attempt failures, and freezes the unchanged Gate B plus
one 2,000-update ceiling. Fifty-six T20.36 tests pass. Reviewer 250 authorizes
exactly one local attempt after this boundary is confirmed on origin. No model,
inference, optimizer, Gate C, hardware, external compute, or Brev action has
occurred.

## 2026-07-15 - T20.36h consumed on missing SmolVLA dependency

The one-use attempt marker `43c2d0a1...` preceded model import. Exact local VLM
construction reached AutoProcessor and stopped because `num2words` is absent.
Signed failure `56415b28...` and tracked result `3804eff6...` record zero
optimizer updates, no policy checkpoint load, no inference, no Gate B
evaluation, and no retry. Read-only metadata localization proves the pinned
LeRobot `smolvla` extra directly requires `num2words>=0.5.14,<0.6.0` and
delegates to `accelerate>=1.14.0,<2.0.0`; both distributions are absent from the
consumed Python 3.12 environment. Reviewer 251 verifies a preflight dependency-
closure defect rather than policy failure and opens Brief 200 for an offline
exact dependency audit/correction design. Installation, replacement model
access, Gate C, hardware, external compute, and Brev remain closed.

## 2026-07-15 - T20.36i exact SmolVLA dependency closure verified

Audit `0804fd4f...` recursively expands the pinned `smolvla` extra through
`transformers-dep` and `accelerate-dep` and cross-checks installed metadata.
LeRobot 0.6.1 and Transformers 5.5.4 pass; `num2words>=0.5.14,<0.6.0` and
`accelerate>=1.14.0,<2.0.0` are missing. Thus the observed error was declared
and predictable, while Accelerate was a second hidden prerequisite. The signed
correction requires complete version closure and an offline AutoProcessor smoke
before any future marker; full policy construction remains counted after the
marker. Fifty-nine T20.36 tests pass. Reviewer 252 verifies the audit without
installation or model access and blocks T20.36j pending new owner authority for
bounded environment mutation and at most one replacement local-MPS attempt.

## 2026-07-15 - T20.36j-A offline cache resolution verified

Offline resolution `8dec69ae...` evaluates the exact existing Python 3.12 venv
against the missing SmolVLA requirements with network disabled and no install.
The 28-package closure reuses 24 installed distributions and proposes exactly
Accelerate 1.14.0, docopt 0.6.2, num2words 0.5.14, and psutil 7.2.2. All four
are already in the local uv cache; manifest `6cc7235c...` binds metadata,
content trees, and the built docopt wheel, so network acquisition is not
needed. Sixty-three T20.36 tests pass after an adversarial duplicate/alias
verifier hardening. Reviewer 253 verifies the read-only audit and keeps package
installation, environment mutation, AutoProcessor/model access, and a
replacement attempt blocked pending an exact owner decision.

## 2026-07-15 - T20.36j-B corrected replacement preflight verified

Contract `cb018b69...` binds the unchanged SmolVLA spec, consumed failure,
recursive closure audit, exact four-package offline resolution, and cache
manifest. Its reusable validator independently reconstructs active
`Requires-Dist` edges and version bounds from signed distribution metadata.
The processor evidence contract requires the exact local VLM snapshot,
`local_files_only`, offline flags, zero network, and zero weight/tensor reads.
The only accepted order is closure, processor smoke, attempt marker, then full
counted policy construction. Sixty-nine T20.36 and 12 pointer tests pass after
adversarial hardening for evidence spoofing, aliasing, and authority language.
Reviewer 254 verifies the model-free implementation while withholding install,
live processor/model access, permit, marker, and replacement authority.

## 2026-07-16 - Owner authorizes T20.36j corrected replacement

The owner explicitly said "Proceed. I authorize all of this" and then
"proceed," resolving Reviewer 254's human authority blocker. Brief 203 opens an
eight-hour simulation-only window for exactly four cached offline packages,
live execution of corrected preflight contract `cb018b69...`, and at most one
local-MPS replacement attempt under unchanged Gate B. Implementation, tests,
central composition, signed preflight, remote preservation, and a fresh
one-use permit must agree before any marker. Network, extra packages, retry,
sweep, Gate B amendment, Gate C execution before a pass, hardware, external
compute, and Brev remain closed.

## 2026-07-16 - T20.36j implementation and central authority remotely verified

Implementation `b35acd182ca6520aa762f9adc11ab3cce1800422` is preserved on
`origin/codex/pi05-autolearn-loop`. Fresh central decision `aa0992e6...` grants
only `simulation_training_ready` inside the owner window and binds corrected
contract `cb018b69...`, cache manifest `6cc7235c...`, the exact four-package
offline install, one attempt, 2,000 updates maximum, and unchanged Gate B.
The new runtime path is isolated from consumed T20.36h, rejects network and
processor tensor reads, binds the complete recursive installed closure, and
reuses the frozen T20.36h evaluator so 0.10/0.05 cannot drift. Seventy-six
T20.36 tests and 12 pointer tests pass. Reviewer 255 permits the exact cached
offline installation and corrected preflight now. No attempt marker may exist
until the resulting closure, processor smoke, preflight, and one-use permit are
committed, pushed, and confirmed on origin.

## 2026-07-16 - T20.36j offline correction complete; metadata collector corrected

Offline uv resolution reverified cache result `8dec69ae...`, observed all four
authorized packages absent, and installed exactly Accelerate 1.14.0, docopt
0.6.2, num2words 0.5.14, and psutil 7.2.2 with offline/no-download flags. The
first corrected-preflight call stopped before AutoProcessor because editable
LeRobot exposes a second `egg-info/PKG-INFO` distribution alongside
`dist-info/METADATA`. Both files have SHA-256 `ceb9917f...`; no preflight or
attempt artifact was written. Correction `9e9272c` accepts either standard
metadata filename and accepts duplicates only when version, metadata hash, and
dependency rows agree. Live closure `ac8abed1...` now covers 57 active packages
with no missing or mismatched requirement. Seventy post-install applicable
T20.36 tests and 12 pointer tests pass; the two excluded historical audit tests
correctly assert the pre-install missing-package state. Reviewer 256 authorizes
one corrected preflight retry, still before any marker.

## 2026-07-16 - T20.36j processor symlink evidence guard corrected

The second uncounted preflight constructed AutoProcessor offline, with no
network or tensor guard firing, but rejected empty opened-file evidence because
Hugging Face resolved snapshot symlinks into its blob store before opening.
No preflight/permit/marker artifact was written. Correction `54339c2` maps every
resolved blob target back to its snapshot-relative path before construction and
applies the same weight/tensor denial to both spellings. A real guarded smoke
now signs `3f9a4a0c...`, classes `SmolVLMProcessor`, `GPT2Tokenizer`, and
`SmolVLMImageProcessorPil`, plus six safe config/tokenizer files; no weights or
network are observed. Six focused tests, 71 applicable post-install T20.36
tests, and 12 pointer tests pass. Reviewer 257 authorizes the corrected
preflight retry; no attempt marker exists.

## 2026-07-16 - T20.36j lexical snapshot identity corrected

The third uncounted preflight passed recursive closure, offline processor
construction, network/tensor guards, batch load, and checkpoint hashing, then
failed linkage because resolving the owner/spec path under offloaded
`~/.cache` changed it to `/Volumes/cerebro/...`. No artifact or marker was
written. Correction `ad051d0` preserves the exact lexical contract path in
signed evidence while using physical resolution only for access-control target
mapping. Real processor evidence `5223d8f0...` now verifies directly against
contract `cb018b69...`, with the same six safe files and no network/weights.
Seven focused tests, 72 applicable post-install T20.36 tests, and 12 pointer
tests pass. Reviewer 258 authorizes the corrected preflight retry; no marker
exists.

## 2026-07-16 - T20.36j corrected preflight and one-use permit verified

The complete pre-marker run persisted closure `ac8abed1...` over 57 packages,
environment manifest `3f645a25...`, processor smoke `5223d8f0...`, corrected
preflight `3c9b5af9...`, and one-use permit `effa3b65...`. Artifact commit
`a19d48d` is confirmed on origin. Independent reconstruction matches the live
LeRobot stack, canonical batch, and raw checkpoint hashes. The preflight binds
source/origin `ad3d89c`, records closure and processor stages complete, and
leaves marker/model stages false. The permit imports the frozen T20.36h
evaluator, schedule 0/100/250/500/1000/2000, maximum 2,000 updates, objective
ratio 0.10, maximum physical error 0.05 rad, no retry/sweep, and no Gate C
authority. Reviewer 259 authorizes exactly one local-MPS counted replacement;
the first marker consumes it even on runtime failure.

## 2026-07-16 - T20.36j sole SmolVLA replacement verified negative

The one-use marker `ceea58cf...` consumed permit `effa3b65...` at source
`98755da`. Local VLM and policy construction, MPS forward/backward smoke, 2,000
finite AdamW updates, six scheduled evaluations, and an 865M selected checkpoint
completed without network, fallback, external compute, or runtime failure. All
five final seed repeats are bit-identical with zero repeat delta. Final
objective ratio `0.0228663` passes 0.10, while per-seed maximum errors range
from `0.145330` to `0.266024` rad and all fail 0.05. Signed run `7e7304c5...`,
checkpoint `32f0bd30...`, and result `08ef923d...` verify; result commit
`73674a4` is on origin. Reviewer 260 closes the SmolVLA replacement alphabet.
No ACT/SmolVLA retry or Gate C follows. Because the owner pre-authorized the
post-failure amendment path before this result existed, Brief 204 opens
T20.36k: model-free task-consequence calibration using existing evidence,
strict uniform error retained as report-only, and Gate C one-episode behavior
as the eventual arbiter.

## 2026-07-16 - T20.36k model-free consequence calibration verified

Canonical seed-0 action replay passes every strict-v2, contact, safety,
release, retreat, projection, and assistance gate. Result `a3b39178...` binds
252 candidate-independent symmetric perturbation pairs across six joints,
seven exhaustive phase groups, and magnitudes 0.01 through 0.4 rad. Exactly
202 pairs pass and 50 fail; all 42 phase/joint rows are monotonic. Wrist roll
is insensitive through 0.4 rad in every phase, shoulder lift reaches a
0.025-rad ceiling during lift, and gripper reaches 0.01 rad during lift, hold,
and lower. Implementation `fbdb0aa` is on origin. Reviewer 261 verifies the
non-authorizing design: Gate B remains unchanged, strict uniform 0.05 rad stays
visible, and no model, optimizer, Gate C, hardware, external compute, or Brev
action occurred. Brief 205 opens only the frozen amendment and retained-tensor
scoring path.

## 2026-07-16 - T20.36l frozen amendment scores retained evidence fail-closed

Owner decision `32d7e193...` freezes reach/grasp phase-joint thresholds in
gate `463477dc...` before any retained candidate score. Result `0f8ae393...`
uses T20.36f witnesses to prove ACT false at shoulder lift t0, wrist roll t0,
and gripper t49. SmolVLA's objective and deterministic hashes pass, but the
retained run contains no standalone or embedded 50x6 decoded tensor, so its
amended result is indeterminate and fails closed. Implementation `e4c00bd` is
on origin; Reviewer 262 verifies that no checkpoint weight was read and no
model, inference, optimizer, new decode, Gate C, selection, hardware, external
compute, or Brev action occurred. Proposed Brief 206 requests exact new owner
authority for tensor-only reproduction and grants nothing itself.

## 2026-07-14 - Brief 163 owner continuation opens T20.32 divergence localization

The owner opened a fresh simulation-only window (20:10 CDT through hard
closeout 04:10 CDT, no new major slice after 03:25) for T20.32: complete
requested/applied/state trace capture for the frozen T20.24 and T20.31
adapters, earliest-divergence localization against the exact source
trajectories on held-out seeds 6-7, and one bounded training-seed closed-loop
reproduction probe per adapter as capability-ladder Gate C evidence. The same
continuation records the plan refresh: the policy capability ladder A-F, the
twin-uncertainty versus episode-variation grid split, the WCW-1
calibration-witness consumption path, and observable-evaluator qualification
before any canary planning. No optimizer, hardware, camera, Robo Scan
artifact, external-compute, or Brev authority is granted.

## 2026-07-14 - Brief 163 T20.32 divergence localization verified

Six signed 244-frame traces compare T20.24 and T20.31 against exact source
trajectories on training seed 0 and held-out seeds 6-7. All four held-out
action hashes reproduce exactly. Both seed-0 probes fail strict grasp and
first exceed the 0.05 rad action threshold at frame zero; state divergence
follows at frame one. Result `f9b091c6...` routes T20.33 to Gate B
one-batch-memorization/model plumbing, not Gate C chunk/cadence/feedback.
Implementation `7bbf7cf` is preserved on origin; 49 relevant tests and the
workflow audit pass. No optimizer, policy acceptance, hardware, external
compute, or Brev authority follows.

## 2026-07-14 - Brief 164 opens T20.33 Gate B one-batch proof

T20.33 binds T20.17 episode 0 frame 0 and its exact horizon-50 measured-action
target as the only batch. A fresh central training-only decision must be
reviewed, committed, pushed, and current before one fixed 500-update local-MPS
run. Five fixed-seed decoded chunks must each stay within 0.05 rad maximum
source-action error and the five-seed final objective must be at most 10% of
baseline for Gate B to pass. There is no retry, sweep, Gate C correction,
closed-loop rollout, hardware, external compute, or Brev authority.

## 2026-07-14 - Reviewer 194 authorizes the one T20.33 run

Implementation `38fa450`, training spec `3fa3098c...`, and central decision
`ff3ac3c9...` are remotely preserved and recompose exactly. Forty-six relevant
tests pass. The one fixed 500-update local-MPS run may now load the model and
optimizer while the authority is current. No retry, second batch, Gate C
change, closed-loop rollout, policy acceptance, hardware, external compute,
or Brev is authorized.

## 2026-07-14 - T20.33 Gate B one-batch proof verified negative

The one authorized run completed all 500 fixed-batch local-MPS updates with
finite objectives and gradients. Five-seed objective mean changed from
0.959079 to 0.506632, a 0.528248 ratio versus the 0.10 gate. All five decoded
horizon-50 chunks fail the 0.05 rad maximum-error requirement, ranging from
0.843707 to 1.250647 rad. Result `27cd2be3...` and run `718a1c7c...` are bound
by artifact commit `bb3435b` on origin. Gate B remains unmet; no retry, Gate C
work, policy acceptance, hardware, external compute, or Brev is authorized.

## 2026-07-14 - Brief 165 opens T20.34 Gate B plumbing localization

T20.34 loads the pinned base and saved T20.33 adapter without gradients and
decodes the same exact batch under the same five seeds. It must reproduce the
adapter hashes exactly, prove whether LoRA tensors are active, and measure
whether adapter movement aligns with target-minus-base action direction. One
signed report routes dead/misbound adapter plumbing, objective-to-inference
misalignment, or insufficient optimization/capacity. No optimizer, second
batch, Gate C work, hardware, external compute, or Brev is authorized.

## 2026-07-14 - T20.34 Gate B plumbing localization verified

The saved adapter contains 321,688 nonzero values, reproduces all five T20.33
decoded hashes exactly, and reproduces the objective change from 0.959079 to
0.506632. Against the base, every seed improves mean decoded error by
0.0553-0.0826 rad and has positive target-direction cosine 0.456-0.856.
Result `8026980d...` and implementation `491eb6c` are preserved on origin.
Dead/misbound adapter plumbing and objective-to-inference opposition are
rejected; insufficient rank-4 optimization/capacity remains. No Gate B pass,
optimizer, Gate C work, policy acceptance, hardware, external compute, or
Brev authority follows.

## 2026-07-14 - Brief 166 opens T20.35 rank-capacity discriminator

T20.35 changes only LoRA rank/alpha from 4 to 16 while keeping the exact
T20.33 batch, base, processors, learning rate, 500 updates, seeds, and Gate B
thresholds. A fresh central training-only decision and remotely preserved
pre-run review are mandatory. One run is allowed; there is no rank sweep,
continuation, second batch, Gate C work, hardware, external compute, or Brev.

## 2026-07-14 - Brief 160 quantile-postprocessor counterfactual opened

T20.29 inverts each candidate's own q01/q99 action decode and cross-decodes the
same normalized output under the other dataset's quantiles over five paired
seeds. It runs no model or optimizer and creates no policy-acceptance, transfer,
promotion, hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 161 nominal-action-quantile-freezing preflight opened

T20.30 creates a derived view of the verified recovery dataset whose only
statistics change is clean nominal action q01/q99. It binds byte-identical data
and episode metadata, the same sampler seed and 500-update budget, and a fresh
central simulation-only decision. It runs no model or optimizer and grants no
policy, transfer, hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 162 nominal-action-quantile ablation opened

T20.31 consumes only the exact T20.30 central simulation-training decision for
500 same-seed local-MPS updates and frozen unassisted evaluation on seeds 6 and
7. It may record candidate behavior but grants no policy acceptance, transfer,
promotion, hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 162 nominal-action-quantile ablation verified negative

Official LeRobot completed exactly 500 finite local-MPS updates with loss
1.544 -> 0.413 and minimum 0.020. The checkpoint action q01/q99 match T20.30.
Frozen unassisted seeds 6 and 7 each ran 244 frames with distinct action hashes,
zero projected/assisted frames, no strict contact, and only 1.44e-7 / 1.43e-7 m
lift. Reviewer Decision 192 records 0/2 strict successes and no policy,
transfer, promotion, hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 161 nominal-action-quantile-freezing preflight verified

The distinct persistent dataset contains the same five files, 10 episodes, and
2,330 frames as T20.23. Every non-statistics byte matches; only
`meta/stats.json` differs, and its only semantic changes are action q01/q99 from
the clean nominal dataset. Central decision `1d615e13...` grants exactly
`simulation_training_ready`. Reviewer Decision 191 records no model load,
optimizer, rollout, policy acceptance, hardware, external compute, or Brev.

## 2026-07-14 - Brief 160 quantile-postprocessor counterfactual verified

Cross-decoding the five clean normalized outputs with recovery action quantiles
raises source-action MAE by 0.11301 rad, closely accounting for the observed
0.11094 rad recovery regression with a -0.00208 rad residual. The reverse swap
improves recovery outputs by 0.11370 rad. Reviewer Decision 190 accepts only a
postprocessor-level counterfactual and selects nominal-action-quantile freezing
as a separately reviewed ablation; it grants no model, optimizer, rollout,
policy, transfer, hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 159 exact sampler-exposure audit opened

T20.28 replays the pinned official sampler for the exact clean and recovery
campaign seeds, episode boundaries, batch/world size, and update counts, then
binds every selected index to a source class and phase. It runs no model or
optimizer and creates no policy-acceptance, transfer, promotion, hardware,
external-compute, or Brev authority.

## 2026-07-14 - Brief 159 exact sampler-exposure audit verified

The exact clean order contains 14 approach and 0 frame-zero samples; recovery
contains 26 approach and 3 frame-zero samples across 314 nominal and 186
recovery positions. Reviewer Decision 189 rejects low early-phase exposure and
selects recovery-mixture quantile/postprocessor shift as the next audit.

## 2026-07-14 - Brief 158 paired multi-seed source comparison opened

T20.27 deduplicates the two exact-reproducing process batches and pairs clean
and recovery actions over one baseline plus four distinct inference seeds
against the exact source frame-zero action. It runs no model, applies no action,
and creates no optimizer, policy-acceptance, transfer, promotion, hardware,
external-compute, or Brev authority.

## 2026-07-14 - Brief 158 paired multi-seed source comparison verified

Five duplicate-free paired seeds show clean source-action MAE 0.50833 rad and
recovery MAE 0.61926 rad. Recovery regresses all 5/5 seeds by 0.11094 rad mean;
only gripper improves by 0.00120 rad while the arm regresses. Reviewer Decision
188 creates no capability or optimizer authority.

## 2026-07-14 - Brief 157 frozen frame-zero variability opened

T20.26 launches two independent local-MPS processes per frozen adapter and
samples only one identical held-out seed-6 frame-zero observation under fixed
same-seed and distinct-seed schedules. No action is applied and no rollout or
optimizer runs. The slice creates no policy-acceptance, transfer, promotion,
hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 157 frozen frame-zero variability verified

Four independent processes bind one identical frame-zero observation. Both
adapters have 0.0 rad within-process and cross-process same-seed difference;
distinct seeds span 0.18478 rad clean and 0.14797 rad recovery. Reviewer
Decision 187 treats the older clean hash as historical-runtime-specific and
requires paired multi-seed comparisons before training attribution.

## 2026-07-14 - Brief 156 frozen-candidate localization opened

T20.25 will rerun the immutable T20.17 and T20.24 adapters on held-out seeds 6
and 7, capturing every requested action and pre-action simulator state for
source-relative and candidate-relative comparison. Frame zero is isolated as
prediction error; later differences include closed-loop state drift. The slice
runs no optimizer and creates no policy-acceptance, transfer, promotion,
hardware, external-compute, or Brev authority.

## 2026-07-14 - Brief 156 frozen-candidate localization verified

Four source-bound frozen traces verify that both candidates diverge at frame
zero. Recovery regresses sampled frame-zero MAE by 0.11137 rad but improves
sampled pre-contact MAE by 0.04735 rad. Its two prior hashes reproduce exactly;
the clean seed-6 prior hash does not, even through the original evaluator with
the same stack identity. Reviewer Decision 186 therefore blocks training
attribution and selects repeated inference-variability measurement before more
optimizer work.

## 2026-07-14 - Brief 155 recovery-augmented campaign opened

T20.24 activates only the exact T20.23 campaign: clean `pi05_base`, package
quantile statistics, rank-4 LoRA, local MPS, batch size one, fixed seed, and 500
updates. Its frozen adapter must run one unassisted strict-v2 rollout on each of
seeds 6 and 7. No policy acceptance, transfer, promotion, hardware/camera,
external-compute, or Brev authority follows from opening the brief.

## 2026-07-14 - Brief 155 recovery-augmented campaign verified negative

Run 002 completed 500 finite local-MPS updates after preserving a Python-3.14
pre-optimizer launch failure as run 001. The frozen adapter then ran held-out
seeds 6 and 7 unassisted: both made zero strict contact and lifted only 0.000144
mm / 0.000143 mm. Reviewer Decision 185 verifies the 0/2 negative result. The
accepted-policy pointer remains unchanged; no transfer, promotion, hardware,
external-compute, or Brev authority was created.

## 2026-07-14 - Brief 154 recovery-augmented dataset preflight opened

T20.23 selects the next causal policy step without opening an optimizer. The
training candidate is exactly six T20.17 nominal strict-success episodes plus
four T20.18 strict-success recovery branches, totaling 10 episodes and 2,330
frames. The two near-failures and two failures remain immutable evaluation-only
diagnostics outside dataset statistics. Hardware, cameras, Robo Scan, physical
transfer, promotion, external compute, and Brev remain closed.

## 2026-07-14 - Brief 154 recovery-augmented dataset preflight verified

Implementation `fc54988` and Reviewer Decision 184 verify one actual ten-
episode, 2,330-frame LeRobotDataset: six nominal strict successes plus four
policy-visited strict-success recoveries. Seeds 6-7 and all four negative
branches remain outside training/statistics. Central composition grants only
`simulation_training_ready`; no model, inference, optimizer, rollout, hardware,
camera, external compute, or Brev was used. The next optimizer boundary requires
a separate brief and exact 500-update local-MPS campaign.

## 2026-07-14 - Brief 148 clean-base campaign verified negative

Official LeRobot completed 250 finite rank-4 local-MPS updates from the clean
base, but the frozen seed-6 candidate made no strict contact and lifted only
0.000307 mm in 244 unassisted frames. Implementation `dce1995` and Reviewer
Decision 178 record a negative result without policy acceptance. T20.18
recovery data is next; more optimizer work is not yet authorized by a brief.

## 2026-07-14 - Brief 149 policy-visited recovery episodes verified

Exact replay captured 244 T20.17 policy-visited states. Eight zero-tolerance
state forks produced four observed recoveries, two near-failures, and two
failures. A separately signed 48 MB supplement retains 1,290 child frames and
2,580 branch-rendered observations with measured, unpadded actions. Reviewer
Decision 179 verifies only this simulation recovery-data capability; T20.19 is
next.

## 2026-07-14 - Brief 150 discrete recovery ensemble verified

The fixed 12-cell one-factor grid passed 11 cells. Gripper scale 1.05 was the
sole failure: it lifted 31.849 mm but missed the full stable-hold and lower
counts. Decision 180 verifies only this uncalibrated discrete scorecard; T20.20
is next.

## 2026-07-14 - Brief 151 observer-role evaluator verified

The privileged and observable roles share eight strict-v2 predicates under
disjoint input schemas. Two complete simulator cases agree, while missing,
leaked, spoofed, camera/VLM, malformed, or undeclared evidence fails closed.
Decision 181 verifies only local evaluator-fixture conformance; no hardware
observation or physical qualification occurred. T20.21 is next.

## 2026-07-14 - Brief 152 offline paired trace runner verified

Two independently signed synthetic traces bind exact `q0`, clock, joint,
proposed/issued/measured action, and event data. The matched pair has zero error;
nine fixed cases route every mismatch category without calibration or twin
mutation. Decision 182 verifies only offline runner-fixture conformance. T20.22
is next.

## 2026-07-14 - Brief 153 offline timing certificate verified

One synthetic certificate passes every derived timing threshold. Eleven
one-factor cases route clock, age, skew, assembly, transport, hold, period,
jitter, inference, drop, and deadline failures; each blocks dynamics-error
attribution. Decision 183 verifies only offline fixture conformance. The local
T20.17-T20.22 queue is complete, while the broader MVP exit remains unmet.

## 2026-07-14 - Brief 147 source-native clean-base preflight verified

Implementation `b826e3f` and Reviewer Decision 177 verify the persistent
six-episode LeRobotDataset, frozen raw held-out seeds 6-7, package quantile
statistics, complete pinned `pi05_base` cache, and the fixed bounded campaign
contract. Central composition grants only `simulation_training_ready` and
continues to withhold physical transfer and promotion.

No model, optimizer, inference, simulator rollout, hardware, external compute,
or Brev was used. A new brief must activate the exact bounded campaign before
optimizer execution.

## 2026-07-14 - Brief 146 MVP cut and local queue verified

Implementation `81c9a25` and Reviewer Decision 176 make the accepted triage a
durable living plan. T20.17 remains the immediate clean-base dataset-native
PI0.5 campaign. T20.18-T20.22 are pending in dependency order: state-fork
recovery data, a 10-20-cell discrete ensemble, observer-role evaluation, a thin
paired trace runner, and timing/latency evidence. The reference-only Robo Scan
I2/I3 boundary is complete; I4 waits on real producer M1-M4 evidence.

No model, optimizer, simulator rollout, hardware, external compute, or Brev was
used. No physical, transfer, promotion, or policy-acceptance authority changed.
The next action is a new narrow T20.17 implementation brief.

## 2026-07-13 - Post-109 maintenance reconciliation

Commit `2f880d0` added grasp-evidence observability hardening after Brief 109:
3-5 rendered keyframes, measured-vs-threshold gate margins, explicit retirement
of the degenerate 12-sample Halton design, and approach/IK tolerance
consistency. The fourteen signed evidence artifacts were regenerated and
verified. This is maintenance reconciliation, not a new major slice: T17.4
remains pending, the latest verified implementation boundary remains Brief 109
at `76cb16d`, and no pointer advance is implied.

The regenerated T17.1 content-addressed projection is recorded in
`project_state.json` with its maintenance linkage to Session 140 and Reviewer
Decision 136. Its original Brief 107 verification is not rewritten. No
hardware, Brev, paid compute, optimizer, training, or physical motion occurred.

## 2026-07-13 - Brief 110 T17.4 start

The prior eight-hour window expired at `2026-07-13T20:30:11-05:00` and was
recorded in `run_window_history`. Owner continuation opened a fresh eight-hour
window at `2026-07-13T20:30:52-05:00`; no-new-major-slice cutoff is
`2026-07-14T03:45:52-05:00` and hard closeout is `2026-07-14T04:30:52-05:00`.

T17.4 is now `in_progress` under Brief 110. The first implementation slice is
the source-bound compiler only: deterministic frame rows, hard-boundary
segments, and explicit quarantine/compiler manifests. The current fixture's
missing per-frame action evidence must remain quarantined; no normalization,
training, optimizer, hardware, or Brev authority is opened.

## 2026-07-13 - Signed dependency reconciliation

The T17.1 maintenance refresh changed the source experience-record identity, so
the signed T17.2 processor and T17.3 normalization bundle were regenerated from
their canonical builders. Commit `f6626fa` records the processor identity
`59827b3d...` and normalization identity `dea3ff8c...`; their capabilities and
closed authority flags are unchanged. The T17.4 compiler was then rebound to
the new normalization identity. No raw bytes, hardware, Brev, training, or
optimizer work occurred.

## 2026-07-13 - Brief 110 T17.4 verification

T17.4 is verified by Reviewer Decision 138. Commit `1a37466` is pushed to the
allowed remote branch and contains the deterministic source-bound compiler,
writer, tests, brief, and tracked outputs. The current fixture yields 2 frame
rows, 0 eligible frames, 0 segments, and 2 frame quarantines. The compiler
preserves raw identities and unavailable action/gripper/effort reasons,
splits on declared hard boundaries, prevents quarantined frames from bridging
segments, and keeps training, optimizer, and physical authority closed.

The repository-wide unit invocation was environment-limited at 616 tests with
69 dependency-import errors from the incomplete local runtime; the relevant
compiler, contract, normalization, processor, and pointer gates passed. T17.5
is now the next pending task and must not infer or pad windows from this empty
fixture.

## 2026-07-13 - Brief 111 T17.5 start

T17.5 is now `in_progress` under Brief 111. It may read only the verified T17.4
frame/segment outputs and compile deterministic unpadded windows at horizons
5, 10, 15, and 50. The present source has zero eligible segments, so its only
valid result is a signed empty `window_index.parquet` and explicit counts. No
padding, inferred actions, normalization rewrite, training, optimizer, Brev,
hardware, or physical authority is permitted.

## 2026-07-13 - Brief 111 T17.5 verification and T17.5b adoption

T17.5 is verified by Reviewer Decision 139. Its source-bound window compiler
and writer bind the T17.4 compiler manifest, frame/segment hashes, raw rollout
identities, and every window's exact frame/action IDs. The current verified
source remains correctly empty: `window_index.parquet` contains zero rows and
the manifest reports zero windows at horizons 5, 10, 15, and 50. Empty short
segments are reported rather than padded; all training, optimizer, physical,
and raw-rewrite authority flags remain false. Six focused adversarial tests
and the 74-test compiler/contract/processor/normalization/pointer/authority
gate passed, as did both deterministic writers and the pointer check.

The reviewer adopts T17.5b as the next pending task because no existing ledger
row owns recording the verified scripted grasp into complete raw experience.
The adoption includes one mandatory compatibility condition: current T17.4 and
T17.5 code accepts only `observed` action variants, while a truthful scripted
expert must retain by-construction identical variants as `derived` with an
explicit derivation. T17.5b must make that representation verifiable and
fail-closed before it emits or compiles a non-empty source. It may not relabel
derived values as observed.

## 2026-07-13 - Brief 112 T17.5b start

T17.5b is now `in_progress` under Brief 112. It begins with a narrow,
fail-closed compatibility rule for named `derived` action variants, then
records eight deterministic MuJoCo scripted-expert episodes into the ignored
append-only store `outputs/robot_lab/t17_5b_raw_store`. Seed 0 replays the
exact T19.0l request; other seeds use only a fixed +/-1 mm planar scene shift
and +/-0.03 rad yaw perturbation, with grasp pose and aperture re-derived by
the existing geometry path. Every episode also retains a 64-frame unassisted
stable-hold segment: phase boundaries remain explicit, and this is the minimum
recording duration that permits unpadded horizon-50 windows without crossing a
boundary. Failures are retained and labeled; no tuning, optimizer, training,
Brev, hardware, or physical authority is opened.

## 2026-07-13 - Brief 112 T17.5b verification

T17.5b is verified by Reviewer Decision 141. It records eight fixed-seed,
unassisted scripted MuJoCo grasp episodes as append-only content-addressed raw
bytes under `outputs/robot_lab/t17_5b_raw_store`; the tracked signed manifest
has identity `3860158e201e457146a167cfa778da14f210d88fa223cb075a1ec6d422ecfd1a`.
Seed 0 retains the T19.0l strict 8/24/12/24 cycle and five 256px top/wrist
keyframes; all eight seeds are strict successes. Requested actions are
observed, while the four equal pipeline variants are explicitly `derived` with
a named provenance derivation and independent compiler/window enforcement of
six finite named joints. The fresh source-bound compiler view reports 1,952
eligible frames, 88 hard-boundary segments, and zero quarantines; its unpadded
index contains 1,600/1,176/848/120 windows at horizons 5/10/15/50. A fresh
eight-seed temporary replay reproduced the manifest, compiler, and index
byte-for-byte. Training, optimizer, physical, and raw-rewrite flags remain
false. T17.6 is now the pending next task.

## 2026-07-13 - Brief 114 T17.6 start

T17.6 is now `in_progress` under Brief 114. It may inventory only the bounded
local legacy canary roots and must preserve their bytes. A candidate is
recompiled only if it already satisfies the current raw rollout/frame contract,
including action semantics, source identities, timestamps, hard boundaries,
and provenance. Every other candidate receives an explicit deterministic
quarantine reason; no normalized/action/coordinate reconstruction or inferred
migration is permitted. Training, optimizer, Brev, hardware, and physical
authority remain closed.

## 2026-07-13 - Brief 114 T17.6 verification

T17.6 is `verified`: the fixed inventory bound the legacy observation stream
(3,219 rows), DAgger intervention sidecar (660 rows), and 12-episode training
metadata. None exposes the current signed raw-rollout/frame envelope, complete
five-variant action lineage, integer nanosecond timing, source-bound frame
provenance, or the current hard-boundary contract; the sidecar also retains
unconfined legacy image paths. The signed inventory accepts zero candidates and
the new compiler view has zero frames, segments, and quarantines. This is a
truthful compatibility outcome, not a migration failure: the verified T17.5b
source remains the non-empty source for T17.7. Training, optimizer, raw
rewrites, hardware, physical actuation, and Brev remain closed or false.

## 2026-07-13 - Brief 115 T17.7 start

T17.7 is now `in_progress` under Brief 115. It may inspect only the verified
T17.5b append-only episode manifest/store and its tracked compiler/window
views. The audit will select exactly 25 deterministic windows at each supported
horizon, preserve raw-to-compiler-to-window identity binding, and materialize
only canonical actor-input/action descriptors. No model call, optimizer,
training data mutation, raw rewrite, hardware, physical authority, external
compute, or Brev activity is permitted.

## 2026-07-13 - Brief 115 T17.7 verification

T17.7 is `verified`: the signed audit samples exactly 100 windows, 25 at every
supported horizon, and includes every realized scripted rollout in every
horizon stratum. It verifies 1,952 raw frame identities against the compiler,
88 source segments, and 3,744 source windows; every selected frame is traced
through its raw record, compiler row, segment, and window index. Canonical
collection/training/inference input descriptors agree at the input-contract
boundary, while requested action descriptors remain separate training targets.
This is not model loading, inference, or trained-policy proof. M17 is complete;
training, optimizer, raw rewrite, hardware, physical actuation, external
compute, and Brev remain false or closed.

## 2026-07-13 - Brief 116 T18.1 start

T18.1 is now `in_progress` under Brief 116. It may inspect only the verified
T17.5b compiler/window source and T17.7 audit. The sampler must select valid
windows episode-first across source class, task phase, control mode, and horizon
with a fixed seed and explicit configured-versus-realized accounting. It must
not mutate buffers, mixture state, normalization, raw evidence, or training
authority; model calls, optimizer work, hardware, external compute, and Brev
remain prohibited.

## 2026-07-13 - Brief 116 T18.1 verification

T18.1 is `verified`: the signed initial selection contains 192 unique valid
windows—one deterministic hash-ranked window for each of eight realized
episodes in each of 24 complete source-class/task-phase/control-mode/horizon
buckets. The source binds the T17.5b index and the signed T17.7 audit; no
bucket is allowed to replace a missing episode with extra windows from another
episode. This selection is not a mutable buffer or mixture freeze. Model,
optimizer, training, raw rewrite, hardware, physical actuation, external
compute, and Brev authority remain false or closed.

## 2026-07-13 - Brief 117 T18.2 start

T18.2 is now `in_progress` under Brief 117. It may consume only the verified
T18.1 selection and its source bindings to create an append-only logical buffer
registry. Cycle 0001 must retain the exact selected IDs forever; any later
cycle must be additive, source-bound, and duplicate-free. No data buffer may be
materialized, no source window or raw evidence may be rewritten, and model,
training, optimizer, hardware, external compute, and Brev authority remain
closed.

## 2026-07-13 - Brief 117 T18.2 verification

T18.2 is `verified`: logical cycle 0001 retains the exact ordered 192 T18.1
selected IDs and their digest. The signed registry does not materialize a
dataset; later append validation rejects a changed prior cycle, duplicate cycle
ID, reused or absent source window, and authority escalation. Training,
optimizer, model, raw rewrite, hardware, physical actuation, external compute,
and Brev authority remain false or closed.

## 2026-07-13 - Brief 118 T18.3 start

T18.3 is now `in_progress` under Brief 118. It may inspect only the verified
T18.2 logical cycle and its source-bound compiler frames. It must compile exact
state task phase, progress, reward components, and provenance without exposing
reward/progress/contact/strict-evaluator fields to actor inputs. No buffer
mutation, model, optimizer, training, hardware, physical actuation, external
compute, or Brev activity is permitted.

## 2026-07-13 - Brief 118 T18.3 verification

T18.3 is `verified`: the exact ordered 192-window T18.2 logical cycle resolves
to 1,345 unique, source-bound compiler-frame component records. Each retains
the canonical task phase plus source phase, exact sourced/derived progress and
reward payloads, source pointer/provenance, finite-value predicates, and a
signed frame identity. Reward is checked against the already-recorded strict
evaluator result; phase normalization is retained rather than falsely treated
as a source-phase mismatch. The actor schema is exactly top RGB, wrist RGB,
joint position, and joint velocity; reward, progress, contact, strict
evaluator, gripper pose, aperture, effort, and other outcome fields remain
privileged. No buffer, model, optimizer, training, raw rewrite, hardware,
physical actuation, external compute, or Brev activity occurred.

## 2026-07-13 - Brief 119 T18.4 start

T18.4 is now `in_progress` under Brief 119. It may consume only the verified
T18.3 exact-state components and T18.2 logical cycle to construct immutable
snapshot and branch records. It must make the absence of current correction
evidence explicit rather than fabricate a failed or corrected episode. Fixture
tests may exercise branch semantics only when permanently labeled fixture-only.
No buffer, mixture, model, optimizer, training, raw rewrite, hardware,
physical actuation, external compute, or Brev activity is permitted.

## 2026-07-13 - Brief 119 T18.4 verification

T18.4 is `verified`: all 192 logical-cycle windows now have immutable snapshots
that exactly restore their ordered frame, component-record, and signed
frame-identity sequences. The current scripted-expert source contains no
correction evidence, so the tracked source-bound manifest truthfully contains
192 source/base branches and zero correction events. The branch-event helper is
fixture-only, rejects event or branch reuse and absent/cross-window references,
and cannot construct a source-bound correction event. No buffer, mixture,
model, optimizer, training, raw rewrite, hardware, physical actuation, external
compute, or Brev activity occurred.

## 2026-07-13 - Brief 120 T18.5 start

T18.5 is now `in_progress` under Brief 120. It may freeze only a deterministic,
reference-only source composition from the verified T18.1-T18.4 artifacts. It
must preserve the zero correction-event count, actor privilege boundary, and
all separated action variants; it may not materialize records, open a model,
run inference or an optimizer, or grant simulation-training authority.

## 2026-07-13 - Brief 120 T18.5 verification

T18.5 is `verified`: the frozen reference-only mixture and training-input
manifests bind exactly 192 ordered source windows, zero correction windows, the
four-field actor schema, and all five separated action variants. They are not a
materialized buffer and both declare training ineligible. M18 is complete; T20.2
remains pending because the central training authority and training lock are
closed.

## M16 - Twin And Dependency Foundation

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T16.0 | verified | none | Add a scoped dirty-path guard, freeze rungs 500/1,000, and validate the repo goal-loop launch | 70 tests; 51 protected paths unchanged across pair dry-run; b5d056b |
| T16.1 | verified | T16.0 | Inventory LeRobot, OpenPI reference, Menagerie/Robot Studio SO-101, licenses, and local patches | Dependency inventory and source evidence verified; executable resolution completed separately by T16.1b |
| T16.1b | verified | T16.1 | Unify the executable LeRobot/preprocessing revision used by every robotics stage | `dca2b45`; stack identity `c8e903e7...`; exact base + tracked patch + environment lock + saved-sample stage parity |
| T16.2 | verified | T16.1b | Define TwinProfile, TwinQualificationSpec, and TwinQualificationReport schemas | Schema scaffold plus T16.2b computed decision path verified on fixture evidence; no physical qualification |
| T16.2b-A | verified | T16.1b,T16.2,T16.4 | Define the only central composer for global authority from scoped component capabilities | `c0b9629`; reviewer 043; contract `6d04b205...`; 101-test broad gate; remote through `e1d59ca`; grants contract validity only |
| T16.3 | verified | T16.1-T16.2 | Reconcile current Robot Studio MJCF with pinned Menagerie rather than replacing it silently | `7bebf55` baseline plus semantic corrections through `cadc0f3`; reviewer decision 033 closes the v2 identity reopen after manager intervention 008 |
| T16.4 | verified | T16.2-T16.3 | Add measured-part mass intake and assembly inertia/COM compiler | Production compiler valid on declared fixture evidence; current-arm physical input remains blocked |
| T16.4b | verified | T16.2,T16.4,T16.2b-A | Implement strict production measured-inertial intake with local capability output | `7d05629`/reviewer 045/remote `dbdd1ef`; normalized Jacobi convergence/residual checks; scale-relative adversarial coverage; 17 focused and 131 broad tests |
| T16.2b | verified | T16.1b,T16.2,T16.2b-A,T16.4b | Compute qualification results from the specification and independently verify them | `710960b`/reviewer 046/remote `383557b`; 16 focused and 147 broad tests; fixture numeric pass remains qualification-withheld |
| T16.5 | superseded | T16.1b,T16.2b,T16.4b | Original combined census task | Split by owner steering into T16.5a/T16.5b/T16.5c/T16.6 so offline, live read-only, shadow, and supervised motion proof cannot collapse |
| T16.5a | verified | T16.1b,T16.2b,T16.4b | Offline no-write transport/lifecycle preflight | Corrected `5102422`/`eeb16e1`; reviewer 049; remote `2407299`; v2 protocol-0/hash/semantic binding; 16 focused and 195 broad tests; `census_trace_conformant` only |
| T16.5b | verified | T16.5a | Live read-only census and finite physical camera capture while owner-present lease is active | Attempt 006; private `125de28f...`; original manifest v4 `eff3c824...`, mechanically migrated manifest v5 `5218c3bd...`; exact two-camera 640x480 capture; 54 no-write reads; six torque-off values; sequential evidence only |
| T16.5c | verified | T16.5b | Real-observation preprocessing, PI0.5 shadow, and matched MuJoCo replay with no actuation | Negative transfer diagnosis verified through Brief 094/Reviewer 120: physical bracket/camera roles and diagnostic preprocessing/proposal/corrected consequence replay observed; sorting deployment input, matched physical replay, motion, transfer, qualification, and training withheld |
| T16.6 | pending | T16.5a-T16.5c | Exact initial supervised physical POC under final owner confirmation | Signed/content-addressed session permit; no-op-equivalent then at most one small one-joint delta and exact return; no second prompt; active lease; requested/projected/sent/measured separate; `supervised_micro_motion` only |

### 2026-07-13 - Brief 093 antipodal contact gate

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: v2 analytic antipodal gate verified; actual grasp still rejected; live gate closed; training lock closed
V1 preservation: strict fixture remains byte-identical at 4f0bad3c...
V2 requirements: distinct jaws; span >= 0.02 m; normal dot <= -0.8; contact-axis alignment >= 0.8
Positive: declared analytic expert semantic success; not policy, MuJoCo, physical, or full-wrench proof
Negatives: all 17 fail, including exact 4.907838 mm collapsed span, same jaw, same side, misalignment, malformed, and non-finite witnesses
Artifact: 950e7568... identity; 5ac9c96e... file SHA-256; 246755 bytes
Authority gained: strict_grasp_antipodal_contact_proxy_fixture_conformant only
Authority withheld: actual grasp, full 6D wrench closure, strict policy, physical twin, simulation training, optimizer, and motion
Next step: orientation/lateral MuJoCo search compiled through v2 and full unassisted phases
```

### 2026-07-13 - Brief 092 contact span and friction/compliance sweep

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: contact geometry/sweep observed; force closure and friction-only grasp rejected; live gate closed; training lock closed
Contact profile: 19 simultaneous-jaw frames; span collapses 32.86691 mm to 4.907838 mm during hold
Interpretation: two named jaw bodies contact one local region; contact count alone is not opposing force closure
Training grid: 12 friction x contact-time settings; zero lift successes; no selected candidate
Holdout: friction 4.0 / 0.01 s excluded from selection; also fails; final object z 0.322867 m
Artifact: 89c04062... identity; 8860549b... file SHA-256; 10245 bytes
Authority gained: mujoco_contact_span_profile_observed and bounded_contact_property_sweep_observed only
Authority withheld: force closure, strict/policy grasp, physical aperture/twin, simulation training, optimizer, and motion
Next step: orientation/lateral search with opposing normals, span, wrench closure, impact, and full unassisted phases
```

### 2026-07-13 - Brief 091 low-impact two-jaw search

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: low-impact two-jaw contact accepted; unassisted lift rejected; live gate closed; training lock closed
Search: 20 fixed wrist-roll x pregrasp-height candidates; same nominal object/model/seed/close target
Selected: wrist roll -1.5 rad; height 0.018 m; 11 two-jaw close frames; 8/8 prelift hold frames; peak 4.1971684 N
Lift: no weld/assist; only 4 two-jaw lift frames; 0/12 lift-hold frames; final object z 0.324974 m below required 0.35 m
Joint evidence: two-jaw contact at 0.2395 to 16.724525 gripper percent; metric aperture not inferred
Artifact: 5a5de249... identity; fa250ee6... file SHA-256; 186089 bytes
Authority gained: low_impact_two_jaw_mujoco_contact_candidate_observed only
Authority withheld: unassisted/strict/policy grasp, metric aperture, physical qualification, simulation training, optimizer, and motion
Next step: geometry-derived aperture plus bounded friction/compliance/close-hold sweep with held-out setting
```

### 2026-07-13 - Brief 090 first MuJoCo anchor grasp attempt

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: deterministic attempt observed and strict grasp rejected; live gate closed; training lock closed
Object: nominal nonphysical 50 x 35 x 30 mm, 25 g turquoise anchor cousin
Rollout: two exact 371-frame replays; complete non-image state/action/contact/assist/object/gripper trace retained
Legacy score: placement pass after contact-gated weld assistance; not unassisted or policy grasp success
Strict result: fail on 17.081659463 N peak impact, missing current and aperture calibration, one-sided grasp contact, invalid stable hold, and contact-retaining release
Artifact: 32f14feb... identity; 831fdf2a... file SHA-256; 439297 bytes
Verification: 9 focused tests; 69-test relevant broad gate; Brief 089 fixture byte-identical
Authority gained: deterministic_mujoco_anchor_grasp_attempt_observed only
Authority withheld: unassisted/strict/policy grasp success, physical profile, twin qualification, simulation training, optimizer, and motion
Next step: low-impact two-jaw pregrasp/close, nominal simulation aperture profile, stable hold, and clean release
```

### 2026-07-13 - Brief 089 strict anchor grasp evaluator

```text
Current task: T16.5c / Minimum Viable Grasping Twin
State: evaluator fixture verified; T16.5c still in progress; live gate closed; training lock closed
Physical anchor: visible small lightweight turquoise rectangular candidate bound to accepted external frame; dimensions, mass, COM, material, friction, and pose unknown
Nominal cousin: declared analytic simulation geometry and mass; no physical-measurement claim
Positive: one ordered analytic-expert trace passes semantic strict-grasp success and remains pure_policy_success=false
Negatives: all 12 adversarial traces fail through the same evaluator for their expected reasons
Artifact: 4f0bad3c... identity; 3be8ac16... file SHA-256; 133859 bytes
Verification: deterministic fixture exact; 6 focused tests in each repository runtime; 66-test relevant broad gate
Authority gained: strict_grasp_evaluator_fixture_conformant only
Authority withheld: MuJoCo grasp validity, physical anchor profile, policy success, physical twin qualification, simulation training, optimizer work, and motion
Next step: execute a deterministic anchor-cousin grasp in pinned MuJoCo and feed measured trace through the unchanged evaluator
```

### 2026-07-13 - Brief 088 midpoint coordinate replay correction

```text
Current task: T16.5c
State: in_progress; live gate closed; training lock closed
Cause: legacy simulation-policy shoulder/elbow offsets were applied to the pinned midpoint-calibrated physical-pose model
Correction: preserve legacy v1; add a separately versioned fail-closed midpoint-direct candidate for offline physical-pose diagnostics
Candidate review: b98445cb...; direct identity selected for offline replay only; metric transform and twin qualification false
Replay: a0179263...; horizons 5/10/15 twice exactly; zero start/action projection; zero robot self-contact; zero warnings; near-zero cube motion
Remaining rejection: physical scene mismatch, no metric camera/workcell transform, invalid policy input, wrist-roll support mismatch, 54.4099-degree first wrist change, 5.43238 rad/s maximum simulated velocity
Verification: 188 focused tests in each pinned runtime; 293-test broad authority/twin gate; legacy dependency/preprocessing/reviewed-input/fixture and twin/authority identities remain byte-stable
Authority gained: midpoint pose candidate and corrected prefix-replay diagnostic observations only
Authority withheld: accepted input/shadow, matched replay, safe_enough_to_prepare_t16_6, motion, qualification, training, Brev, and paid compute
Next step: first executable offline Minimum Viable Grasping Twin slice around the visible turquoise anchor
```

### 2026-07-13 - Brief 087 current physical preprocessing, shadow, and replay diagnostic

```text
Current task: T16.5c
State: in_progress; live gate closed; training lock closed
Inputs: accepted private-success v2 final frames, reviewed external/wrist roles, exact q_after, exact sorting prompt
Preprocessing: 57acad57...; exact tensors 89644c19... / 8041d823... / missing 811b0abf...; wrist roll outside observed checkpoint min/max
Inference: exact local revision 84b551af... and weights 471adf9a...; real MPS two-pass fixed-noise equality; finite 50x6 chunk 4d350587...
Proposal finding: first wrist-roll delta 54.4099 degrees; maximum chunk deltas include 55.8645 wrist roll and 51.5712 elbow flex; DO_NOT_ACTUATE
Replay: 42499e46...; horizons 5/10/15 twice exactly; no warnings; near-zero cube motion; shoulder lift/elbow start projection and every-action projection; shoulder/lower-arm self-contact
Authority gained: diagnostic tensor, proposal, and prefix-control-replay observations only
Authority withheld: accepted live input, accepted policy shadow, matched replay, safe_enough_to_prepare_t16_6, motion, qualification, training, Brev, and paid compute
Next step: offline measured-pose coordinate and collision reproduction; do not open a motion gate
```

### 2026-07-13 - Brief 084 private current-frame retention

```text
Current task: T16.5c
State: in_progress; accepted session remains v1; live gate closed; training lock closed
Experiment-derived gap: accepted bracket retained four frame hashes and semantics but not current pixel bytes, blocking real preprocessing
Correction: future successful sessions emit private-success v2 with four exact source-bound PNGs; result/receipt/tracked review remain hash-only; v1 remains verifiable
Verification: targeted red then green; 183 focused tests per pinned runtime; 382 broad tests in 121.863 seconds; source verifiers in both runtimes; actual accepted v1 verifies in both; compile/workflow/JSON/privacy/diff checks
Authority gained: private_source_bound_current_frame_retention_conformant only
Authority withheld: accepted live policy input, preprocessing, model, inference, shadow, replay, motion, qualification, training, and paid compute
Next step: remote confirmation, then a separately reviewed finite bracket with fresh profile, discovery, lease, holder preflight, and no-torque cleanup
```

### 2026-07-13 - Brief 074 unselected AVFoundation source correction

```text
Current task: T16.5c
State: in_progress; live gate open; sessions started zero; training lock closed
Failure: fresh macOS discovery added AVFoundation-only Capture screen 0; candidate construction rejected before contract or device open
Correction: require system-camera names to be a subset of AVFoundation names; resolve static-pose selections only from sources with exact system identities; selecting the screen source still rejects
Actual evidence: discovery 4c29fe9c... resolves RealSense index 0 and C922 index 1; candidate preflight f8555cad...; hardware_accessed false
Verification: 78 focused tests per pinned runtime; 378 broad tests; both source verifiers in both runtimes; diff checks
Authority gained: unselected_avfoundation_source_tolerance_conformant only
Authority withheld: live observation acceptance, reviewed input, model, inference, replay, motion, qualification, and training
Next step: remote confirmation, fresh profile and lease, then the one allowed candidate session
```

### 2026-07-13 - Live candidate rejected; gate consumed and closed

```text
Current task: T16.5c
State: in_progress; gate closed; sessions started one; training lock closed
Attempt: t16-5c-20260713-0845-cdt
Failure: camera-frame normalization rejected invalid fields after session start; no success result or receipt issued
Evidence: discovery 673ff2d2...; profile 69e86eda...; lease 43fc0c72...; contract e6bf4f62...; immutable failure b117e797...
Shutdown: Studio follower disconnected; torque false; leader connected; canonical/TTY holders [0,0]
Authority: no observation, reviewed input, policy, replay, motion, qualification, or training label
Next step: one narrow offline frame-contract correction; any future live attempt requires a new reviewed gate
```

### 2026-07-13 - Brief 076 live frame metadata adapter verified offline

```text
Current task: T16.5c
State: in_progress; prior gate closed/consumed; training lock closed
Reproduced mismatch: pinned generic reader returns 5 semantic fields plus exact receive-start/finish timestamps; strict runtime accepts exactly 5 semantic fields
Correction: pinned live adapter validates exact field set and increasing nonnegative integer receive interval, rejects unknown/missing/invalid metadata, then returns unchanged semantic view
Verification: targeted test red then green; 79 focused tests per pinned runtime; 379 broad in 124.646 seconds; both source verifiers in both runtimes; compile/diff checks
Authority gained: live_static_pose_frame_metadata_adapter_conformant only
Authority withheld: live gate/session, observation acceptance, reviewed input, model, inference, replay, motion, qualification, and training
Next step: remote preservation, then a separately reviewed fresh gate and full preflight
```

### 2026-07-13 - Brief 071 Full Access/no-prompt runtime policy verified offline

```text
Current task: T16.5c
State: in_progress; Brief 071 verified and remotely preserved; live gate closed
Completed: trusted project default plus explicit hardware profile now require danger-full-access/never; formal doctor, same-thread runtime evidence, candidate gate, and redacted review require the same no-prompt semantics; profile-purpose instructions remain distinct
Evidence: implementation 19b7e766f31e4bf5702e454c62606165bf023dc5; reviewer 097; profile hashes 65edfaff.../0fce3e51.../66378a47...
Verification: 96 proof-ladder tests in each pinned runtime; 70 static-pose tests in each; 371-test authority/twin gate; both source verifiers in both runtimes; compile/JSON/workflow/state-alignment/diff checks
Adversarial: restricted or interactive defaults; on-request profile/turn/doctor; stale/cross-thread/changed runtime; profile field/content drift; permissions cannot grant gate, lease, session, proof label, training, or motion authority
Authority gained: full_access_no_prompt_runtime_profile_contract_conformant only
Authority withheld: live candidate session, accepted static pose, reviewed production input, policy shadow, replay, actuation, T16.5c verification, T16.6 permit, qualification, training
Runtime at Brief 071 review: live-ineligible because that earlier task was managed/restricted; a fresh task had to prove danger-full-access/never
Hardware: none; no discovery/open, serial/camera/Studio, model, MuJoCo, motion, optimizer, training, Brev, or paid compute
Training lock: closed
Next step: canonical review reconciliation, then a fresh no-prompt Full Access task and separate remotely confirmed one-session gate
```

## M17 / Gate A - Truthful Experience Compiler

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T17.1 | verified | T16.2,T19.0l | Define immutable raw rollout/frame records and provenance dictionaries | Brief 107/Reviewer 133; maintenance reconciliation 2f880d0 / Session 140 / Reviewer 136 updates the current content-addressed projection identity without rewriting Brief 107; grasp/twin/coordinate bound; stable rollout/frame identities; canonical/source phases; recovery only a control mode; five action variants remain distinct; two-frame fixture quarantined for five missing-data reasons; 210-test broad gate |
| T17.2 | verified | T16.2-T16.3,T17.1 | Implement a named canonical SO-101 processor shared by collection, training, evaluation, and adapters | Brief 108/Reviewer 134; maintenance f6626fa / Session 141 / Reviewer 137 rebinds the source reference; processor 59827b3d...; pure unclamped transform, fail-closed bounds, explicit requested/executed limiter; 128 round trips max 4.441e-16; golden parity and monotonic gripper; 221-test broad gate |
| T17.3 | verified | T17.2 | Generate immutable `normalization_bundle.json` | Brief 109/Reviewer 135; maintenance f6626fa / Session 141 / Reviewer 137 rebinds the processor reference; bundle dea3ff8c...; 94,568-sample MEAN_STD statistics; actual cached processor/tokenizer fixture parity; camera/order/runtime/tensor hashes pinned; production/training false; 227-test broad gate |
| T17.4 | verified | T17.1-T17.3 | Compile `frames.parquet` and hard-boundary `segments.parquet` | Brief 110/Reviewer 138; commit 1a37466; 2 frame rows, 0 eligible frames, 0 segments, 2 quarantines; deterministic Parquet/JSON outputs; quarantined rows cannot bridge segments; training/optimizer/physical authority closed |
| T17.5 | verified | T17.2-T17.4 | Compile unpadded `window_index.parquet` for horizons 5/10/15/50 | Brief 111/Reviewer 139; commit cc507f3; 0 rows at all horizons from the verified empty source; source manifest/hash and exact frame/action identities bound; no gaps, missing actions, padding, reset, teleport, drift, or forbidden transition |
| T17.5b | verified | T17.1-T17.5,T19.0l | Record deterministic scripted single-cube grasp episodes into an append-only raw store with complete per-frame evidence | Brief 112/Reviewer 141; commits 5c3c34b + 8ccee81; 8/8 strict successes, five seed-0 256px proof keyframes, 1,952 eligible frames, 88 segments, zero quarantines, and 1,600/1,176/848/120 unpadded 5/10/15/50 windows; derived variants require named provenance plus six finite named joints; training/optimizer/physical/raw-rewrite false |
| T17.6 | verified | T17.1,T17.4,T17.5b | Audit bounded legacy canary descriptors and recompile only exact current raw-record evidence | Brief 114/Reviewer 142; implementations `520ca0c` + `68b20ed`; signed inventory `5ba35300...`; 3 descriptors/0 accepted/3 quarantined; explicit source-bound zero-row compiler view; no guessed migration or authority escalation |
| T17.7 | verified | T17.5b,T17.6 | Audit 100 deterministic windows from raw grasp frames through compiler and index rows | Brief 115/Reviewer 143; implementations `435ecd9` + `c1f0a40`; signed audit `e0fca4fe...`; 25 windows at every 5/10/15/50 horizon, all 8 rollouts per stratum; model-free canonical input/action descriptor parity |

## M18 / Gate B - Intentional Mixture And Corrections

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T18.1 | verified | T17.7 | Sample valid windows episode-first over source x task-phase x control-mode x horizon | Brief 116/Reviewer 144; implementation `ce3a12c`; signed selection `17f804dd...`; 24 complete buckets × 8 episodes = 192 unique windows; fixed seed 181001, immutable logical sampling cycle, no buffer/training mutation |
| T18.2 | verified | T17.1,T17.7,T18.1 | Preserve append-only logical source/cycle buffers | Brief 117/Reviewer 145; implementation `4a034f4`; signed registry `b1b08441...`; immutable cycle 0001 binds exact 192 selection IDs; prior-cycle mutation and duplicate reuse reject; no materialized buffer |
| T18.3 | verified | T17.1,T17.4,T18.2 | Compile exact-state phase, progress, reward components, and provenance | Brief 118/Reviewer 146; implementation `b55186d`; signed manifest `40f522d1...`; all 192 cycle windows map to 1,345 unique source-bound frames; exact phase/progress/reward predicates; four-field actor schema excludes privileged outcomes; no buffer/training mutation |
| T18.4 | verified | T16.3,T17.1-T17.5,T18.3 | Implement snapshot branch-and-correct linked by `correction_event_id` | Brief 119/Reviewer 147; implementation `c588a92`; signed manifest `7b0d00e9...`; 192 exact source snapshots/base branches; zero source correction events; fixture-only event mechanism rejects reuse, mutation, and source-evidence spoofing |
| T18.5 | verified | T18.1-T18.4 | Generate `dataset_mixture_manifest.json` and training-input manifest | Brief 120/Reviewer 148; implementation `4a5afd5`; frozen reference-only 192-window/zero-correction composition; actor schema and five action variants preserved; training remains ineligible |

## M19 - Physical Hardware Twin Qualification

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T19.0 | verified | T16.3,T16.5c | Establish truthful simulated gripper geometry and contact semantics before grasp search | Brief 095/Reviewer 121; audit `9bfce4c6...`; 3 bodies/12 geoms; original composite collisions non-pad; explicit pad boxes; 5.238-130.944 mm simulation reference aperture; order-independent inward-normal proof; 174-test broad gate |
| T19.0b | verified | T19.0 | Make grasp orientation and object yaw independently controllable and verified before search | Brief 096/Reviewer 122; fixture `cdcb2359...`; 4/4 candidates; exact wrist/yaw; max residual 0.538 mm; requested/achieved axes; collision-free; 176-test broad gate |
| T19.0c | verified | T19.0,T19.0b | Run deterministic bounded geometry-first grasp search without friction/compliance tuning | Brief 097/Reviewer 123; 12 Halton candidates + untouched holdout; 10 reachable; zero pad contacts/eligible; composite jaw occlusion isolated; 178-test broad gate |
| T19.0d | verified | T19.0c | Correct explicit-pad collision occlusion without tuning friction or search ranges | Brief 098/Reviewer 124; identical rerun; 3 candidates/277 positive fixed-pad contacts up to 4.338 N; zero moving-pad/bilateral contacts; 180-test broad gate |
| T19.0e | verified | T19.0d | Center object on predicted pad midpoint instead of gripperframe/fixed-pad reference | Brief 099/Reviewer 125; identical 12 candidates + excluded holdout; 2 bilateral candidates through 8/8 hold frames; zero strict-v2/eligible; 182-test broad gate |
| T19.0f | verified | T19.0e | Separate object-yaw/table settling from gripper-induced preclose motion | Brief 100/Reviewer 126; 6/12 approach-motion-valid; 2 bilateral through 8/8 hold frames; zero strict-v2/eligible; 184-test broad gate |
| T19.0g | verified | T19.0f | Align the gripper closing axis with an anchor principal axis before search | Brief 101/Reviewer 127; 4 candidates at 0.806-0.886 alignment; 2 motion-valid; zero bilateral/strict-v2/eligible; 186-test broad gate |
| T19.0h | verified | T19.0g | Jointly solve wrist flex and roll for a horizontal principal-axis closing vector | Brief 102/Reviewer 128; zero solutions at >=0.95 x-axis alignment and <=0.1 vertical; zero contact/eligible; 188-test broad gate |
| T19.0i | verified | T19.0h | Evaluate both anchor x and y principal axes under the same horizontal gate | Brief 103/Reviewer 129; 8 y-axis aligned, 6 motion-valid, 2 bilateral through 8/8 hold, zero strict-v2/eligible; 190-test broad gate |
| T19.0j | verified | T19.0i | Center the target along the selected closing axis while retaining transverse offset | Brief 104/Reviewer 130; 8 centered, 6 motion-valid, 2 bilateral through 8/8 hold; max span 20.965 mm; alignment <=0.052; zero strict-v2/eligible; 192-test broad gate |
| T19.0k | verified | T19.0j | Audit actual contact faces and normals for centered bilateral candidates | Brief 105/Reviewer 131; candidates 2/3 source-identical; fixed pad +z 30/30; moving pad -y 27/30; convention proof valid/order-independent; 194-test broad gate |
| T19.0l | verified | T19.0k | Build geometry-derived unilateral-jaw close/hold/lift/lower/release proof | Brief 106/Reviewer 132; q=0.249247 rad from 37 mm target aperture; 6 nm preclose motion; strict-v2 8/8 hold, 24/24 lift, 12/12 unsupported hold, 24/24 lower; 36.271 mm lift; zero assist/non-pad frames; final retreat clear; 198-test broad gate |
| T19.1 | verified | M16, read authority | Run read-only servo/firmware/register census | Brief 212/Reviewer 282; centrally composed session `t19-1-20260716-0712-cdt`; six model-777 firmware-3.9 servos, torque off 6/6, 54/54 reads, zero retries/writes/torque changes/motion/unexpected operations, one no-torque close, no cameras; manifest `f423f5d3...` |
| T19.2 | in_progress | T19.1, motion authority | Calibrate cameras, joint offsets, kinematics, timing, and gripper aperture | Brief 213/Reviewer 283 readiness; Brief 214/Reviewer 284 target; Brief 215/Reviewer 285 fixture-only +8-tick/0.7033-degree wrist-roll watchdog/deadman/exact-return harness `1282784f...`; T19.2c next binds printed-target evidence and central one-use live authority, with no gate yet |
| T19.2d | verified | historical WCW-1, owner request | Produce and deliver a printer-ready weighted AprilTag cube without opening physical calibration authority | Brief 221/Reviewer 298; source commit `b24ac30`; 13 watertight/manifold/outward STLs with zero source self-intersections; six ordinary nominal 20 mm balls; tag36h11 IDs 0-4; ZIP `b650af2a...`; Gmail message `19f6d356a4121193`; physical print/QC remains unproven |
| T19.2e | verified | T19.2d, owner batched-plate request | Batch the verified WCW-1A parts for Bambu-class plates and deliver a replacement package | Brief 223/Reviewer 300; source commit `fb0800e`; standard-3MF two-job 256 mm and four-job 180 mm routes; unchanged 13-STL geometry; ZIP `553e8c63...`; Gmail replacement `19f6d4d052383966`; native slice/physical QC remains unproven |
| T19.3 | pending | T19.1-T19.2, motion authority | Identify delay, saturation, settling, directionality, backlash, friction, compliance | Per-joint fitted distributions and held-out trajectory evidence |
| T19.4 | pending | T19.2-T19.3, contact authority | Identify fingertip/table friction, slip, force/current, and object profiles | Held-out grasp/lift/slip/release envelope |
| T19.5 | pending | T16.4, T19.2-T19.4 | Fit posterior and run held-out qualification | Every TwinQualificationSpec metric passes or is explicitly failed |
| T19.6 | pending | T19.5, M17 | Bind qualified twin hash and requalification triggers to all downstream artifacts | Contract/hardware drift blocks execution |

## M20 / Gate C - Cheap Falsification And Clean Supervision

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T20.1 | verified | M17-M18 | Freeze one clean simulation-only single-cube dataset, split, structural twin, prompts, seeds, and semantic-success proof contract | Brief 121/Reviewer 149; 488 train + 244 held-out source-bound frames; central decision grants only `simulation_training_ready` |
| T20.2 | verified | T20.1 | Overfit one to three episodes with ACT | Brief 122/Reviewer 150; 100 updates: train L1 1.0217 -> 0.1682, held-out 0.2213; policy-owned rollout made zero strict contacts and 0.2023 mm lift vs 25 mm; verified negative, not promoted |
| T20.3 | verified | T20.1 | Repeat tiny overfit with PI0.5 | Brief 123/Reviewer 151; 20 finite LoRA updates: train 100.8441 -> 100.0873, held-out 130.0066 -> 128.4057; policy-owned rollout made zero strict contacts and 0.0003007 mm lift vs 25 mm; verified negative, not promoted |
| T20.4 | verified | T20.2-T20.3 | Add explicit accumulation and run 250/500/1,000 optimizer-update MPS ladder | Brief 124/Reviewer 153; 500 updates reduced held-out loss 130.0066 -> 1.8620 but zero strict contacts persisted; first command retained 0.655 rad gripper error, so 1,000 was retired |
| T20.5 | verified | T20.4 | Sweep PI0.5 execution horizons 5/10/15 with chunk size 50 | Brief 125/Reviewer 154; 49/25/17 refills produced distinct action hashes but identical zero-contact and 0.0003007 mm lift failures; queue-duration hypothesis closed |
| T20.6 | verified | T20.2-T20.5 | Run fixed one-cube phase-level and adversarial outcome-versus-strict evaluation | Brief 126/Reviewer 155; analytic positive passes all eight stages; all 8 target-reaching adversarial traces retain stable occupancy while failing strict success for their expected reason |
| T20.7 | verified | T20.1, T20.6 | Bake off PI0.5, SmolVLA, ACT, and Diffusion Policy | Brief 127/Reviewer 157; exact 20-sample local-MPS rung and same seed-2 closed loop completed for all four; zero strict contacts and zero strict successes, no winner; ACT lifted 2.4213 mm vs 25 mm; Diffusion also failed no-projection with 52 clipped frames |
| T20.8 | verified | T20.6-T20.7 | Accept or reject simulation policy using semantic strict success; separately evaluate transfer eligibility | Brief 128/Reviewer 158; central decision `05878200...` has no selected model and 0/3 strict repeats; simulation policy, physical transfer, and promotion rejected |
| T20.9 | verified | T20.8 | Replay held-out source expert actions through the exact policy closed-loop adapter and localize first divergence | Brief 129/Reviewer 159; exact 244-action/state/object/contact reproduction, 36.3853 mm lift, zero projection/assist; only release-clear semantic mismatch remains |
| T20.10 | verified | T20.9 | Reconcile release-clear semantics and rerun the exact source oracle | Brief 130/Reviewer 160; legacy artifact stable; corrected exact oracle passes all gates with release active-contact clear 1/1 and retreat geometry clear 1/1 |
| T20.11 | verified | T20.10 | Localize learned action errors against the exact source oracle by model, phase, and joint | Brief 131/Reviewer 161; all four diverge frame 0; PI0.5 non-gripper MAE 0.03097 rad vs gripper 0.75432 rad; diagnostic hypothesis only |
| T20.12 | verified | T20.11 | Audit the PI0.5 gripper channel end to end before retraining | Brief 132/Reviewer 162; 3.606e-9 rad max round-trip vs 1e-8; equal six-way loss weights; four action channels outside checkpoint normalizer min/max |
| T20.13 | verified | T20.12 | Derive a train-only dataset-bound PI0.5 state/action normalizer | Brief 133/Reviewer 163; train means/stds within 2.35e-7 of 0/1; inverse errors <=1.23e-9 rad; wrist-roll target mean-square 412.39 -> 1.0 |
| T20.14 | verified | T20.13 | Retrain PI0.5 with frozen dataset-bound normalization and equal loss weights | Brief 134/Reviewer 164; gripper error 0.75432 -> 0.23898 rad, but non-gripper MAE 0.03097 -> 0.74683 rad; zero strict contact and five reviewed keyframes |
| T20.15 | verified | T20.14 | Isolate PI0.5 state-token versus action-postprocessor normalizer effects | Brief 135/Reviewer 165; action postprocessor arm effect 0.95872 rad, state effect 0.23586, interaction 0.26037; no optimizer or rollout |
| T20.16 | verified | T20.15 | Test checkpoint arm/state scaling with dataset-derived gripper-only action postprocessing | Brief 136/Reviewer 166; frame-zero arm/gripper errors 0.03088/0.12015 rad passed; trajectory MAE 0.90603 rad, zero strict contacts, 0.0003007 mm lift; zero conversion clipping/projection; five reviewed keyframes; hybrid retired |
| T20.17 | in progress | T20.16 | Consolidate the recreation at package boundaries before any clean pi05_base campaign | Briefs 137–139 retain compact bespoke IP, remove only unreferenced test-only surfaces, bind native LeRobot episode provenance, and observe actual PI0.5 processor outputs; a source dataset and separate authority are still required before any optimizer or campaign |
| T20.38 | verified | preserved T20.36l boundary | Derive a policy-independent quantitative strict-v2 receipt contract | Briefs 209/211, Reviewer 280; receipt `042bf0be...` binds 33 predicates with guard-preempting bottleneck and remains analytic-fixture evidence only |
| T20.39 | verified | T20.19,T20.38 | Define the counterexample archive schema and bootstrap T20.19 gripper-1.05 | Briefs 210/211, Reviewer 280; receipt `60babc53...`, index `043d45b3...`; routing-bound, evidence only, replay/training inactive |
| T20.39a | verified | T20.38,T20.39 | Harden receipt/archive guard, duplicate, routing, and stale-source verification | Brief 211/Reviewer 280; implementation `83d51c5`; 24 contract + 12 pointer tests; no model/replay/hardware action |
| T20.40 | deferred | T20.39,mechanical Gate C pass | Replay the fixed active archive on every checkpoint eligible for selection | Required Gate C pass is absent; no replay authority granted |
| T20.41 | verified | T20.36o,T20.39,owner decision | Select and authorize the next capability strategy after ACT, SmolVLA, and X failed forward routing | Owner decision `ae75bb59...` at `e9d0507` selects R0-R3; no silent correction-objective continuation |
| T20.42 | verified | T20.41,T17.5b,T20.18,T20.23 | R0 dataset expansion by construction | Briefs 216-218/Reviewer 290; sole result `d238379b...` passes 119/119 training and 9/9 fresh held out; exact base once; 129 episodes/31,366 frames; independent verifier exit 0 |
| T20.42a | verified | reviewed T20.42 contract implementation | Implement R0 central request/runtime preflight/one-use permit/marker contracts | Brief 217/Reviewer 287; 9 focused + 70 broad + 8 MuJoCo source tests; authority artifacts, marker, and generation remain prohibited |
| T20.42b | verified | verified T20.42a + fresh owner window | Implement/review live collector, authority materializer, and sole fixed R0 runner; materialize/review/execute the pre-run boundary | Brief 218/Reviewers 288-290; one attempt, no retry, result `d238379b...`, mixture `37b30d34...`, statistics `02ba0e70...`, retention `19d19fba...` |
| T20.43 | verified | verified T20.42 | R1 ACT standard rung | Brief 219/Reviewer 293; sole marker `064e5650...`; zero updates; checkpoint-0 chunk-50 trace `6133ce58...`; renderer child lacks MuJoCo; terminal receipt `b64ec6d0...`; no retry; trained ACT unresolved |
| T20.43b | in_progress | verified T20.44 terminal boundary on origin | One owner-authorized ACT replacement after the renderer-only T20.43 failure | Brief 222/Reviewers 299/301/302; acceptance `5f2abf3`; marker absent; replacement unconsumed; fresh authority epoch required next window |
| T20.44 | verified | verified T20.42,T20.43 boundary | R2 SmolVLA standard rung | Brief 220/Reviewer 297; sole result `9d916206...`; 5,000 finite updates; 5 checkpoints/10 rollouts; 0 Gate C passes; no retry |
| T20.45 | pending | R1/R2 evidence | R3 conditional pi0.5 standard rung or costed external-compute proposal | Local run or proposal only under a fresh brief; external compute/Brev consumption remains unauthorized |

The external-example disposition and adversarial semantic-success requirements are
recorded in `docs/autonomous-workflow/so-frame-adoption-decision.md`. They add no
current dependency, runtime, checkpoint, model asset, training authority, or
hardware authority.

## M21 / Gate D - Improve A Competent Policy

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T21.1 | pending | M20 | Emit exact-state SARM-compatible progress data | Hashed progress artifact and predicate validation |
| T21.2 | pending | T21.1 | Compare uniform BC, balanced BC, and balanced exact-progress RA-BC | Paired ablation on identical seeds |
| T21.3 | pending | T21.2 | Add residual-RL readiness gate | Blocks without repeatable strict success and deployment-honest actor inputs |
| T21.4 | pending | T21.3 | Adapt EXPO-style learner/client interfaces | Frozen base, bounded residual, privileged critic allowed, actor privilege rejected |
| T21.5 | pending | T21.4 | Run bounded residual-RL experiment | Budget/safety logs and paired accept/reject evaluation |
| T21.6 | pending | T20.40,Gate D competent policy; T19.5 for posterior mode | Run an expert-competence-gated CEGIS scene adversary: one-factor search first, then bounded compound edits only after useful yield | Expert-policy regret receipts, actionable counterexample archive, complete regression replay, fixed budget and untouched realism holdout; training ingestion remains separate |
| T21.7 | pending | T21.5-T21.6 | Final promotion/rollback decision | Accepted-pointer integrity and proof matrix |

## M22 - Physical Shadow And Closeout

| ID | State | Depends on | Task | Verification / artifacts |
|---|---|---|---|---|
| T22.1 | pending | M19, M21 | Run explicitly authorized read-only observation/tensor parity in shadow mode | Real versus compiled tensors; no actuation |
| T22.2 | pending | T22.1, motion authority | Review commands, then validate one low-risk phase at reduced speed | Deadman/workspace limits and physical evidence |
| T22.3 | pending | T22.2 | Produce final sim-to-real capability audit | Honest proof matrix and remaining gates |

## Existing Work Disposition

- M0-M9 safety, Git, cleanup, evaluation, promotion, and rollback contracts remain valid.
- T10.1-T10.5 are legacy-v1 precursors superseded for new training by T17.1-T17.7.
- T11.1 is superseded by valid-window T18.1; T11.3 remains a useful trigger primitive.
- T11.4 hash/duplicate checks remain useful but its registry is superseded by T18.2.
- T12.1-T12.5 remain valid and will be reused by M20-M21.
- T13.1's 250 rung remains pipeline/development evidence; later rungs move to T20.4.
- T13.2-T13.4 move to T20.5, T20.7, and T20.8.
- M14-M15 move to M21-M22.

## Milestone Log

### 2026-07-12 - Brief 062 desktop-resume hardware-profile correction verified

```text
Current task: T16.5c
State: in_progress; exact current turn hardware-profile eligible; live gate closed; training lock closed
Completed: resumed session metadata may repeat only when all existing fields remain exact and only memory_mode is added; latest exact turn still controls the runtime decision
Evidence: implementation d404778; turn 7d245960...; profile 4ade6d50...; on-request; danger-full-access; hardware_accessed false
Verification: 177 focused tests in each pinned runtime; live doctor/profile capture; py_compile; diff checks; 376 broad tests in 102.558 seconds
Adversarial: changed thread, cwd, git, timestamp, source, CLI, provider, field removal, unexpected addition, existing-value mutation, stale never turn, profile drift, or before/after runtime drift still reject before hardware
Authority gained: current same-thread hardware-supervised runtime eligibility only
Authority withheld: live gate, device discovery/open, observation acceptance, reviewed input, tensors, model, inference, shadow, replay, actuation, qualification, and training
Next step: separately review, commit, push, and remote-confirm one fresh finite static-pose gate before discovery
```

### 2026-07-12 - Brief 061 preflight rejected; live gate closed unused

```text
Current task: T16.5c
State: in_progress; live gate closed; session count zero
Failure: formal hardware-profile capture rejected before discovery because one rollout contained repeated session metadata and concurrent active turn IDs with contradictory on-request and never policies
Safety: no USB, serial, camera, servo bus, holder discovery, model, policy, replay, training, or paid compute access; no private session outcome artifact required because the session never started
Correction: do not weaken the active-runtime verifier or select a favorable stale context; end the conflicting turn and start one unambiguous hardware-supervised on-request parent
Authority gained: none
Authority withheld: all live observation, reviewed input, tensor, model, shadow, replay, actuation, qualification, and training labels
Next step: push this fail-closed transition, repair the app thread permission mode between turns, then open a new separately reviewed finite gate
```

### 2026-07-12 - Brief 060 one-session T16.5c live gate transition

```text
Current task: T16.5c
State: in_progress; live gate open only after this transition commit is confirmed on origin
Window: 2026-07-12T10:55:00-05:00 through 2026-07-12T11:25:00-05:00; one session; fresh five-minute owner-presence lease required
Runtime: active thread 019f5372... independently observed danger-full-access, on-request, permission profile disabled
Allowed: metadata discovery; canonical and TTY zero-holder checks; exact identity/calibration/640x480-at-30 verification; six Present_Position reads before; two frames per signed camera; six Present_Position reads after; no-torque close; post-close all-alias zero-holder check; one immutable private outcome artifact
Forbidden: handshake, configuration or register writes, torque changes, motion commands, policy execution, training, retries of the overall session, reconnect, paid compute
Authority gained: one fresh static-pose candidate session only after remote confirmation
Authority withheld: static_pose_bracketed_observation, reviewed physical policy input, model load, inference, policy shadow, replay, actuation, qualification, training
Next step: commit, push, confirm remote, then perform fresh profile/lease/discovery/holder preflight and the one decisive bracket
```

### 2026-07-11 - Brief 059 PI0.5 training-support semantics correction verified offline

```text
Current task: T16.5c
State: in_progress; Brief 059 verified and remotely preserved; live gate closed
Completed: versioned v2 fixture artifact; exact nine-vector training-statistic binding; mean/std, bin, quantile, and observed-min-max recomputation; pure isolated support module; explicit no-clamp/no-mode-switch contract
Evidence: implementation f6b6c08; artifact b20e0782...; runtime 1642f75c...; normalizer 8dc4c304...
Verification: 175 focused tests in .mujoco_venv; 175 in pinned LeLab runtime; exact writers/gates; compilation/privacy/diff checks; 374 broad tests in 86.332 seconds
Correction: [-1,1] is a textual discretizer reference, not a hard input domain; wrist_flex alone is outside observed training min-max and q01-q99; gripper is within q01-q99 and min-max support
Parity: fixture input, prompt, bins, state, preprocessor tensors, tokens, model images/masks, model-call contract, action/queue contract, and frame evidence are byte-identical to Brief 058
Authority gained: fixture_pi05_training_support_audit_conformant only beyond the existing fixture tensor-parity capability
Authority withheld: real reviewed input, static_pose_bracketed_observation, policy_shadow_input_valid, model/weight load, inference, shadow, replay, hardware, actuation, qualification/transfer, promotion, training
Hardware: none; current parent remains live-ineligible
Training lock: closed
Next step: fresh hardware-supervised on-request parent, finite run window, separate reviewed live gate, fresh lease/discovery/all-alias zero-holder proof; apply v2 support audit before policy shadow
```

### 2026-07-11 - Brief 058 fixture PI0.5 model-ready tensor parity verified offline

```text
Current task: T16.5c
State: in_progress; Brief 058 verified and remotely preserved; live gate closed
Completed: four deterministic complete PNGs; signed top/wrist role and highest-frame selection; calibrated q_after; exact CPU checkpoint processor and tokenizer; exact 224x224 model images/masks; token, prompt, tensor, action-horizon, and queue-reset hashes/contracts
Evidence: implementation 77724e1; artifact configurations/robot_lab/pi05_fixture_model_ready_tensor_parity.json; identity 559b9dbd...; runtime identity 4c89ca10...
Verification: 153 focused tests in .mujoco_venv; 153 in pinned LeLab runtime; exact tensor writer; Brief 056/057 writers; static fixture; compile/privacy/path/diff checks; 352 broad tests in 82.674 seconds
Finding (superseded by Brief 059): wrist_flex and gripper exceed mean±std, but only wrist_flex is outside observed training support; [-1,1] is not a hard validity domain for this serialized MEAN_STD checkpoint
Adversarial: source/gate/static-result substitution; fixture-live relabeling; camera/frame/PNG/state/task/token/tensor/mask/action/horizon/queue drift; false model/weight/network/hardware/inference/replay claims; runtime/path/privacy violations
Authority gained: fixture_pi05_model_ready_tensor_parity_conformant only
Authority withheld: real reviewed-input bundle, accepted live policy input, static_pose_bracketed_observation, policy_shadow_input_valid, model/weight load, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio, reconnect, write, torque, or motion; current parent remains live-ineligible
Training lock: closed
Next step: fresh hardware-supervised on-request parent, finite run window, separate reviewed live gate, fresh lease/discovery/all-alias zero-holder proof; no hardware in this parent
```

### 2026-07-11 - Brief 057 PI0.5 reviewed-input issuance gate verified offline

```text
Current task: T16.5c
State: in_progress; Brief 057 verified and remotely preserved; live gate closed
Completed: strict signed schemas and composition gate for future live-session acceptance, stable-camera-to-top/wrist role binding, and exact reviewed task prompt; exact source/session/issuer/review-record/validity/evidence-class consistency; fixture/production separation
Evidence: implementation 44dd871; artifact configurations/robot_lab/pi05_reviewed_inputs.blocked_missing_reviewed_inputs.json; schema scenesmith.pi05_reviewed_input_gate.v1; identity 0f6362f6...; all three input slots absent
Verification: 123 focused tests in .mujoco_venv; 123 in pinned LeLab runtime; Brief 056 and Brief 057 writers/verifiers in both runtimes; py_compile; whitespace/privacy/source/diff checks; 322 broad tests in 69.292 seconds
Adversarial: self-signed authority and extra-field escalation; source/issuer/scope/subject/session/review-decision drift; future/expired/boolean/oversized validity; manifest substitution; fixture/production mixing; partial bundles; camera identity/role/model ambiguity; numeric-index/raw-identity leakage; missing private-review hash; task whitespace/underscore/multiline/control/Unicode-normalization/hash drift; review-record path/hash/marker and input path alias substitution
Real inputs created: none; no live-session acceptance artifact, stable-camera role assignment, or reviewed task prompt exists
Authority gained: pi05_reviewed_input_issuance_gate_conformant only
Authority withheld: pi05_reviewed_input_bundle_valid, accepted_live_policy_input, static_pose_bracketed_observation, policy_shadow_input_valid, model/tokenizer/processor construction, model-weight load, preprocessing, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, model weight, optimizer, or paid compute
Training lock: closed
Next step: separately reviewed offline fixture preprocessing conformance or later real reviewed inputs; production preprocessing and live gate remain closed
```

### 2026-07-11 - Brief 056 PI0.5 preprocessing source contract verified offline

```text
Current task: T16.5c
State: in_progress; Brief 056 verified and remotely preserved; live gate closed
Completed: deterministic signed source contract for the exact PI0.5 executable files, cached checkpoint processor and tokenizer revisions, six-wide normalizer statistics, physical coordinate semantics, prompt template, and sole CUDA-to-CPU preprocessing override
Evidence: implementation fd49820; artifact configurations/robot_lab/pi05_policy_input_preprocessing.blocked_missing_inputs.json; schema scenesmith.pi05_preprocessing_source_contract.v1; identity f6b21668...; checkpoint revision 84b551af...; tokenizer revision 35e4f464...
Verification: 114 focused tests in .mujoco_venv; 114 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture/dependency/source-contract verifiers in both runtimes; py_compile; whitespace/privacy/source/diff checks; 313 broad tests in 70.328 seconds
Adversarial: executable source and runtime drift; cache revision/escape/file and ancestor alias substitution; checkpoint config/order/device drift; safetensors malformed header/offset/overlap/gap/boolean/non-finite/wrong-width/nonpositive/fractional statistics; tokenizer/coordinate drift; fixture/live relabeling; blocker, camera-role, task, acceptance, and authority fabrication
Blocked inputs: accepted_live_session_review_decision; reviewed_stable_camera_role_binding; reviewed_task_prompt
Authority gained: pi05_policy_input_preprocessing_source_contract_conformant only
Authority withheld: accepted_live_policy_input, static_pose_bracketed_observation, policy_shadow_input_valid, model/tokenizer/processor construction, model-weight load, preprocessing, inference, policy shadow, MuJoCo replay, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, model weight, optimizer, or paid compute
Training lock: closed
Next step: separate fixture-only reviewed-input issuance gate; production preprocessing and live gate remain closed
```

### 2026-07-11 - Brief 055 redacted live-session review manifest verified offline

```text
Current task: T16.5c
State: in_progress; Brief 055 verified and remotely preserved; live gate closed
Completed: complete historical private-success/receipt/source re-verification before deterministic redaction; exact candidate-pending-review schema; private-path-free source, drift, timing, frame, holder, and lifecycle summaries; exclusive session-named tracked writer with reread
Evidence: implementation 411e5cc; schema scenesmith.static_pose_live_session_review_manifest.v1; no actual live manifest instance written or accepted
Verification: 107 focused tests in .mujoco_venv; 107 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture source verifiers; py_compile; duplicate-dict/privacy/source/diff checks; current parent live-profile negative proof; 306 broad tests in 69.782 seconds
Adversarial: failure artifact and fixture/live relabeling; contract/profile/result/static-source/private-evidence/receipt/reference/root substitution; source and manifest authority escalation; raw path/report/identity/position leakage; field drift; output escape/wrong name/parent alias/overwrite/corruption; boolean operation count and frame index
Authority gained: redacted_static_pose_live_candidate_session_review_conformant only
Authority withheld: actual live review manifest, live candidate acceptance, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: fixture-only PI0.5 policy-input preprocessing source contract; live gate remains closed
```

### 2026-07-11 - Brief 054 fail-closed live-session orchestrator verified offline

```text
Current task: T16.5c
State: in_progress; Brief 054 verified and remotely preserved; live gate closed
Completed: one production entry point that reverifies the active profile, complete candidate contract, new private destination, and exact one-shot factories before session start; exactly-one immutable private outcome; candidate result withholding; signed candidate-only receipt
Evidence: implementation ce7a794; receipt schema scenesmith.static_pose_live_session_receipt.v1; private-reference digest plus contract/profile/result/evidence/root linkage; ancestor-symlink hardening
Verification: 101 focused tests in .mujoco_venv; 101 in pinned LeLab runtime; all execution/candidate/camera/calibration/static-fixture source verifiers; py_compile; duplicate-dict/diff checks; current parent live-profile negative proof; 300 broad tests in 92.360 seconds
Adversarial: profile/contract/destination/factory preflight rejection; private destination reuse and ancestor alias; candidate and cleanup error groups; failed or regressed outcome clocks; success/failure build, verify, write, and reference failures; receipt build/verification failure; contract/profile/result/evidence/reference/authority/time substitution; no retry or second write
Authority gained: fail_closed_static_pose_live_session_orchestrator_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline redacted candidate-session review manifest; live gate remains closed
```

### 2026-07-11 - Brief 053 live-execution interlocks verified offline

```text
Current task: T16.5c
State: in_progress; Brief 053 verified and remotely preserved; live gate closed
Completed: safe owner-interactive project default plus separate hardware/offline profiles; active-turn-context and explicit doctor cross-check; full-contract/profile-gated one-shot Feetech and exact-name FFmpeg factories; candidate result v2 hardware-profile linkage; fixed exclusive content-addressed private success/failure evidence
Evidence: implementation d76baf5; project/hardware/offline profile hashes 977e1b42.../dfce70f4.../76c188c5...; FFmpeg 8.0.1 / 0a96da27...; hardware profile schema v1; candidate result v2; private success/failure v1
Verification: 90 focused tests in .mujoco_venv; 90 in pinned LeLab runtime; matching source/profile/Feetech/FFmpeg verifiers; py_compile; duplicate-dict/source/diff checks; current parent live-profile negative proof; 289 broad tests in 73.993 seconds
Adversarial: child config cannot mask parent never policy; cross-thread/stale/synthetic/re-signed/changed-during-capture runtime evidence rejects; profile symlink/config drift rejects; unpinned Feetech/path/protocol/alias drift rejects; camera identity/mode/frame/binary drift rejects; factory reuse rejects; result/profile substitution and success/failure relabeling reject; private session reuse, symlink, path escape, and content drift reject
Authority gained: pinned_static_pose_live_factory_spec_conformant, private_static_pose_live_candidate_evidence_conformant, and hardware_supervised_runtime_profile_validator_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Current runtime: live-ineligible because persisted active turn_context approval_policy is never; checked-in profile changes do not alter the running parent
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline fail-closed production-session orchestrator and exactly-one private artifact path; live gate remains closed
```

### 2026-07-11 - Brief 052 source-bound static-pose candidate verified offline

```text
Current task: T16.5c
State: in_progress; Brief 052 verified and remotely preserved; live gate closed
Completed: fixed production/fixture contract and result classes; exact project-state gate snapshot, lease, follower USB/all-alias, stable-camera fresh-index, calibration/static-source, operation-count, timing, and no-write lifecycle binding; candidate-only production result
Evidence: implementation 79eee89; verification follow-up 2c0b903; contract/result schemas scenesmith.static_pose_live_candidate_contract.v1/scenesmith.static_pose_live_candidate_result.v1; accepted discovery b57fbec8...; follower USB c5bd66ff...; stable cameras 69d55167... and 9931d030...
Verification: 77 focused tests in .mujoco_venv; 77 in pinned LeLab runtime; accepted private-discovery source resolver in both runtimes; manifest/profile/static/source verifiers; py_compile; safety/privacy/diff/JSON checks; 276 broad tests in 72.567 seconds
Adversarial: fixture/live evidence-class re-signing; stale or consumed gate; scope/session/window/review drift; expired lease; project-state digest drift; follower USB/alias/path substitution; stable-camera ambiguity/index churn/mode drift; holder/lifecycle/count/timing/pose drift; write/torque/motion/unexpected-operation audit; constructor/primary/release/close/post-holder failure preservation
Authority gained: static_pose_live_candidate_contract_valid and source_bound_static_pose_live_candidate_runtime_conformant only
Authority withheld: live candidate result, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Live prerequisites missing: fresh finite run window; actual hardware_supervised_on_request/on-request runtime; separate reviewed remote gate transition; fresh owner-presence lease; fresh discovery and all-alias zero-holder snapshots
Next step: separate offline exact Feetech/FFmpeg factory, immutable private evidence, and execution-profile validator slice; live gate remains closed
```

### 2026-07-11 - Brief 051 stable camera identity binding verified offline

```text
Current task: T16.5c
State: in_progress; Brief 051 verified and remotely preserved; live gate closed
Completed: manifest v5 migration from exact accepted v4/private evidence; full capture-selection digest retained; stable name/unique-ID/model-ID/input-mode digest excludes only numeric index; calibration/static-pose/runtime source chain regenerated under v2 bracket schemas
Evidence: implementation bff160d; private 125de28f... unchanged; manifest 5218c3bd.../file 4311ffc2...; stable cameras 69d55167... and 9931d030...; profile 24db6f24...; contract/observation/result 7260be3e.../9ad35d18.../6b40e275...
Verification: 67 focused tests in .mujoco_venv; 67 in pinned LeLab runtime; four offline artifact/source verifiers; py_compile; privacy/diff/JSON checks; 266 broad tests in 79.568 seconds
Adversarial: numeric index churn preserves only stable digest; name/unique-ID/model-ID/mode churn changes it; malformed/duplicate/re-signed digests reject; v4 compatibility grants no stable capability and cannot satisfy pinned v5 consumers; private file refs rehashed; path traversal and arbitrary migration sources rejected
Authority gained: stable_camera_identity_binding_valid only; prior calibration and fixture capabilities preserved on regenerated identities
Authority withheld: live bracket/permit, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline source-bound live-candidate contract/runner, then another review before any live-gate transition
```

### 2026-07-11 - Brief 050 injected static-pose runtime verified offline

```text
Current task: T16.5c
State: in_progress; Brief 050 verified and remotely preserved; live gate closed
Completed: source-verified contract entry; signed pre/post all-alias holder checks; exact construct/connect/q_before/two-camera/q_after/no-torque-close sequence; strict global monotonic clock; fixture transport and camera audits; nested observation/evaluation; exception grouping and cleanup
Evidence: implementation 4f75a7a; runtime schema scenesmith.static_pose_bracket_runtime_result.v1; fixture_static_pose_bracket_runtime_conformant only
Verification: 27 focused contract/runtime tests in .mujoco_venv; 27 in pinned LeLab runtime; py_compile; privacy/diff checks; 265 broad tests in 84.573 seconds
Adversarial: live-adapter refusal before connect; construction/connect/before/after read failure; camera open/read/release and paired failures; close plus holder failure; nonzero holders; audit writes/torque/motion/unexpected operations; camera semantics/property writes/continuous capture; bus drop; clock regression; pose drift; resigned authority/holder/lifecycle/nested evidence
Authority gained: fixture_static_pose_bracket_runtime_conformant only
Authority withheld: live candidate/permit, static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, qualification/transfer, promotion, training
Hardware: none; no discovery/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, MuJoCo, optimizer, or paid compute
Training lock: closed
Next step: separate offline source-bound live-candidate contract and runner, then another review before any live-gate transition
```

### 2026-07-11 - Brief 049 static-pose bracket contract verified offline

```text
Current task: T16.5c
State: in_progress; Brief 049 verified and remotely preserved; live gate closed
Completed: exact six-joint q_before/camera/q_after contract; profile-based degree/percent conversion; 0.5-degree/0.5-percent drift limits; strict monotonic enclosure; five-second bracket cap; exact no-write lifecycle counts; two accepted camera identities/modes; all-alias holder and no-torque teardown requirements
Evidence: contract 90e7baea43ebc059c09ef45b615c5808cf74abbbab87948a23536666acb43ceb; fixture observation 84d0aa12...; fixture result 6ebb9bd6...; implementation 4fd1f3a remote
Verification: 11 focused tests in .mujoco_venv; 11 focused tests in pinned LeLab runtime; independent fixture/profile rebuild; py_compile; privacy/diff checks; 249 broad tests in 75.655 seconds
Adversarial: source/tolerance/authority substitution; extra observation/nested fields; missing/duplicate/wrong identities; boolean/noninteger/out-of-range positions; body/gripper drift; time order/duration; camera identity/mode/dimension/hash; writes/torque/motion/count drift
Authority gained: static_pose_bracket_contract_valid and fixture_static_pose_bracket_conformant only
Authority withheld: real static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, physical qualification/transfer, promotion, training
Hardware: none; no enumeration/open, serial/camera/Studio access, reconnect, write, torque change, motion, policy, simulation replay, optimizer, or paid compute
Training lock: closed
Next step: separate offline fake-transport integration into the bounded live orchestrator, followed by independent review before any live-gate reconsideration
```

### 2026-07-11 - Overnight authority/twin run closeout

```text
State: scheduled closeout after the 11:44:07 no-new-major-slice cutoff; T16.5c remains in progress
Verified tasks: T16.2b-A central composer; T16.4b production compiler on fixture evidence; T16.2b computed qualification on fixture evidence; T16.5a offline no-write conformance; T16.5b live read-only census/capture
Latest partial: Brief 048 signed calibration profile b360b4f6... verified and remote at 700be05; canonical closeout remote through 7100c1c
Accepted physical labels: live_read_only_census_observed; physical_observation_capture
Authority withheld: synchronized/policy-valid observation, policy_shadow, motion, physical qualification/transfer, promotion, training
Safety: live gate closed; training lock closed; follower remained virtually disconnected with torque reported off; no motion command was sent
Remaining: static-pose bracket and coordinate validation; PI0.5 preprocessing/shadow; matched MuJoCo replay; only then separately gated T16.6 permit work
Next: open one offline static-pose-bracket/coordinate-contract brief in a new session; do not inherit a live session or motion permit
```

### 2026-07-11 - Brief 048 signed calibration profile verified offline

```text
Current task: T16.5c
State: in_progress; Brief 048 verified and remotely preserved; live gate closed
Completed: strict parsing of exactly six named joints/IDs; signed STS3215 homing-offset and raw-range bounds; drive mode zero; live model/firmware binding; body degree normalization; gripper 0=closed and 100=open semantics
Evidence: profile b360b4f60077846c62128fe4d4cc33d1ee4e6e72aa7831fcb7c6706e6b6599b4; calibration 192404b6.../770 bytes; manifest eff3c824.../file cd4120f0...; servo digest 66e9d363...; commit 700be05 remote
Verification: 6 focused adversarial tests; offline artifact rebuild; py_compile; git diff check; 238-test authority/twin regression in 87.588 seconds
Adversarial: missing/extra/duplicate/wrong joint identity; booleans/nonintegers; inverted/out-of-domain ranges; invalid homing offset/drive mode; calibration or manifest substitution; resigned normalization/polarity/global-authority drift
Authority gained: local calibration_profile_semantically_valid only
Authority withheld: static_pose_bracketed_observation, policy_shadow_input_valid, policy_shadow, actuation, physical qualification, transfer, promotion, training
Hardware: none; no serial/camera/Studio access, reconnect, write, torque change, motion, policy inference, optimizer, or paid compute
Training lock: closed
Next step: close out the run, then design the static-pose-bracket and coordinate-validation slice before any preprocessing or shadow inference
```

### 2026-07-11 - T16.5b attempt 006 accepted

```text
State: verified; live gate closed at 2026-07-11T11:24:24-05:00
Discovery/contract: b57fbec8... / cf1ad99c...; fresh lease 3d9494b6...; RealSense uyvy422 640x480@30 and C922 yuyv422 640x480@30
Servo: 54 reads, zero retries/writes/torque changes/motion; all six Torque_Enable=0; no-torque close
Camera: four PNGs, all decoded 640x480 and exact-mode matched; two finite subprocesses; release/wait success; no stderr, terminate, kill, or residual process
Ownership: both signed serial aliases [0,0] before and after; snapshot b33a7cc0...
Evidence: tracked manifest eff3c824.../file cd4120f0...; private 125de28f.../file 02a264bd...; all bundle refs independently rehashed
Labels: live_read_only_census_observed; physical_observation_capture
Limits: sequential host receive intervals only; not synchronized, not policy-shadow-input-valid, not physical qualification, not motion authority
Next: T16.5c offline parsed calibration, static-pose bracket design/capture gate, PI0.5 preprocessing/shadow, matched MuJoCo replay; no actuation
```

### 2026-07-11 - Brief 047 signed 640x480 mode floor verified offline

```text
Current task: T16.5b
State: in_progress; Brief 047 verified offline; live gate closed for separate review
Selection: signed modes must be at least 640x480 and support integer 30 fps within 0.01; then choose smallest area and reviewed pixel-format priority; no default or cross-camera fallback
Actual discovery regression: C922 yuyv422 640x480@30; RealSense uyvy422 640x480@30; sub-floor 160x90 and 424x240 excluded
Evidence: e68068a remote; 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests in 71.477 seconds; actual discovery selection; offline/compile/diff checks
Hardware: none during Brief 047; live gate closed; no discovery/open, Studio request, reconnect, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical closeout, then separate final-session gate decision only if safe window remains
```

### 2026-07-11 - Brief 046 exact output dimensions verified offline

```text
Current task: T16.5b
State: in_progress; Brief 046 verified offline; live gate closed; Brief 047 active offline
Completed: named FFmpeg capture rejects parsed PNG dimensions that differ from signed mode before frame return; captured-frame/private-success and manifest layers independently recheck exact dimensions
Actual evidence: corrected manifest builder rejects attempt-005 private candidate ebb4934c... for 424x240-to-640x480 camera-1 drift
Verification: 6eb5f89 remote; 53 focused tests; 33 LeLab-runtime camera tests; 232 broad tests in 71.943 seconds; both offline verifiers; actual candidate rejection; pycompile; authority/privacy/diff checks
Hardware: none during Brief 046; live gate closed; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, optimizer, or paid compute
Remaining practical gap: deterministic smallest-area selection chose a signed 424x240 RealSense mode that live capture did not honor; both cameras have signed 640x480@30.000030 alternatives
Training lock: closed
Next step: Brief 047 signed 640x480-minimum selection offline
```

### 2026-07-11 - T16.5b live attempt 005 rejected; output-dimension drift

```text
Current task: T16.5b
State: in_progress; live gate closed; Brief 046 active offline
Discovery: v2 session t16-5b-20260711-1105-cdt; identity b8b11e74...; 209 C922 modes and 26 RealSense modes; zero devices opened during metadata discovery
Contract: v3 f76ea66f...; lease 4680d13a...; camera 0 yuyv422 160x90@30; camera 1 yuyv422 424x240@30
Servo/holder safety: 54 reads, zero retries/writes/torque changes/motion; all six Torque_Enable=0; no-torque close; both signed aliases [0,0] before and after; no ffmpeg process
Candidate capture: four valid PNGs; camera 0 observed 160x90 and matched; camera 1 observed 640x480 and contradicted signed 424x240 mode
Verifier gap: current v4 private/manifest verifier accepted the mismatched dimensions; post-run same-agent audit rejected the session
Evidence: private candidate ebb4934c.../file c341fdf3... retained ignored; candidate manifest 0d7b4400.../file 095ea665... removed; accepted proof labels []
Forbidden effects: no reconnect, Studio POST, signal, write, torque change, motion, policy, optimizer, paid compute, or physical qualification
Training lock: closed
Next step: canonical rejection closeout, then Brief 046 exact output-dimension enforcement offline
```

### 2026-07-11 - One fresh discovery-v2/contract-v3 session gated

```text
Current task: T16.5b
State: in_progress; one-session gate effective only after scoped transition commit is confirmed on origin
Window: 2026-07-11T11:04:00-05:00 through 2026-07-11T11:34:00-05:00; session limit one; fresh five-minute owner-presence lease required
Scope: fresh discovery v2 with metadata-only per-camera supported modes; zero holders across both signed aliases; contract v3 exact per-camera input modes; 54-read six-servo census with all Torque_Enable=0; no-write close; zero holders; two finite exact-name PNG frames per pinned camera; stable rediscovery and v4 evidence finalization
Failure: any mismatch rejects, writes no success manifest or proof label, cleans up, and immediately recloses the gate; no retry implied
Forbidden: reconnect, Studio POST, signal, register/configuration write, torque transition, motion, policy actuation, qualification, optimizer, or paid compute
Evidence: implementation 820a40f; canonical closeout a6da4b4; reviewer 067; disconnect proof 627de4fd...; all-alias holder snapshot b33a7cc0...
Training lock: closed
Next step: remotely confirm transition, then execute exactly once and reclose
```

### 2026-07-11 - Brief 045 signed per-camera input modes verified offline

```text
Current task: T16.5b
State: in_progress; Brief 045 verified offline; live gate closed for separate review
Discovery: v2 binds exact name/unique ID/model ID plus normalized finite pixel format, dimensions, and frame-rate ranges from AVCaptureDevice format metadata without AVCaptureSession or frame streaming
Selection: smallest frame area, then reviewed pixel-format priority; integer 30 fps must fall within signed range using only 0.01-fps AVFoundation matcher tolerance
Contract/command: v3 selects each camera from its own signed modes; exactly one -pixel_format, -video_size, and -framerate precedes each AVFoundation input
Evidence: diagnostic v3, private success v4, private failure v4, and tracked manifest v4 bind exact input mode; attempt-003 v2 and attempt-004 v3 private failures still verify
Adversarial: empty/unknown/duplicate/non-finite modes, identity mismatch, legacy discovery reuse, cross-camera substitution, malformed mode, coordinated resigned contract/diagnostic/result substitution, command reordering/duplication, stderr/nonzero/PNG/cleanup failures
Verification: 820a40f remote; 52 focused tests; 32 LeLab-runtime camera tests; 231 broad tests in 74.938 seconds; both offline verifiers; Swift typecheck; legacy artifact verification; pycompile; authority-surface/privacy/diff checks
Hardware: none during Brief 045; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical closeout, then separate one-fresh-session live-gate review
```

### 2026-07-11 - T16.5b live attempt 004 rejected; pixel-format cause retained

```text
Current task: T16.5b
State: in_progress; live gate closed; Brief 045 active offline
Discovery: session t16-5b-20260711-1036-cdt; identity 2e63871a...; four serial candidates and two exact-name cameras; zero devices opened during discovery
Contract: v2 b9b3c7ec...; five-minute lease f993a7c7...; integer 30 fps; two frames per pinned camera
Servo result: f5c6d17e...; 54 reads, zero retries/writes/torque changes/motion; six model 777 servos; all six Torque_Enable=0; one successful no-torque close
Serial ownership: both signed paths [0,0] before open, after close, and after failure; snapshot b33a7cc0...
Camera failure: first exact-name camera; return 0; strict subprocess_stderr rejection; 339 stderr bytes hash 80b01de5...; 5,244,174 stdout bytes hash 11bcb1c0...; yuv420p unsupported; supported list uyvy422/yuyv422/nv12/0rgb/bgr0
Private evidence: v3 identity 785241af...; file 305c42fb...; 40,640 bytes; complete contract/result independently verified; diagnostic bd722dd7...
Cleanup: release succeeded; no ffmpeg process; no success bundle, tracked manifest, proof label, reconnect, Studio POST, signal, write, torque change, motion, policy, optimizer, or paid compute
Training lock: closed
Next step: canonical rejection closeout, then Brief 045 offline per-camera supported-mode contract
```

### 2026-07-11 - One fresh v2-contract live session gated

```text
Current task: T16.5b
State: in_progress; one-session gate effective only after scoped transition commit is confirmed on origin
Window: 2026-07-11T10:33:00-05:00 through 2026-07-11T11:13:00-05:00; session limit one; fresh five-minute owner-presence lease required
Scope: fresh discovery; zero holders across both signed aliases; v2 exact 30-fps contract; 54-read six-servo census with all Torque_Enable=0; no-write close; zero holders; two finite exact-name PNG frames per pinned camera; stable rediscovery and evidence finalization
Failure: any mismatch rejects, writes no success manifest or proof label, cleans up, and immediately recloses the gate; no retry implied
Forbidden: reconnect, Studio POST, signal, register/configuration write, torque transition, motion, policy actuation, qualification, optimizer, or paid compute
Evidence: implementation 4ae0521c; canonical closeout cee8240; reviewer 064; disconnect proof 627de4fd...; all-alias holder snapshot b33a7cc0...
Training lock: closed
Next step: remotely confirm transition, then execute exactly once and reclose
```

### 2026-07-11 - Brief 044 explicit camera mode verified offline

```text
Current task: T16.5b
State: in_progress; Brief 044 verified offline; live gate closed for separate review
Completed: v2 live contract binds 30 fps; ffmpeg command places one -framerate 30 before -i; v2 diagnostic and v3 private/tracked evidence bind mode; v3 failure embeds full contract and servo result; legacy v1/v2 verification retained
Basis: attempt-003 diagnostic advertises 30.000030; installed ffmpeg 8.0.1 default is ntsc; AVFoundation source matches rates within 0.01 fps, so integer 30 differs by 0.000030
Evidence: 4ae0521c remote; 50 focused tests; 30 LeLab-runtime camera tests; 229 broad tests in 76.974 seconds; both offline verifiers; deterministic proof/fixture verification; legacy attempt-003 artifact verification; py_compile; diff check
Adversarial: missing/noninteger/non-30 contract mode; wrong/misordered command mode; audit drift; coordinated contract/result substitution; nonzero torque; missing full result; legacy compatibility
Hardware: none during Brief 044; no discovery/open, Studio request, reconnect, signal, write, torque change, motion, policy, training, or paid compute
Training lock: closed
Next step: canonical closeout, then separate one-fresh-session live-gate review
```

### 2026-07-11 - T16.5b live attempt 003 rejected; framerate cause retained

```text
Current task: T16.5b
State: in_progress offline; live gate closed; Brief 044 active
Session: t16-5b-20260711-1005-cdt; discovery 7a187d11...; contract 63979ed4...; lease 527ad754...
Census: 54 read successes; zero retries/writes/torque changes/motion; no-torque close success; pre/post/final holder counts [0,0]
Failure: first named-camera ffmpeg returned 251; diagnostic 482064ad...; stderr 13,548 bytes/64a8d5ff...; 29.970030 fps unsupported and 30.000030 advertised
Evidence: private rejection e7f8eb21.../6148b56e... retained; release success; zero ffmpeg processes; no success manifest; proof labels empty; physical_follower_commanded=false
Limitation: failure schema v2 binds servo result identity 2128192c... and counts but not full decoded servo/trace evidence
Safety: follower not reconnected; no Studio request, signal, write, torque transition, motion, policy, training, or paid compute
Training lock: closed
Next step: commit/push rejection; implement Brief 044 explicit 30 fps contract and full failure-servo evidence offline
```

### 2026-07-11 - Brief 043 live gate opened for one fresh session

```text
Current task: T16.5b
State: in_progress; live gate open after remote confirmation only; one-session limit; valid through 10:43 CDT
Prerequisites: 7ea26651 implementation and 37108426 canonical closeout remote; proof 627de4fd...; permit consumed; holder b33a7cc0... counts [0,0]; Torque_Enable trace gate verified offline
Allowed sequence: fresh metadata discovery; zero holders across canonical plus paired TTY; five-minute owner-presence lease; exact content-addressed no-write contract; six-servo census; no-write close; zero holders; finite named-camera batches; stable discovery; private bundle and tracked redacted manifest
Mandatory: all six Torque_Enable values zero; handshake false; disconnect disable_torque false; zero writes/motion; physical_follower_commanded=false; reclose gate on success or failure
Withheld: reconnect, motion, policy actuation, synchronized/policy-input-valid claim, physical qualification, training
Hardware: none during this state transition
Training lock: closed
Next step: commit/push/confirm transition, then execute exactly one fresh session
```

### 2026-07-11 - Brief 043 state-integrity gates verified offline

```text
Current task: T16.5b
State: in_progress; Brief 043 verified offline; live gate closed for a separate review commit
Completed: tracked/private disconnect proof; one-call permit consumed; canonical plus paired TTY holder enumeration and evidence binding; six-servo Torque_Enable read and trace-decoded evidence verification
Evidence: 7ea26651 remote; proof 627de4fd...; permit 85f91cea...; private a9941b84.../9b45502b...; all-alias holder b33a7cc0... counts [0,0]; census 28d087fe.../41526a67.../d58f0e8d...
Verification: 50 focused; 229 broad in 74.864 seconds; both offline runtime verifiers; fixture and disconnect-proof verifiers; py_compile; privacy scan; git diff --check
Hardware: none during Brief 043; no serial/camera open, Studio POST, reconnect, signal, write, torque change, motion, policy actuation, or training
Proof wording: disconnect evidence is honestly reconstructed; no accepted live census/camera label; sequential capture is not synchronized or policy-shadow-input-valid
Training lock: closed
Next step: separately review, commit, push, and confirm at most one fresh finite live-gate transition
```

### 2026-07-11 - Brief 042 verified; owner review hardens next live gate

```text
Current task: T16.5b
State: in_progress; Brief 042 offline verified; live gate closed
Completed: typed signed camera failure diagnostic; bounded sanitized stderr preview; full stream counts/digests; primary+cleanup preservation; atomic immutable private failure record; no success manifest/label path
Evidence: 2d1cd97; 24 dedicated tests; 40 combined census tests; 219 broad robot-lab tests; both offline verifiers; py_compile; git diff --check
Owner review: conditional continue; canonical disconnect artifact, consumed permit, all signed serial aliases, and per-servo Torque_Enable are hard prerequisites
Proof wording: sequential census then camera is finite physical camera capture only, not synchronized or policy-shadow-input-valid
Training lock: closed
Next step: Brief 043 offline implementation and review; no live reopen in this boundary
```

### 2026-07-11 - T16.5b live attempt 002 rejected; gate reclosed

```text
Current task: T16.5b
State: in_progress; live gate closed; attempt 002 rejected
Session: t16-5b-20260711-0904-cdt; discovery 7766ed1c...; contract 51467ec7...; lease 980b555c...
Reached: metadata discovery; exact contract verification; zero-holder precheck; read-only census; no-torque close; zero-holder postcheck; first exact-name camera batch
Failure: ffmpeg subprocess returned nonzero; production exception retained neither bounded stderr text nor digest, so cause is not yet mechanically classified
Cleanup: no ffmpeg process; follower disconnected/torque false; holder 4f53cda1... count 0; private bundle absent; tracked manifest absent
Proof labels: none; physical_follower_commanded=false
Training lock: closed
Next step: commit/push rejection, implement Brief 042 offline bounded diagnostic evidence, review remotely, then reconsider a new session
```

### 2026-07-11 - T16.5b live gate reopened for one fresh finite session

```text
Current task: T16.5b
State: in_progress; live gate open only for one fresh session
Prerequisites: b211562 remote; follower disconnected/torque false; holder 4f53cda1... count 0 at 09:01:09 CDT; T16.5a verified; owner present and resume authority explicit
Allowed: metadata-only discovery; five-minute owner-presence lease; exact content-addressed contract; one no-write census; two finite named-camera frames each
Mandatory guards: stable device/camera/calibration identity; zero holders before serial open and after close; handshake false; 48 allowlisted reads; disconnect disable_torque false; no configuration/torque/register writes; physical_follower_commanded=false
Withheld: proof labels until accepted evidence verifies; reconnect without no-motion proof; motion; policy actuation; physical qualification; training
Training lock: closed
Next step: commit/push this gate, confirm remote, then prepare and execute a brand-new session once
```

### 2026-07-11 - Virtual follower disconnect and zero-holder proof verified

```text
Current task: T16.5b
State: in_progress; exclusive follower ownership proven; live gate still closed
Operation: one POST /api/hardware/disconnect with {"role":"follower"}; call count 1; HTTP 200; response {"connected":false}; no retry
Postconditions: hardware d58a7549... follower disconnected/torque false; holder 4f53cda1... count 0; leader connected; safety 8c425d38... unchanged; routing 620cb845... unchanged; jobs 0
Writes: only the owner-authorized torque-disable inherent in follower disconnect; no motion, goal, leader, safety, routing, policy, or training operation
Authority gained: verified virtual follower disconnect; exclusive follower bus ownership
Authority withheld: live proof labels, motion, reconnect without no-motion proof, general register writes, physical qualification, training
Training lock: closed
Next step: commit/push this boundary; confirm remote; then separately review and open a fresh-session-only live gate
```

### 2026-07-11 - Owner-authorized virtual follower disconnect resumes T16.5b

```text
Current task: T16.5b
State: in_progress; live gate closed; prior blocked audit resolved by owner message
Completed: fresh branch/remote/dirty/status/holder revalidation; narrow disconnect plan; durable resume boundary
Evidence: 08:53:51 CDT holder 64230513... count 1; hardware 79f4ce89... follower connected/torque true; safety 8c425d38... armed; routing 620cb845... none; jobs 0
Authority: exactly one Studio follower disconnect call, including inherent torque-disable, plus response/status/zero-holder verification; later reconnect only if proven no-motion-safe
Withheld: motion command, leader disconnect, safety-route mutation, general register writes, policy actuation, physical qualification, training
Training lock: closed
Next step: commit/push this boundary; execute the exact disconnect once; fail closed unless response, status, and holder proof all agree
```

### 2026-07-11 - T16.5b blocked after third identical owner-authority audit

```text
Current task: T16.5b
State: blocked; stop sentinel active
Completed: third independent read-only holder/status audit; blocked-threshold review; durable owner choice packet
Evidence: 05:54:27 CDT holder 64230513... count 1; hardware 79f4ce89... follower connected/torque true; safety 8c425d38... armed; routing 620cb845... none; jobs 0; reviewer 054; manager 013
Blocked classification: missing_input at a proven human-authority boundary, repeated for three consecutive Goal turns
Forbidden while blocked: process signal, Studio disconnect/safety POST, serial/camera open, register write, torque change, motion, policy actuation, training
Unblock: owner manually disconnects follower, explicitly authorizes exact torque-release disconnect, or selects offline-only disposition
Training lock: closed
Next step: mark persisted Goal blocked and wait for owner choice
```

### 2026-07-11 - Studio reports torque on; disconnect choice escalated to owner

```text
Current task: T16.5b
State: in_progress; live gate closed; owner authority decision pending
Completed: read-only source audit of Studio shutdown/disconnect semantics; GET-only health/hardware/safety/routing/jobs status audit
Evidence: hardware hash 79f4ce89...; safety hash 8c425d38...; routing hash 620cb845...; follower connected true; follower torque true; safety armed true; running jobs 0; follower route none
Safety finding: SIGTERM does not call hardware disconnect/torque release; HTTP follower disconnect does release torque and is a motor-register write
Authority: neither process signal nor torque-changing endpoint was invoked
Remaining: owner manually disconnects follower, explicitly authorizes exact disconnect, or keeps Studio active and accepts offline-only continuation
Blockers: exclusive follower bus ownership cannot be established while Studio remains connected
Training lock: closed
Next step: present the exact three-way owner choice
```

### 2026-07-11 - Fresh serial-holder gate remains closed; owner decision required

```text
Current task: T16.5b
State: in_progress; live gate closed; owner decision pending
Completed: remote confirmation through c686ab6; fresh read-only holder check using the reviewed guard
Evidence: snapshot 642305133b602477840e31d756e52b11cf5d97e689eda15ae2741291ed47106c at 2026-07-11T05:47:27-05:00; holder count 1; serial device opened by check false
Authority: no process stop/signal has been performed; no force-kill authority requested or inferred
Remaining: owner choice on graceful Studio server stop; zero-holder verification; only then a separately recorded live-gate reopen decision
Blockers: one independent holder remains
Hardware state: no serial/camera open during the recheck
Training lock: closed
Next step: ask owner for narrow graceful-stop authority
```

### 2026-07-11 - Brief 041 offline correction reviewed; live gate remains closed

```text
Current task: T16.5b
State: in_progress; offline correction verified; live gate closed
Completed: stable exact-name/unique-ID camera binding; finite ffmpeg PNG batch parser; decompressed pixel/scanline validation; subprocess cleanup/evidence counts; pre-open/post-close zero-holder serial gate
Evidence: ea99ec9/66003d8/fd13bf6/01802a0; reviewer 053; 19 dedicated, 35 combined census, and 214 broad tests; both runtime offline verifiers; no hardware reopened
Authority: offline harness capabilities only; attempt 001 remains rejected; proof labels remain empty
Remaining: remote preservation; explicit owner resolution of the pre-existing Studio server; only then reconsider a new session/lease under the closed-by-default gate
Blockers: one pre-existing Studio server was last observed holding the follower serial device; capture code will now reject any holder before serial open
Hardware state: no new enumeration/open during Brief 041; historical attempt 001 remains rejected and closed
Training lock: closed
Next step: commit/push reviewer 053 and canonical state, confirm remote, then request owner direction for the independent holder while continuing offline
```

### 2026-07-11 - T16.5b live attempt 001 rejected; live gate closed

```text
Current task: T16.5b
State: in_progress offline; live gate closed
Completed: one bounded contract attempt reached post-close discovery and cleanup; failure containment; pre-existing serial holder identification; redacted camera-drift comparison
Evidence: contract 2102227c...; lease c9c9a88d...; AVFoundation camera-name set unchanged but index/name mappings swapped; Studio server started 2026-07-08 and predates attempt; reviewer 052
Accepted evidence: none; no private bundle, tracked manifest, live proof label, write, torque, motion, or physical qualification claim
Remaining: Brief 041 stable name/unique-ID-bound finite camera path; review/push; owner resolution of independent serial holder before another live open
Blockers: ephemeral numeric camera indexes; exclusive follower-bus ownership unproven
Hardware state: attempt process exited after cleanup and before evidence writing; pre-existing Studio server preserved untouched
Training lock: closed
Next step: commit/push the rejection boundary, then implement Brief 041 entirely offline
```

### 2026-07-11 - T16.5b metadata discovery and compatibility correction reviewed

```text
Current task: T16.5b
State: in_progress
Completed: metadata-only discovery; actual-OS optional-manufacturer compatibility correction; exact hashed follower/two-camera/six-joint-calibration resolution
Evidence: discovery 53440393...; follower hash 321be886...; camera-set hash 427eaa29...; calibration hash 192404b6...; correction b85a253; reviewer 051; 14 dedicated/30 combined/209 broad tests
Commit: b85a253 correction; review/canonical preservation pending
Remaining: push correction/reviewer; create short lease and exact execution contract; one bounded live read-only census/camera attempt
Blockers: none now; any remote, identity, lease, contract, source, model, telemetry, camera, or cleanup mismatch fails closed
Hardware state: metadata enumerated; serial ports opened 0; cameras opened 0; follower commanded false
Training lock: closed
Next step: commit reviewer 051 and canonical state, push/confirm the named remote, then prepare and inspect the exact private lease/contract
```

### 2026-07-11 - T16.5b offline live-readonly harness locally reviewed

```text
Current task: T16.5b
State: in_progress
Completed: bounded metadata-discovery, exact identity/lease contract, no-write bus, finite camera, private evidence, and redacted manifest harness reviewed offline
Evidence: implementation 16d24ea; reviewer 050; 14 dedicated, 30 combined census, and 209 broad tests; both .mujoco_venv and external/leLab offline verifiers; Black, py_compile, static no-write inspection, and diff checks
Commit: 16d24ea; review/canonical preservation pending
Remaining: commit and remotely preserve reviewer boundary; metadata-only discovery; exact lease/contract; one bounded read-only census/camera attempt
Blockers: no offline blocker; live open fails closed on any identity, calibration, lease, camera, source, or contract ambiguity
Hardware state: not enumerated and not opened
Training lock: closed
Next step: commit reviewer 050 and canonical state, push only the named branch, confirm remote, then run metadata discovery only
```

### 2026-07-11 - Corrected T16.5a remotely verified; T16.5b reopened

```text
Current task: T16.5b
State: in_progress
Completed: corrected T16.5a v2 protocol/source binding remotely preserved with reviewer 049
Evidence: local HEAD, origin tracking, and git ls-remote all matched 240729968ee1956cab489ea49501768156b16777; commits 5102422/eeb16e1 and reviewer 049 are ancestors; unrelated dirty baseline remains 232 paths
Commit: 5102422/eeb16e1 correction; 2407299 reviewer boundary
Remaining: offline live-adapter/discovery/camera/evidence tests, lease revalidation, then one bounded live read-only attempt
Blockers: none for offline implementation; live access fails closed on lease or identity ambiguity
Training lock: closed
Next step: execute Brief 039 offline gates before opening any device
```

### 2026-07-11 - T16.5a protocol/source correction locally reviewed

```text
Current task: T16.5a
State: in_progress
Completed: corrected protocol 0; v2 source-hash contract; independent protocol/baud/model/resolution/register/joint/lifecycle semantic parser; constants derived from verified semantics
Evidence: commits 5102422/eeb16e1; reviewer 049; 16 focused and 195 broad tests; contract 73652ffa...; trace 17921a5f...; result 4a83298b...
Commit: 5102422 and eeb16e1; review/remote preservation pending
Remaining: preserve correction and reviewer on origin, then reclose T16.5a and reopen Brief 039
Blockers: no offline blocker; all live hardware remains closed
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.5a reopened before live access

```text
Current task: T16.5a
State: in_progress
Completed: contained a protocol binding defect before any hardware enumeration or open
Evidence: reviewer 048; pinned Feetech DEFAULT_PROTOCOL_VERSION=0 and MODEL_PROTOCOL[sts3215]=0; fixture declared 1; source hashes 0460413c.../71f7f7be...
Commit: correction pending
Remaining: Brief 040 code/source binding, artifact regeneration, tests, review, and remote confirmation
Blockers: none for offline correction; T16.5b is closed
Training lock: closed
Next step: correct and mechanically bind the offline census to the pinned runtime
```

### 2026-07-11 - T16.5a remotely verified; T16.5b opened

```text
Current task: T16.5b
State: in_progress
Completed: T16.5a offline no-write census preflight remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched d002c8038ac1e393c5c92f4a2f215c961b408bf2; implementation f200087 and reviewer 047 are ancestors; unrelated dirty baseline remains 232 paths
Commit: f200087 implementation; d002c80 reviewer boundary
Remaining: offline live-adapter/discovery/camera/evidence tests, lease revalidation, then one bounded live read-only attempt
Blockers: none for offline implementation; live access fails closed on lease or identity ambiguity
Training lock: closed
Next step: execute Brief 039 offline gates before opening any device
```

### 2026-07-11 - T16.5a offline no-write census locally reviewed

```text
Current task: T16.5a
State: in_progress
Completed: code-pinned follower/six-servo fixture contract; narrow injected and recorded transports; complete ordered read lifecycle; bounded retry; dual-error cleanup; signed no-write trace/result; safe leader teardown
Evidence: implementation f200087; reviewer 047; 14 focused and 193 broad tests; contract 17e8c712...; trace 25cbac27...; result e7c0ecfc...; hardware_opened=false; physical_follower_commanded=false
Commit: f200087; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.5a and prepare the separately gated live read-only brief
Blockers: no offline blocker; live hardware remains closed until remote confirmation and lease revalidation
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.2b remotely verified; T16.5a opened offline

```text
Current task: T16.5a
State: in_progress
Completed: T16.2b mechanically computed qualification remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched 383557b0bdb1dc17725b4eac0db37d19c902b1c0; implementation 710960b and reviewer 046 are ancestors
Commit: 710960b implementation; 383557b reviewer boundary
Remaining: offline read-only transport/lifecycle preflight before any live discovery
Blockers: none for offline work; live hardware remains closed
Training lock: closed
Next step: execute Brief 038 using fake/recorded transports only
```

### 2026-07-11 - T16.2b mechanically computed qualification locally reviewed

```text
Current task: T16.2b
State: in_progress
Completed: code-pinned v2 metric rules; signed/content-addressed evidence and input; deterministic conservative aggregation; independent report recomputation; legacy caller-status closure; central-composer-only claims
Evidence: implementation 710960b; reviewer 046; 16 focused and 147 broad tests; spec eff5a15e...; input 5c942916...; report 7ed02c6e...; denial composition 41a4d731...; all global decisions withheld
Commit: 710960b; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.2b and start offline T16.5a
Blockers: no offline blocker
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.4b remotely verified; T16.2b opened

```text
Current task: T16.2b
State: in_progress
Completed: T16.4b deterministic numerical hardening remotely preserved with its same-agent review
Evidence: local HEAD, origin tracking, and git ls-remote all matched dbdd1ef019961cc6d7deba81f69a873c11efac5a; implementation 7d05629 and reviewer 045 are ancestors
Commit: 7d05629 implementation; dbdd1ef reviewer boundary
Remaining: mechanically generated and independently recomputed qualification results; offline T16.5a follows
Blockers: none for offline T16.2b
Training lock: closed
Next step: execute Brief 037
```

### 2026-07-11 - T16.4b numerical hardening locally reviewed

```text
Current task: T16.4b
State: in_progress
Completed: deterministic scale-normalized symmetric eigensolver; fixed iteration bound; eigenvector residual and orthogonality checks; scale-relative symmetry/PSD/triangle tolerances; finite-intermediate rejection; deterministic NumPy corpus
Evidence: implementation 7d05629; reviewer 045; 17 focused and 131 broad tests; 20,000 extreme-scale eigensystems and 2,000 randomized physical tensors; product identities unchanged; every global composer decision withheld
Commit: 7d05629; review/remote preservation pending
Remaining: preserve implementation and reviewer evidence on origin, then close T16.4b and start T16.2b
Blockers: no offline blocker
Training lock: closed
Next step: commit reviewer evidence, push only the named branch, and confirm the remote
```

### 2026-07-11 - T16.4b production compiler locally reviewed

```text
Current task: T16.4b
State: in_progress
Completed: rooted hierarchical exact-cover BOM; six production source modes; explicit units/calibration/metrology; content-addressed evidence; full-precision transforms/aggregation; fixture-only mixed-source artifact; current arm remains blocked
Evidence: implementation a93ff05; reviewer 044; 21 focused and 122 broad tests; fixture fe9dbd5468a606019db735dc8664c05d5fc207d94bdcbc84243f58cfa98f869f -> b8d7c5d287051aa863c3ef08597deefb9dd7685ad2c89d820456f92491fef25d; composer withholds all global decisions
Commit: a93ff05; remote preservation pending
Remaining: deterministic eigensolver convergence/residual and scale-relative numerical hardening before T16.4b closes
Blockers: remote preservation pending; no offline implementation blocker
Training lock: closed
Next step: preserve implementation/review on origin, then execute numerical-hardening brief
```

### 2026-07-11 - Owner-supervised physical proof steering

```text
Current task: T16.4b
State: in_progress
Completed: recorded ten-hour window extension and staged T16.5a/T16.5b/T16.5c/T16.6 authority; final operator confirmation granted for one exact initial micro-motion permit
Evidence: explicit owner steering while physically present beside the desk-mounted SO-101; persisted Goal remains active
Commit: pending scoped steering commit
Remaining: finish T16.4b and T16.2b before any T16.5a; no live hardware before verified T16.5a; no write/motion before exact session permit gates
Blockers: none for offline continuation
Training lock: closed
Next step: preserve steering on origin, then resume Brief 033
```

### 2026-07-11 - T16.2b-A central authority composition verified

```text
Current task: T16.4b
State: in_progress
Completed: versioned central authority contract and fail-closed composer; assembly-inertials v2 local-capability boundary; non-authorizing deterministic fixture decision
Evidence: implementation c0b9629; reviewer 043; 101-test broad gate; contract identity 6d04b20547a9391c4e695b5a337ee292410a2a13a8a3efdf34cb7033feda6ba1; denied composition d1206c5c710a280e4f7c5c448fd9ba59793b9850c2e9fd1bf962999ec82bc8ab; origin confirmed through e1d59ca
Commit: c0b9629 implementation; e1d59ca review evidence
Remaining: production hierarchical measured-inertial compiler, mechanically computed qualification, and offline census conformance
Blockers: none for offline T16.4b
Training lock: closed
Next step: resume Brief 033 without granting any global readiness from inertial output
```

### 2026-07-11 - Authority-composer-first redirect and overnight launch

```text
Current task: T16.2b-A
State: in_progress
Completed: accepted T16.4b strict artifact sub-slice as valid partial progress; recorded the central-composer architectural boundary; installed single-agent overnight instructions and launch prompt
Evidence: reviewer decision 042; Brief 034; AGENTS.md; .codex/config.toml; overnight-authority-twin-goal-loop.md
Commit: supplied by the scoped overnight-substrate commit containing this entry
Remaining: implement and verify T16.2b-A, resume production T16.4b, then T16.2b and offline T16.5
Blockers: none for offline continuation
Training lock: closed
Next step: implement Brief 034 in the separate top-level overnight Codex thread
```

### 2026-07-10 - T16.4b strict artifact and authority sub-slice

```text
Current task: T16.4b
State: in_progress
Completed: strict finite JSON/signing/reference layer; PSD and principal-moment inertia validation; unique measurement and exact prior graph checks; content-addressed synthetic evidence; explicit compilation/simulation/physical/promotion authority gates
Evidence: implementation commit 69df54d; reviewer decision 041; 35 focused tests; product CLI proves synthetic compilation succeeds while synthetic simulation-training authority fails
Commit: 69df54d
Remaining: production non-synthetic mixed-source measured intake, hierarchical BOM exact cover, explicit units/calibration, full-precision aggregation, golden fixture, and broad review
Blockers: none for offline continuation
Training lock: closed
Next step: continue brief 033 with the production mixed-source compiler path
```

### 2026-07-10 - T16.1b unified executable stack verified

```text
Current task: T16.4b
State: in_progress
Completed: T16.1b replaced split_runtime_unresolved with one exact LeRobot base plus tracked patch-set and routed collection, training, finalization, inference, and LeLab through a fail-closed stack identity
Evidence: implementation commit dca2b45; reviewer decision 040; stack identity c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4; 13 stack/lock, 13 twin, 24 structural, and 24 measured-inertial tests passed
Commit: dca2b45
Remaining: T16.4b, T16.2b, revised T16.5
Blockers: none for offline T16.4b
Training lock: closed
Next step: execute brief 033
```

### 2026-07-10 - External review reopens production-authority boundaries

```text
Current task: T16.1b
State: in_progress
Completed: preserved exact df9ed0a branch and dirty-worktree evidence; accepted prior T16.1, T16.2, and T16.4 results only as inventory/schema/synthetic scaffold evidence
Evidence: reviewer decision 039; origin/codex/pi05-autolearn-loop points at df9ed0a4d2212819382a4701a33c263f2cdee32e; local status, binary patch, and integrity-checked untracked archive written outside the repo
Commit: pending
Remaining: unify executable stack, harden production measured-inertial authority, compute qualification mechanically, then restart revised T16.5
Blockers: none for offline T16.1b
Training lock: closed
Next step: execute brief 032
```

### 2026-07-10 - Reviewer closeout T16.4 and open T16.5

```text
Current task: T16.5
State: in_progress
Completed: reviewer reran brief 030 and confirmed the bounded synthetic_test_only measured-inertial compiler now preserves the ready happy path while failing closed for exact-cover ambiguity, reused evidence, and invalid rotation/inertia inputs; T16.4 is accepted as verified
Evidence: reviewer decision 038; independent reruns reproduced 24 focused measured-inertial tests, 69 broad robot-lab tests, blocked real identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4, and synthetic ready identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d
Commit: pending
Remaining: first fake-bus/recorded-trace harness slice for a read-only servo census replay, then broader T16.5 fitting/qualification scaffolding
Blockers: none for offline continuation
Training lock: closed
Next step: execute brief 031 without opening hardware or claiming physical qualification
```

### 2026-07-10 - T16.4 synthetic ready negative matrix

```text
Current task: T16.4
State: in_progress
Completed: extended the bounded synthetic_test_only proof with explicit negative-matrix regressions for missing exact-cover atoms, duplicate active atom coverage, ambiguous multi-atom measurement selection, reused measurement evidence, invalid rotation matrices, and invalid inertia matrices; relaxed only the synthetic verifier precheck needed so incomplete-but-well-formed synthetic inputs fail through the exact-cover compiler path
Evidence: focused measured-inertial suite passed 24 tests including the six new negative cases; py_compile passed for measured_inertial_intake module/tests/CLI; live default --verify preserved blocked real identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; live default --verify --require-ready still exited nonzero with blocked_missing_measurements; live synthetic CLI write to /private/tmp/scenesmith-next-synthetic-ready.json still reached ready identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d; broad robot-lab gate passed 69 tests
Commit: pending
Remaining: reviewer confirmation that brief 030 fully closes T16.4, then begin T16.5
Blockers: none for offline continuation
Training lock: closed
Next step: reviewer rerun of the negative matrix and bounded CLI paths, then open the smallest fake-bus/recorded-trace harness slice
```

### 2026-07-10 - T16.4 synthetic ready happy path

```text
Current task: T16.4
State: in_progress
Completed: added a bounded synthetic_test_only measured-inertial fixture and ready compiler branch; proved deterministic golden aggregate mass/COM/full inertia, stable semantic ready identity under reordered synthetic input, and hard-refused writes to either checked-in real current-arm destination
Evidence: tests/fixtures/robot_lab/measured_mass/synthetic_complete.json identity 412825dfedd4c5b015b81a2f4d32d208e6d1dbd6de547a665a8f92005acf8388; live synthetic CLI output identity 9638e5abded29b948f0ef28b80e52e3ecd0a6adca58bb0e3d4899b984a64071d with mass 4.5 kg, COM [0.35, 0.283333333, 0.033333333], inertia [[0.073625, -0.053025, 0.26218125], [-0.053025, 1.1719375, 0.0126125], [0.26218125, 0.0126125, 1.11475]]; default blocked identities remained 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; focused measured-inertial suite passed 18 tests; broad robot-lab gate passed 63 tests
Commit: pending
Remaining: expand the synthetic path from happy-path proof to the full negative matrix for exact-cover ambiguity, reused evidence, and invalid transform/inertia failures
Blockers: none for offline continuation
Training lock: closed
Next step: keep T16.4 open and land the negative matrix in the next slice without changing the default blocked real current-arm path
```

### 2026-07-10 - T16.4 custom absolute-path CLI safety correction

```text
Current task: T16.4
State: in_progress
Completed: preserved caller-provided absolute intake/output paths outside the repo for the measured-inertial CLI; added direct external-path write, verify, require-ready, and invalid-input no-overwrite regressions
Evidence: python -m unittest tests.unit.test_measured_inertial_intake (14 tests); python -m py_compile scenesmith/robot_lab/measured_inertial_intake.py scripts/robot_lab/write_measured_inertial_intake.py tests/unit/test_measured_inertial_intake.py; python scripts/robot_lab/write_measured_inertial_intake.py --verify kept blocked identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; external temp-path live CLI write+verify succeeded with output identity e92738a2b9f450a72c693d67903eb75cbaa40a483a35c18f4a46cf09521e1478; external --require-ready rejected nonzero; forged external intake failed before overwrite and left output sha256 7fe752efca565caca826dbd1c12b052899b72235115cf7a3663eae9b1666b35e unchanged; broad gate ./.mujoco_venv/bin/python -m unittest tests.unit.test_measured_inertial_intake tests.unit.test_robotics_dependency_lock tests.unit.test_twin_contract tests.unit.test_structural_twin_diff passed 59 tests
Commit: pending
Remaining: synthetic_test_only ready fixture/compiler, exact-cover overlap and reused-evidence rejection, golden aggregate inertia proof, and stable ready identity checks
Blockers: none for offline continuation
Training lock: closed
Next step: keep T16.4 open and implement the bounded synthetic ready-state compiler path from brief 028
```

### 2026-07-10 - T16.4 custom CLI path defect added to closeout

```text
Current task: T16.4
State: in_progress
Completed: independent rerun confirmed all embedded-prior attacks fail and existing outputs remain unchanged
Evidence: valid canonical intake copied outside repo fails before CLI write/verify because _relative_to_repo unconditionally calls relative_to(REPO_ROOT) on absolute paths
Commit: pending
Remaining: support bounded absolute custom paths with correct artifact refs, then complete synthetic ready math and negative matrix
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 028; brief 027 is superseded
```

### 2026-07-10 - T16.4 embedded CAD prior integrity gap

```text
Current task: T16.4
State: in_progress
Completed: independent adversarial audit accepted the blocked proof state but tested re-signed nested evidence rather than only top-level refs
Evidence: re-signed changes to cad_priors[0] source path/hash/mass/transform were accepted; a 99 kg forged prior compiled and verified with cad_prior_summary 99.485006 kg; duplicate component records were also accepted
Commit: pending
Remaining: deterministic embedded-prior reconstruction/evidence validation and duplicate-ID rejection, then the synthetic ready compiler and full negative matrix
Blockers: none for offline correction; real measurements remain absent by design
Training lock: closed
Next step: execute brief 026; brief 025 is superseded
```

### 2026-07-10 - T16.4 embedded prior integrity correction

```text
Current task: T16.4
State: in_progress
Completed: awaiting-measurements verification now rejects re-signed nested CAD-prior tampering and duplicate component IDs by requiring deterministic equality with the repo rebuild before blocked assembly compilation can read the intake
Evidence: 10 focused measured-inertial tests including forged 99 kg CAD prior, duplicate component ID, and no-output-written regression; py_compile on module/tests/CLI; live CLI --write-intake and --verify preserved identities 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88 / 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; 55-test broad robot-lab gate passed
Commit: pending
Remaining: synthetic_test_only ready compiler, exact-cover selection, overlap/reused-evidence rejection, inertia math golden fixture, and order-invariance checks
Blockers: none for offline implementation; real current-arm measurements remain absent by design
Training lock: closed
Next step: implement Part B of brief 026 without changing the default blocked real-artifact paths
```

### 2026-07-10 - T16.4 manager truth correction before implementation

```text
Current task: T16.4
State: in_progress
Completed: repo/history audit found no genuine physical SO-101 piece-weight evidence; seven MJCF masses totaling 0.632006 kg are CAD-derived priors only
Evidence: manager intervention 009; TwinProfile leaves full_arm_mass_kg null; no measured-mass source file exists
Commit: pending
Remaining: checked-in awaiting-measurements intake, blocked current-arm result, synthetic-only ready compiler proof, binding/tamper/double-count tests, and fresh review
Blockers: real current-arm inertials remain blocked until physical measurements are supplied, but the offline compiler capability is implementable now
Training lock: closed
Next step: execute brief 024; do not execute superseded brief 023
```

### 2026-07-10 - T16.4 blocked real-artifact baseline

```text
Current task: T16.4
State: in_progress
Completed: added deterministic measured-mass intake and assembly inertials artifacts for the checked-in current arm; normal CLI write emits `awaiting_measurements` intake plus `blocked_missing_measurements` output bound to the dependency lock, TwinProfile, structural diff, and intake file hash; `--verify` passes and `--require-ready` rejects nonzero
Evidence: configurations/robot_lab/pi05_measured_mass_intake.awaiting_measurements.json identity 35571daca435bb191313c9b22594c9fecaaef7abc68c8e7e2faa362692653b88; configurations/robot_lab/pi05_assembly_inertials.blocked_missing_measurements.json identity 5816faa0d05dd309a2768551cd50b845932ff5abbc355c11f146371d868580c4; 7 focused measured-inertial tests; live CLI write+verify; 52 broad robot-lab tests
Commit: pending
Remaining: synthetic_test_only ready-state compiler math, golden mass/COM/inertia fixture, overlap/double-count/tamper hard-fail coverage, and order-invariance checks
Blockers: real current-arm physical inertials remain blocked until future measurements exist; offline synthetic compiler proof is still implementable
Training lock: closed
Next step: extend `scenesmith.robot_lab.measured_inertial_intake` to compile a synthetic ready fixture without changing the default blocked real artifact
```

### 2026-07-10 - T16.3 manager reopen after adversarial identity checks

```text
Current task: T16.3
State: in_progress
Completed: independent manager audit reproduced the accepted v1 implementation and tested semantic invariants outside the executor suite
Evidence: scaled-equivalent quaternion spellings produced different unnamed keys; reversing same-stem duplicates with friction 1 versus 2 changed both collision and friction records; manager intervention 008
Commit: pending
Remaining: canonical quaternion identity hashing, deterministic full-attribute duplicate ordering, v2 strategy declaration, artifact regeneration, and fresh review
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 022; do not execute deferred brief 021
```

### 2026-07-10 - T16.3 unnamed-geom identity v2 correction

```text
Current task: T16.3
State: in_progress
Completed: unnamed collision-key hashing now canonicalizes equivalent explicit quaternions, same-stem duplicate occurrence suffixes are assigned after deterministic full-attribute sorting, signed-zero quaternion spellings collapse to the same canonical payload, and the tracked artifact now declares identity strategy v2
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9; 24 focused structural-diff tests; py_compile of structural diff, tests, and CLI; live CLI write+verify pass; 49 broad robot-lab tests
Commit: pending
Remaining: fresh reviewer rerun of the adversarial fixtures and live verify path to close T16.3
Blockers: none for offline correction
Training lock: closed
Next step: obtain a reviewer decision on brief 022 before reopening deferred brief 021 / T16.4
```

### 2026-07-10 - T16.3 reviewer closeout (superseded by manager intervention 008)

```text
Current task: T16.4
State: pending
Completed: reviewer verified order-invariant unnamed collision identities, duplicate multiplicity preservation, visual-sibling stability, and explicit non-pairing across incompatible runtime-vs-Menagerie structures
Evidence: reviewer decision 032; commit 07a652e; configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683; 21 focused structural-diff tests; live CLI verify pass; 46 broad robot-lab tests
Commit: 07a652e
Remaining: measured inertial intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence
```

### 2026-07-10 - T16.3 semantic unnamed-geom identity

```text
Current task: T16.3
State: in_progress
Completed: structural diff now derives unnamed collision identities from a shared semantic key helper used by both collision and friction extraction, records the identifier strategy in the artifact, ignores visual-only sibling insertions, preserves duplicate multiplicity deterministically, and leaves incompatible runtime-vs-Menagerie structures as explicit missing/extra evidence instead of ordinal pairings
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 5b070b1b1f98aad3eaf00d4bd9d153ab78f53ec4046b0948ef2cf5ae93387683; 21 focused structural-diff tests; live CLI write+verify pass; 46 broad robot-lab tests
Commit: pending
Remaining: reviewer confirmation for T16.3 closeout
Blockers: none for offline correction
Training lock: closed
Next step: obtain a reviewer decision on brief 020 and, if accepted, reopen T16.4 measured-mass intake
```

### 2026-07-10 - T16.3 unnamed-geom proof strengthened

```text
Current task: T16.3
State: in_progress
Completed: source/profile binding, effective solver defaults, quaternion semantics, inferred-inertia unknowns, and effective contact/friction evidence
Evidence: commit d31cdc3; manager audit 007 proves repeat-generation alone cannot detect sibling-index instability
Commit: pending
Remaining: order-invariant semantic unnamed-geom identity
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 020 and obtain a fresh reviewer decision
```

### 2026-07-10 - T16.3 inertial and contact truthfulness correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now surfaces non-derivable mass-bearing inertials as explicit unknown evidence and compares friction/contact through real attached joints and collision geoms while keeping declaration-only defaults separate
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fe9177e07a597e9db57c1896f5295f84b7ae9ff313219e33afa83b41c46fd08d; 15 focused structural-diff tests; live CLI write+verify pass; 40 broad robot-lab tests
Commit: pending
Remaining: deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: finish the deterministic unnamed-geom handling needed to reopen T16.4
```

### 2026-07-10 - T16.3 complete quaternion semantic coverage

```text
Current task: T16.3
State: in_progress
Completed: structural diff now applies quaternion canonicalization across all transform-bearing structural categories, treats omitted transform quaternions as effective identity where MuJoCo defaults apply, and tolerates tiny canonical quaternion noise
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity a90ffc8b347ae8b6d4a7a4bde0d60c3be64af7a41fb77b543e2c6c9beb6b9331; 12 focused structural-diff tests; live CLI write+verify pass; 37 broad robot-lab tests
Commit: pending
Remaining: inferred-inertia unknown handling, effective friction/contact attachment semantics, and deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: resume brief 016 and make inertial/contact truthfulness explicit without reopening quaternion false deltas
```

### 2026-07-10 - T16.3 quaternion coverage correction

```text
Current task: T16.3
State: in_progress
Completed: TwinProfile binding and effective solver comparison; partial rotation canonicalization
Evidence: commit fb54e64; five scale-equivalent arm-collision quaternion deltas remain in the artifact; manager audit 006
Commit: pending
Remaining: collision/implicit-identity quaternion semantics, inferred-inertia unknowns, effective friction/contact evidence, and deterministic identifier limits
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 017, then return to queued brief 016
```

### 2026-07-10 - T16.3 semantic acceptance reopened

```text
Current task: T16.3
State: in_progress
Completed: deterministic source/hash plumbing and first machine diff baseline
Evidence: commit 7bebf55; manager audit 005; independent semantic audit
Commit: pending
Remaining: profile binding, canonical rotations, effective solver semantics, inferred-inertia unknowns, effective friction/contact evidence, and regression tests
Blockers: none for offline correction
Training lock: closed
Next step: execute brief 014 and obtain a fresh reviewer decision before T16.4
```

### 2026-07-10 - T16.3 TwinProfile binding correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now binds the checked-in simulation-only TwinProfile as an explicit artifact input and rejects profile drift during verify
Evidence: commit 936dd2f; local write/verify product path; 6 focused tests; 31 broad robot-lab tests
Commit: 936dd2f
Remaining: canonical rotations, effective solver defaults, inferred-inertia unknowns, effective friction/contact evidence, and deterministic identifier limits
Blockers: none for offline correction
Training lock: closed
Next step: normalize equivalent quaternions and compare effective solver defaults before reopening T16.3 for review
```

### 2026-07-10 - T16.3 quaternion and solver semantics correction

```text
Current task: T16.3
State: in_progress
Completed: structural diff now canonicalizes equivalent quaternions for semantic comparison, records compared canonical quaternion values on true rotation mismatches, and compares effective MuJoCo solver defaults even when one source omits <option>
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity 6a990b8a28d6b18e12dde18398122ea84ba7d3a91569ca2f728d8c09f5d3dad7; 9 focused structural-diff tests; live write+verify product path; 34 broad robot-lab tests
Commit: pending
Remaining: inferred-inertia unknown handling, effective friction/contact attachment semantics, and deterministic unnamed-geom limits
Blockers: none for offline correction
Training lock: closed
Next step: close the remaining T16.3 semantic gaps before reopening T16.4
```

### 2026-07-10 - Advice rebaseline

```text
Current task: T16.0
State: in_progress
Completed: converted the new architecture into prerequisite-gated execution order
Evidence: local MJCF has CAD inertials/STS prior; 3,327 H50 windows cross minimal semantic boundaries in the current corpus
Commit: pending
Remaining: M16-M19 before any more training
Blockers: none for offline implementation
Training lock: closed
Next step: protect and dry-run the repo-local goal loop, then pin dependencies and reconcile the twin
```

### 2026-07-10 - T16.0 scoped goal-loop guard

```text
Current task: T16.1
State: in_progress
Completed: protected-worktree snapshot/verify and scoped pair/start/stop wrappers
Evidence: 70 tests; 51 protected paths; pre/post dry-run guard pass
Commit: b5d056b
Remaining: dependency lock and twin foundation
Blockers: none for offline work
Training lock: closed
Next step: pin all policy/model/runtime repositories and local patches
```

### 2026-07-10 - T16.1 manager redirect

```text
Current task: T16.1
State: in_progress
Completed: local LeLab, dirty LeRobot patch, Robot Studio MJCF/URDF identities
Evidence: commit 92adde5; reviewer commit ec788fc; manager audit found OpenPI/Menagerie revision=null and absolute repo_root
Commit: correction pending
Remaining: portable remote pins before T16.2
Blockers: none
Training lock: closed
Next step: correct the dependency lock and re-review T16.1
```

### 2026-07-10 - T16.1 completed and planning realigned

```text
Current task: T16.2
State: in_progress
Completed: portable local/remote dependency lock including actual Menagerie so101.xml
Evidence: commits 92adde5, addcafd, cd5ab42; 81 tests; live offline lock verify
Commit: cd5ab42 final content correction
Remaining: twin schemas, structural reconciliation, mass compiler, fake qualification harness
Blockers: none for T16.2
Training lock: closed
Next step: content-addressed simulation-only twin contract
```

### 2026-07-10 - T16.2 truth correction and T16.3 start

```text
Current task: T16.3
State: in_progress
Completed: twin profile/spec/report schemas without fabricated measurement evidence
Evidence: bc5187c schema feature; ae6fe04 removes invented pass/12 V value; 94 tests
Commit: ae6fe04
Remaining: structural diff, measured-mass compiler, offline qualification harness
Blockers: none for structural diff
Training lock: closed
Next step: compare pinned runtime and Menagerie structures without switching either
```

### 2026-07-10 - T16.3 false blocker cleared

```text
Current task: T16.3
State: in_progress
Completed: tracked exact Menagerie license, README, so101.xml, and scene.xml
Evidence: commit 38b3425; vendored hashes match remote pin; 95 tests
Commit: 38b3425
Remaining: machine structural diff and reconciliation decision
Blockers: none for offline work
Training lock: closed
Next step: resume structural comparison from tracked source inputs
```

### 2026-07-10 - T16.3 structural baseline verified

```text
Current task: T16.4
State: in_progress
Completed: deterministic structural diff between the active Robot Studio MJCF and pinned Menagerie so101.xml, with matched/mismatched/missing/extra buckets and explicit reconciliation decisions
Evidence: configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity d71576574eb3dbb592cb495481a9de2e17e1581cc3e10476e1bc098106053b89; 5 focused structural-diff tests; live CLI write+verify pass; 17-test broad robot-lab suite pass
Commit: pending
Remaining: measured inertial intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence
```

### 2026-07-10 - T16.1 robotics dependency lock

```text
Current task: T16.2
State: verified
Completed: pinned LeLab runtime, split local LeRobot checkout, OpenPI semantic reference, Robot Studio SO-101 runtime files, and Menagerie target lineage in one tracked lock
Evidence: configurations/robot_lab/pi05_robotics_dependency_lock.json; 7 tests passing in .mujoco_venv; live lock write+verify pass; active MJCF/URDF hashes recorded; local lerobot tracked diff sha256 captured
Commit: pending
Remaining: twin profile, qualification schemas, structural reconciliation, and downstream compiler gates
Blockers: none for offline work; unrelated broad-suite provenance test still needs an importable lerobot package in the validation environment
Training lock: closed
Next step: define TwinProfile, TwinQualificationSpec, and TwinQualificationReport with a simulation-only example tied to the new dependency lock
```

### 2026-07-10 - T16.1 portable remote pin correction

```text
Current task: T16.2
State: verified
Completed: replaced unresolved OpenPI and Menagerie placeholders with exact remote revisions plus license/content hashes; removed absolute repo_root from the signed lock identity
Evidence: updated configurations/robot_lab/pi05_robotics_dependency_lock.json; 7 focused dependency-lock tests passing; live write+verify pass; 11-test broad robot-lab suite pass including scene-builder reachability
Commit: pending
Remaining: twin schemas, structural reconciliation, and downstream compiler gates
Blockers: none for offline work
Training lock: closed
Next step: define TwinProfile, TwinQualificationSpec, and TwinQualificationReport with a simulation-only example tied to the corrected dependency lock
```

### 2026-07-10 - T16.2 twin contract schemas

```text
Current task: T16.3
State: verified
Completed: content-addressed TwinProfile, TwinQualificationSpec, and TwinQualificationReport schemas plus checked-in simulation-only example artifacts bound to the corrected dependency lock
Evidence: configurations/robot_lab/pi05_twin_profile.simulation_only.json; configurations/robot_lab/pi05_twin_qualification_spec.simulation_only.json; configurations/robot_lab/pi05_twin_qualification_report.simulation_only.json; 10 focused twin-contract tests; live write+verify pass; 21-test broad robot-lab suite pass
Commit: pending
Remaining: Menagerie vs Robot Studio structural diff, measured inertial intake, and offline qualification harness
Blockers: none for offline work
Training lock: closed
Next step: reconcile the active Robot Studio SO-101 runtime against pinned Menagerie with a machine-readable structural diff and explicit no-switch semantics
```

### 2026-07-10 - T16.3 blocked on missing Menagerie sources

```text
Current task: T16.3
State: blocked
Completed: confirmed the active runtime MJCF is present locally and that the dependency lock only records Menagerie `robotstudio_so101` as an exact remote pin plus reference-file hashes
Evidence: configurations/robot_lab/pi05_robotics_dependency_lock.json pins `robotstudio_so101/so101.xml` and `robotstudio_so101/scene.xml`; repo search finds no local `robotstudio_so101` directory or Menagerie XML sources to diff against
Commit: pending
Remaining: vendor or otherwise track the pinned Menagerie structural XML sources, then generate the machine-readable diff artifact
Blockers: brief 011 requires a CLI that resolves both runtime and Menagerie sources from repo state, which is impossible while only remote hashes are tracked locally
Training lock: closed
Next step: add the pinned Menagerie `robotstudio_so101` source files to repo state under a tracked path and resume T16.3 without switching the active runtime inputs
```
### 2026-07-10 - T16.3 reviewer closeout after v2 identity correction

```text
Current task: T16.4
State: pending
Completed: independent reviewer reruns confirmed equivalent quaternion spellings now hash to the same unnamed identities, same-stem duplicates are occurrence-assigned independent of sibling order, py_compile stayed clean, live artifact verify stayed bound to the checked-in baseline, and the broad robot-lab gate remained green
Evidence: reviewer decision 033; commit cadc0f3; configurations/robot_lab/pi05_structural_twin_diff.simulation_only.json identity fa86ce5c0ee89b2388759bc86a9a99b4ae23c9dbf7e750d2976587ee6fb0bea9; 24 focused structural-diff tests; live CLI verify pass; 49 broad robot-lab tests
Commit: cadc0f3
Remaining: measured-part mass intake, offline qualification harness, then M17 compiler truth gate
Blockers: none for offline T16.4 implementation
Training lock: closed
Next step: compile measured-part mass inputs and fail closed on ambiguous assembly inertia/COM evidence through brief 023
```

## 2026-07-16 - K3 owner-present RGB camera census closed safely

Brief 228 and Reviewer 313 preserve one consumed RGB-only camera session as a
terminal infrastructure failure. D405 returned a decoded PNG but failed exact
signed input-mode dimension validation; C922 was not opened. Receipt
`5c0edf59...` grants no proof label, stream-config census, latency result, or
hardware readiness. Depth, serial, register operations, torque, motion, audio,
and follower commands remained zero. Any replacement requires new owner
authority after discovery-first requested-versus-decoded dimension evidence is
reviewed.

## 2026-07-17 - K2 portable reconstruction foundation verified

Brief 226 and Reviewer 319 close K2. Source boundary `992ed2f...` is preserved
on origin; manifest `d5396251...` selects 417 files, source-pin validation
export `ae7cfd7c...` verifies 438 files, final wrapper export `97daeb06...`
verifies 438 files / 77,918,520 bytes, and final-pin W1 receipt `7d9fa11a...`
passes 29 focused tests, one strict 244-frame expert episode, and all three
retained schema renders. Combined W2 receipt `86739578...` recreates exact R0:
119+9 strict successes, 129 episodes, 31,366 frames, 59,904 windows, mixture
`37b30d34...`, statistics `02ba0e70...`, no mismatches, and independent verify
exit 0. The 2.7 GB generated tree remains scratch-only.

Original T20.43c and T20.43c-R2 remain distinct immutable boundaries; no
learned Gate C success, authority transfer, hardware, network, external
compute, Brev, transfer, promotion, or tag is granted. W3 and W5 remain
unintegrated. Next eligible task: open a fresh F0 release-gap diagnostic brief
under the owner direction recorded in
`owner-direction-2026-07-17-final-overnight.md`.

## 2026-07-17 - Reviewer 320 verifies F0 and routes to model-free F0a

Brief 230 result `807d3da7...` reconstructs the exact R2 sampler over 10,000
updates, 129 episodes, 31,366 frames, and 79,996 sampled starts. Minimum
late-frame target exposure is 97.085% of the interior median, late-phase
valid-loss mass is 113.889% of its geometric share, and exact frame-200 starts
are 97.869% of uniform expectation. Tail starvation and late-phase mixture
underweight are therefore false. The standalone unpadded H50 index omits
release, but the ACT runner never consumed it.

Required open gripper is within the pre-registered `1e-4` tolerance of the
actual R0 envelope at 1.4174 standard deviations, falsifying the normalization
hypothesis. Physical-L1 conversion does expose a 2.6963 gripper coefficient
and the retained release error is
same-direction and contact-relevant. The more discriminating counterexample is
timing: the candidate's gripper sequence matches the source release pattern
best 20 frames late, reducing pattern MAE from 0.74179 to 0.04893 rad.

Reviewer 320 closes F0 without selecting or consuming the one corrective ACT
rung. Training stays locked. F0a is next eligible only as a fresh model-free
chunk-timing, phase-observability, and observation-aliasing audit. No model,
optimizer, rollout, Brev/external compute, hardware, Gate C, transfer,
promotion, or freeze-tag authority follows.
