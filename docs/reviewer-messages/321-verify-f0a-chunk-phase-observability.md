# Reviewer Decision 321 - Verify F0a Chunk Timing And Phase Observability

**Date:** 2026-07-17

## Decision

`VERIFY_F0A_CHUNK_PHASE_OBSERVABILITY_ROUTE_TO_SEPARATE_F0B`

Brief 231 satisfies its deterministic, model-free acceptance criteria at
implementation commit `f81fa9aa90ba4eaf93a125433f1f341992cca54b` on origin.
Canonical result `278e8bc7...` reconstructs from exact hash-bound sources and
grants no checkpoint, model, optimizer, rollout, Gate C, or system authority.

## Verified findings

- The ACT actor consumes exactly two current RGB images and six qpos values.
  Raw joint velocity and dataset timestamp exist upstream, but velocity,
  phase, progress, timestamp, and environment state are omitted from policy
  inputs.
- The source-calibrated adjacent-state p95 is `0.13180902191868454`; the
  two-camera adjacent-image p95 is `0.017136876723345587`, producing the frozen
  image-near threshold `0.034273753446691174`.
- Twenty of 24 lower-to-lift source pairs meet all pre-registered state, image,
  hidden-velocity, and future-target criteria, exceeding the threshold of 12.
- Candidate frame 200 is nearest lower frame 183 at normalized L2
  `0.5811591805297467` and nearly equally near lift frame 93 at
  `0.5813087817685448`. The resulting 17-frame lag aligns within three frames
  of F0's 20-frame release delay.
- With decode starts `[0, 50, 100, 150, 200]`, no new observation occurs before
  aligned release onset frame 220. The frozen release gate ends at frame 219
  and fails, while retreat-final clearance passes.

## Adversarial review

The image-near result belongs to exact source lift/lower frames. The retained
candidate trace supplies candidate qpos comparisons but not candidate camera
images; this decision therefore does not claim candidate/source visual
identity. Likewise, retreat clearance is not a Gate C pass, cadence alignment
is a mechanistic localization rather than a successful rollout, and omitted
phase information does not license a wall-clock phase token.

Source references are unique, sorted, repository-relative, traversal-free,
hash-bound, and non-symlinked. Thresholds are pre-registered and finite.
Mutations to routing, authority, decode cadence, or signed inputs fail
verification. The implementation reads retained prior inference/rollout
evidence but performs no new rendering, simulation, checkpoint tensor read,
model construction or inference, optimizer action, rollout, dataset mutation,
network access, external compute, Brev access, or hardware action.

## Verification evidence

- canonical live verifier: pass, identity `278e8bc7...`;
- focused F0a suite: seven pass; relevant unit suite: 53 pass;
- T20.43c continuation/replacement suite: 14 pass;
- offline Ruff, JSON/non-finite, path/symlink, authority, and whitespace checks:
  pass;
- implementation commit and origin branch: exact match before this closeout.

## Authority disposition

F0a is verified and closed. After this closeout is exact on origin, a fresh
F0b brief may propose one retained-checkpoint hybrid-tail-cadence evaluation
with starts `[0,50,100,150,176,186,196,206,216,226,236]` and executed lengths
`[50,50,50,26,10,10,10,10,10,10,8]`. Strict-v2 Gate C and all thresholds
remain frozen. F0b model/inference/rollout authority, corrective training,
F1/Brev, hardware, physical transfer, promotion, destructive operations, and
the freeze tag remain closed.
