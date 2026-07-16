# Slice Brief 216 - T20.42/R0 Dataset Expansion By Construction

**Date:** 2026-07-16

## Objective

Implement and verify the deterministic construction contract for R0, then use
one separately authorized bounded generation to create 64-128 new
strict-v2-success scripted episodes over sanctioned cube-pose and episode-
initialization variation. Compile only observed strict successes through the
existing raw-store -> compiler -> window -> LeRobotDataset path, recompute
MEAN_STD statistics from the training split only, and freeze one signed
dataset/statistics/mixture manifest. This is dataset construction, not model
training or policy selection.

## Owner-decision and source boundary

- Bind the recorded T20.41 route decision at commit
  `e9d0507ce7c79ed77997d1c2334db9a14c6fbf1d` and file SHA-256
  `ae75bb594ab93a046afe848b3befb6bb919485f4814f1ab423aad9c36cbea1d5`.
  The decision fixes R0 as first and sole active before R1 ACT.
- Reverify the T17.5b scripted-expert manifest `3860158e...`, the T20.18
  recovery package `c6f36515...`, and the T20.23 dataset manifest
  `f12c95a3...` before accepting any derived construction or dataset artifact.
- Reuse the existing strict-v2 evaluator, append-only raw store, action-
  provenance contract, compiler/window path, package LeRobotDataset writer,
  two camera keys, six-joint order, measured-action convention, 30 Hz rate,
  and task prompt. Do not create a parallel data subsystem.

## Construction contract

- Before any generation, write one signed immutable construction specification
  that enumerates a fixed training-candidate set of no more than 128 unique
  episode specifications plus a separate evaluation-only held-out set. Bind
  every deterministic seed, source initial state, cube pose, allowed
  initialization delta, split role, and expected provenance.
- Cube-pose variation may use only finite planar/yaw deltas within an existing
  verified reachable envelope. Episode-initialization deltas must be bounded by
  cited source joint/scene limits and pass deterministic reachability checks.
  Any axis without a verified bound stays fixed at its source value. Physics,
  friction, mass, damping, actuator, camera, lighting, object-family, and task-
  family randomization are prohibited.
- Training candidates must not duplicate any verified T20.23 member, existing
  held-out seed 6/7 episode, or another candidate. Reserve one fresh,
  explicitly disjoint pose band in the signed specification before generation.
  Existing held-out seeds 6-7 and every episode in that fresh band are a
  separate evaluation-only manifest and do not count toward the 128 training-
  candidate ceiling or 64-success minimum. They must not enter training
  membership, recovery selection, normalization statistics, or mixture weights.
- Re-derive every grasp target and aperture through the verified geometry path.
  Every attempt is unassisted and judged by the unchanged strict-v2 oracle.
  Only observed strict-v2 successes may enter the training dataset. Failures
  remain signed in the raw store/quarantine with measured margins.
- The fixed candidate manifest must yield at least 64 and at most 128 new
  nominal strict successes. Fewer than 64 closes R0 negative; do not extend,
  resample, or adapt the manifest after observing outcomes.
- T20.18-style recovery branches are optional and additive only. If included,
  their parent selection, perturbation, maximum count, and provenance are
  frozen before generation; each must independently pass strict-v2. They do
  not replace or count toward the 64-success nominal minimum.

## Dataset and split contract

- Include each of T20.23's ten verified training episodes exactly once: six
  nominal strict successes plus four strict-success recovery episodes. Add the
  64-128 new nominal strict successes exactly once, plus only any separately
  pre-registered new recovery successes. Do not silently retire, duplicate,
  resample, or reweight the verified base mixture.
- Preserve raw episode bytes append-only and bind every episode, image, state,
  measured action, boundary, outcome, and generation specification by content
  identity. No padding, inferred actions, source mutation, image reuse,
  duplicate episode membership, or cross-boundary windows.
- Compile through the existing raw-store -> frame/segment compiler -> unpadded
  window index -> package LeRobotDataset path. Report exact candidate,
  success, failure, recovery, episode, frame, segment, window, quarantine, and
  split counts.
- Compute MEAN_STD statistics from training rows only after final membership is
  frozen. Prove seeds 6-7, the fresh pose band, failed attempts, and excluded
  recovery branches contribute zero rows to both training and statistics.
- Emit one remotely tracked compact R0 manifest binding the construction spec,
  raw-store manifest, compiler/window identities, LeRobotDataset identity,
  training-only statistics, exact mixture membership, exclusions, and held-out
  references. Large raw/image/dataset bytes may remain local only when their
  hashes and fresh-checkout limitation are explicit.

## Execution and review boundary

- The opening boundary authorizes only tests-first implementation and fixture
  validation of the construction specification, verifier, deterministic
  generator runner, dataset compiler, statistics, and manifest contracts.
- Do not execute the bounded R0 candidate generation until the implementation,
  tests, complete diff, and source identities are committed, pushed, reviewed,
  and origin-confirmed, and a fresh central decision, runtime preflight, and
  one-use generation permit all agree on that exact commit and construction
  specification.
- The permitted generation is one fixed-manifest attempt. A failed attempt is
  signed evidence, not permission to retry or change the candidate set. It
  executes the frozen training-candidate set and fresh-band expert-reference
  set once; verified seed 6/7 evidence is referenced without duplication.

## Acceptance criteria

- Tests reject source or decision drift, duplicate seeds/specifications,
  non-finite or out-of-envelope deltas, physics-parameter variation,
  unreachable initialization, held-out overlap, failed-outcome training rows,
  verified-base omission/double counting, recovery substitution, path escape/
  symlinks, image or action provenance drift, padding/inference, split/
  statistics leakage, non-deterministic order, signed mutation, and authority
  escalation.
- A second model-free verification reproduces every compact identity and exact
  count from immutable retained sources. The final training membership contains
  the ten verified T20.23 episodes exactly once, 64-128 new nominal strict-v2
  successes exactly once, only explicitly declared optional new recovery
  successes, and zero failed or held-out episodes.
- Training-only MEAN_STD statistics round-trip known rows and are invariant to
  all held-out/failure evidence. The signed mixture manifest binds exact source
  class counts without implicit resampling or weighting.
- Focused and relevant broad regression tests, JSON and pointer checks,
  same-agent adversarial review, canonical state, ledger, session evidence,
  reviewer decision, scoped commits, and remote preservation agree before
  T20.42 is described as verified.

## Stop conditions

Stop before generation on missing/drifting source evidence, an unbounded or
overlapping pose band, inability to prove training/statistics exclusion, a
need for physics randomization or a new data subsystem, or absent reviewed
central/preflight/permit authority. After the one permitted generation, fewer
than 64 nominal strict successes, nondeterministic replay, or irreconcilable
source/hash drift closes R0 negative without adaptive expansion.

## Authority withheld

No current episode-generation run, model construction/load/inference,
optimizer creation/training, checkpoint creation, Gate B re-proof, learned-
policy rollout, Gate C/D/E claim, threshold change to `463477dc...`, archive
replay activation, hardware/camera/serial access, physical motion, network or
download, external compute, Brev, physical transfer, promotion, destructive
operation, or R1 activation is granted. T20.43 may open only after T20.42 has a
separately reviewed verified boundary.
