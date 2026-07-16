# Owner Route Decision — T20.41 (2026-07-16)

Recorded 2026-07-16 ~10:20 CDT by Claude at the owner's explicit chat
instruction. This document answers the T20.41 blocker ("select and authorize
the next capability strategy after ACT, SmolVLA, and X all failed forward
routing"). Like the MVP plan, it is a task-ordering and routing source, not an
authority source: every slice still requires its own brief, central authority
composition, preflight, one-use permit, and remote preservation. It does not
resume the closed T20.35/T20.36 candidate field, does not weaken amendment
`463477dc...`, does not accept any retained checkpoint, and does not open
hardware, motion, camera, network/download, external-compute, or Brev
authority. The T19.x physical track remains a separate owner-present track;
the simulation route below must never block on or couple to it.

## Diagnosis the route is built on

1. **Gate B's diagnostic purpose is complete.** Its fault class is "model or
   trainer plumbing," and T20.35x's frozen-uniform pass (worst 0.04478 rad)
   answered it: the data → processor → training → checkpoint → reload →
   decode pathway can optimize to target. T20.36n adds that X's amended-gate
   misses are five grasp-phase gripper cells at 0.000342–0.004420 rad excess —
   fidelity capability is not the blocker.
2. **The failure signature is coverage, and it replicated three times under
   one recipe.** T20.36 coverage training regressed a passing checkpoint;
   T20.36o's baseline passed 0/5 forward chunk starts; T20.36o's 2,500-update
   bridge passed every source objective while forward probes went 0/25 with
   non-monotonic start-0 behavior. The morning summary's own conclusion:
   source objective is not predictive of forward chunk-start accuracy.
3. **All of that evidence comes from one training construction.** Every
   optimizer slice since T20.24 has been bespoke path-corrective surgery:
   supervising retained denoise paths from a handful of frozen contexts, 500–
   2,500 updates, on a 10-episode/2,330-frame dataset. The standard official
   supervised recipe — fresh noise sampling over shuffled window batches from
   the full dataset — has never been run at a realistic budget on adequate
   data. Per the T19.0 lesson (three same-signature failures → interrogate the
   frozen construction), the frozen constant to change is the recipe and the
   data volume, not another correction objective.
4. **The open-loop entry barrier prevented Gate C evidence entirely.**
   Requiring amended-gate passes at all five chunk starts before any rollout
   meant Gate C was never executed, so closed-loop compounding versus
   execution semantics remains unobserved. Simulation rollouts are cheap and
   safe; withholding them bought nothing.

## The route: R0–R3

**R0 — dataset expansion by construction (T20.42, first and sole active).**
Use the verified deterministic scripted expert and the sanctioned
episode-variation randomization (cube pose and initialization deltas within
reachable bounds — never physics parameters) to generate on the order of
64–128 new strict-v2-success episodes; optionally add T20.18-style recovery
branches where cheap. Only strict-v2 passes enter training; failures land in
the raw store/quarantine as usual. Compile through the existing raw-store →
compiler → window → LeRobotDataset contracts (T17.5b/T20.23 pattern).
Recompute MEAN_STD statistics from the training split only. Freeze held-out
evidence outside training and statistics: existing seeds 6–7 plus one fresh
never-trained pose band. Deliverable: one signed dataset, statistics, and
mixture manifest. No new subsystem; construct before search.

**R1 — ACT standard rung (T20.43).** Official LeRobot ACT recipe on the R0
dataset, trained from scratch, realistic budget (order 10k–20k updates,
standard batching, fresh sampling), fixed-interval checkpoints. Evaluation is
rollout-primary (doctrine below). One bounded run; negative results are
signed, not retried.

**R2 — SmolVLA standard rung (T20.44).** Fine-tune the cached SmolVLA base
with the already-validated trainable scope on the same dataset, order 5k–10k
updates, same evaluation. Runs after R1's boundary regardless of R1's outcome
— independent evidence, not a fallback.

**R3 — π0.5 standard rung (T20.45, conditional).** Only after R1/R2 evidence
exists. A bounded local-MPS standard fine-tune from the cached base is
authorized-to-propose; full-scale π0.5 training is not local-feasible, and
external compute stays closed. If R1/R2 show the expanded dataset is
learnable but π0.5 is locally throughput/capacity-bound, prepare a costed
external-compute proposal document (ABEJA-parity reference: ~50 episodes, ~5k
steps, single A100, ~5 h) for a separate, fresh owner authorization. Preparing
the proposal is a documentation act; consuming compute without that fresh
grant is prohibited.

## Evaluation doctrine (owner-signed change)

- **Closed-loop MuJoCo rollout is the primary evaluation primitive.** No
  open-loop gate — amended or uniform — may block an evaluation rollout of a
  trained checkpoint. Rollouts are evaluation, never "retries."
- **Strict-v2 remains the only success oracle.** Gate C = one unassisted
  rollout reproducing a training episode through strict-v2; Gate D = all
  eight constructive episodes; Gate E = frozen held-out starts.
- **Execution semantics are part of Gate C's fault class.** Each evaluated
  checkpoint reports both frozen 50-step chunk consumption and one bounded
  receding-horizon variant (consume k ∈ {5, 10} actions per decode). Both are
  reported; neither changes the oracle.
- **Every rollout result carries:** strict-v2 outcome, first-divergence frame,
  mirror MP4, amended-gate `463477dc...` trace analysis as routing vocabulary,
  frozen-uniform 0.05 rad as report-only, and T20.38 receipt margins.
- **Ladder interpretation:** Gate A parity checks still apply per candidate
  (round-trip tests on the R0 dataset before its rung). Gate B re-proof is not
  required for R1–R3 — its localization job is done; re-imposing one-batch
  perfection as an entry ticket recreates the closed trap.

## Stop rules

- One bounded run per rung; a failed rung closes with signed evidence and no
  retry without a fresh brief.
- Three same-signature failures across rungs stop the route and return to the
  owner with a synthesis, per the T19.0 rule.
- No fourth architecture, no correction-objective work, and no threshold
  change to `463477dc...` without a fresh owner decision.
- T20.40 archive replay activates only after a mechanical Gate C pass; the
  T20.39 archive stays evidence-only until then.
- Checkpoint trees stay local with signed tree identities; no multi-gigabyte
  remote preservation. The four closed negative trees keep their current
  disposition.
- Mid-run fixed-interval probes are mandatory in every rung so regressions
  are caught during, not after, the run.

## Sequencing

R0 first and alone; R1 after R0 verifies; R2 after R1's boundary; R3
conditional on R1/R2 evidence. Model-free receipt/archive work may fill
training waits. The next session begins with a fresh brief for T20.42/R0
under this route.

## Addendum (2026-07-16 ~17:35 CDT) — owner authorizes one T20.43b ACT replacement

Recorded by Claude at the owner's chat instruction after reviewing the T20.43
terminal receipt. Grounds: T20.43 was consumed as a pure infrastructure
failure — the mirror child venv failed `import mujoco` (exit 1) and
terminated the run with **zero optimizer updates executed** (receipt
`b64ec6d0...`, Reviewer 293) — so trained-ACT capability on the R0 dataset
remains unresolved while its rung is closed. Precedent: the T20.36h
dependency failure was followed by the owner-authorized T20.36j replacement
with a corrected environment.

The owner therefore authorizes **exactly one T20.43b ACT replacement rung**,
under all of the following:

- Opens only after the T20.44 terminal boundary (result, review, and state)
  is preserved on origin; if the current run window lacks room, T20.43b is
  the first task of the next owner window.
- Reuses the stable T20.44 runtime interpreter and the renderer-entrypoint
  smoke gate (real renderer execution producing a valid nonempty
  MP4/manifest before any attempt marker), so the T20.43 failure mode cannot
  recur unproven.
- Same fixed official ACT recipe lineage as spec `b3a510f8...` (10,000
  updates, batch 8, fixed checkpoints, chunk-50 plus receding-10 rollout
  semantics, first-pass selection) — no recipe changes.
- Full fresh ceremony: new brief, Gate A probe against the R0 package,
  central authority, runtime preflight, one-use permit, remote preservation
  before the marker.
- This supersedes T20.43's "no replacement" exclusion for exactly one
  replacement and nothing else: no second replacement, no correction
  objectives, no threshold changes, and hardware, network, external compute,
  and Brev remain closed. T20.44 and its result are not modified.
