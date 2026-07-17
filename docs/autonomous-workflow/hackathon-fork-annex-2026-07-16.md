# Hackathon Fork Annex (2026-07-16)

Condensed transfer map for the new-repository fork: four people, three days,
distributed local training on personal devices, basic tasks first, then
harder ones, live-hardware demo at the end. Travels with the reconstruction
kit as an optional-tier source. Not an authority source.

## Copy these five assets — they are the treasure

1. The MuJoCo SO-101 twin and scene compiler.
2. Strict-v2 plus the T20.38 quantitative margin receipts — **a ready-made
   shaped-reward ladder for RL** (approach distance, contact count, lift
   height, place distance; 33 direction-correct margins). This project cut RL
   because sparse success makes it hopeless; the margins are the density fix.
3. The geometry-derived constructive expert: demonstrations for warm-start,
   the baseline to beat, and the regret oracle for auto-curriculum.
4. The R0 generator and randomization bounds (verified 128/128 strict
   successes; episode variation only, never physics parameters).
5. The processor/normalization contracts and the dual-semantics
   (chunk-50 / receding-10) rollout evaluation harness with mirrors.

## Keep exactly three rules; leave the rest of the ceremony behind

- Held-out scenes/seeds are frozen before any training starts.
- Every claim ships with a replayable signed artifact.
- Evaluation code is owned separately from training code.

The authority composer, permits, one-use markers, and reviewer alphabet made a
solo autonomous agent trustworthy for weeks; they are the wrong weight for
four humans in one room. Do carry one habit: pre-marker smoke tests that
execute the exact output-artifact schemas (three experiment slots here died
to a venv import, a renderer entrypoint, and a mirror schema — zero to
science), and give infrastructure failures replacement semantics by default.

## Distributed architecture: distribute episodes, not gradients

Heterogeneous laptops (MPS/CUDA/CPU) make synchronized gradient training
miserable. Each device runs twin + oracle + a local learner; start RL from
**state observations** (pixels are why the VLAs needed 5,000 updates to touch
the cube). Push episodes and checkpoints to a shared hub (LeRobotDataset v3
on Hugging Face works). One frozen central evaluator replays every candidate
on identical seeded scenes: leaderboard plus counterexample-archive
regression gating (the T20.39/T20.40 concept). First leaderboard entry: the
scripted expert.

## Hardware assignments

- 96 GB Macs: local ACT/state-RL training and simulation work; SmolVLA only as
  day-three stretch.
- The NVIDIA box ("800 GB" is almost certainly system RAM, not VRAM — run
  `nvidia-smi` day one): episode hub, central evaluator, RealSense **depth as
  observer-role only** (librealsense is first-class on Linux), and **robot
  gateway** — a policy-inference server (prefer pinned LeRobot async
  inference) exposing an action-chunk protocol with T20.22 timing fields, so
  any checkpoint of any size can drive the robot while a Mac keeps the serial
  driver. If VRAM is genuinely ~80 GB+, it can also host the π0.5 fine-tune
  locally instead of Brev.
- $500 Brev credits: F1 proved the full protocol at **$5.53 per 5,000-step
  π0.5 full fine-tune** (A100-80GB, 3.3 h, receipted teardown). Brev is
  therefore a standing iteration lane, not a single reserved shot — soft cap
  ~$50/day, every run using the F1 pattern (spend ledger, teardown inventory
  receipt, signed evaluation summary).

## Weekend compute-and-model doctrine (updated 2026-07-17 post-F1/R2)

**MPS for iteration, NVIDIA for scale, state for the demo, pixels for the
future.**

- **MPS lane (every Mac):** ACT training (proven: clean 10k-update campaign
  locally) and short continuations (~40 min), all state-RL, all data
  generation, all sim rollouts. This is the per-person fast loop — many
  small experiments against the shared frozen held-outs.
- **NVIDIA/Brev lane:** all π0.5 work (full fine-tune needs ~70 GB+ → Brev
  A100-80GB unless the local box's VRAM matches), batched 1–3 runs/day with
  targeted variations (release-fixed data, early stopping near step 1,000
  where F1 peaked before overfitting). SmolVLA stays parked: both MPS VLA
  attempts were the weakest results per compute hour.
- **Where VLAs fit:** NOT on the live-demo critical path. The
  language-commanded demo grounds language in the LLM planner, which selects
  object/target poses; the policy underneath only needs to be
  goal-conditioned — ACT or state-RL suffices. VLAs are the *robustness and
  sim2real bet*: π0.5's pretrained visual priors are the best candidate for
  transferring RGB policies to real cameras, so keep iterating it cheaply on
  Brev in the background and adopt it the moment it beats ACT on the frozen
  evaluator.
- **The reliable live-hardware path is state, not pixels:** the AprilTag mat
  gives real-time object poses, joints come from the robot bus, so a
  state-conditioned policy runs on hardware with **no visual sim2real gap at
  all**. Sim-trained RGB policies (from-scratch ACT especially) face an
  uncalibrated visual gap. Plan the demo policy state-first with RGB as the
  stretch, and let the teleop fallback trigger only if both fail Saturday
  evening.

## Camera decision (2026-07-16)

VLA/demo policies remain RGB + joint-state. The fast state-RL tier is
camera-free joint state plus simulator object pose. The D405
enumerates on macOS as UVC but its depth stream is out-of-scope on Mac; a
known-good Logitech C922 is already on hand as the RGB fallback. Real risks
to budget for: camera-pose calibration and exposure/latency consistency
between twin renders and the physical view — not depth.

## Demo target and the reliability math

**Primary demo: language-commanded pick-and-place** — an LLM turns "put the
red cube in the left tray" into 1–3 pick/place operations, resettable between
commands, interactive for judges, no compounding chain. **Chess is the
encore, not the load-bearing act**: a full game is 40–80 consecutive
pick-places and reliability compounds (0.95^60 < 5%), so run a mate-in-two
finale (4–6 moves, chunky demo-friendly pieces, LLM narrating, one retry)
only if the central evaluator shows ≥85% per-move success by day 3.

## Day-one checklist

1. Clone at tag `freeze-2026-07-17-hackathon-fork`; run the one-command kit
   bootstrap and inspect its receipt.
2. Start fresh fork ACT and state-RL baselines from the reviewed R0 parity
   boundary. Preserve both ACT source-repo boundaries: original T20.43c is
   exact-equivalence evidence plus an inconclusive update-728 interruption;
   T20.43c-R2 is the later 10,000-update terminal negative. The R2
   counterexample is useful—chunk-50 reached 45.674304 mm maximum lift and the
   final rollout failed only release—while all consumed markers and permits
   remain inert history, never runnable fork authority.
3. Freeze the fork's held-out scene/seed set before anyone trains.
4. Per-device camera RGB checklist (resolution/fps/latency); stand up the
   episode hub and central evaluator; post the expert to the leaderboard.

## Simplifications adopted for the fork (subtract, don't add)

1. **One runtime environment.** The parent-python/child-venv split killed
   three one-use attempts. The fork uses the pinned LeRobot venv as THE
   interpreter for everything — training, rollout, rendering in-process. The
   subprocess dispatch layer is deleted, not smoked.
2. **State-first, camera-free training loops.** Task 0–1 (reach, push) train
   on joint state + object pose from the simulator, no rendering in the loop
   — orders of magnitude faster on laptops. Cameras and video datasets exist
   only for the VLA track and demo mirrors.
3. **Short episodes with early termination.** A 60-frame reach task with
   success-triggered termination, not 244-frame full episodes, for the RL
   ladder's lower rungs. Episode length is the single biggest rollout-cost
   knob.
4. **Two policy tracks only.** ACT (IL baseline) and state-based RL (e.g.,
   SAC) until a demo works end-to-end. SmolVLA/π0.5 are day-3 stretch, not
   parallel workstreams.
5. **Auto-emitted `RUN_RECEIPT.json` replaces ceremony.** Every run's harness
   writes one file: git commit, config hash, dataset identity, seed, wall
   clock, metrics. That is the entire authority story in the fork.
6. **CPU-pinned evaluator.** MuJoCo is CPU anyway; run eval-side policy
   inference on CPU/fp32 so verdicts are bit-identical across all Macs and
   the Linux box. Train fast and nondeterministically; judge slowly and
   identically.
7. **Task registry instead of scene editing.** One frozen workcell XML plus a
   registry mapping task_id → scene variant + predicate set + reward margins.
   Adding a task is a registry entry; nobody touches MuJoCo XML.
8. **Two dataset tiers.** Light state-only parquet for RL iteration; full
   audiovisual LeRobotDataset only for VLA training and demo evidence.
9. **The gateway is the only road to the robot.** All hardware access —
   teleop, tests, demo — goes through the policy-server protocol. One
   integration surface, one timing contract, one thing to debug.
10. **Born-clean repo hygiene.** Outputs gitignored from the first commit,
    plain human run names (`runs/2026-07-17_act_a/`), no task alphabet —
    that notation earned its keep in a solo autonomous loop, not in a
    four-person room.

## Adopted from the RoboTTT/ENPIRE review (2026-07-17, owner-approved)

External anchors verified: RoboTTT (NVIDIA GEAR, July 2026 — 8K-timestep
fast-weights context on GR00T N1.7) and GR00T N1.7 (public, LeRobot
integration, official SO-101 fine-tune/deploy guide). We reproduce neither;
we adopt what our own evidence independently supports.

1. **Temporal-context ablation (MPS, first-class experiment).** F0a's
   aliasing is at heart a *velocity* ambiguity — lifting and lowering states
   match in position/image space with opposite velocities. Escalation ladder,
   one rung at a time against the frozen evaluator: (a) F0c data fix →
   (b) **Markov-augmented state candidate**: add joint/object velocities and
   previous action (augmented, not proven complete — contact mode, actuator
   lag, and controller state stay hidden; the experiment tests sufficiency)
   → (c) explicit 2–4-step state/action history stack via a reviewed
   fork-local wrapper — **verified NOT a config knob**: the pinned ACT
   raises `ValueError` at `n_obs_steps != 1`
   (configuration_act.py:148), so this rung is an implementation slice with
   new processor semantics → (d) 8–16-step learned history (small GRU)
   only if (a–c) leave signed evidence demanding it.
   **Velocity observability parity caveat for rung (b):** sim reads exact
   `qvel`; hardware only gets finite-differenced AprilTag/encoder deltas.
   Train on the same estimator the hardware will use (finite differences
   with the same filter), or rung (b) fixes aliasing while quietly opening
   a new sim2real gap.
2. **Auto-correction episodes (the best new mechanism).** Candidate rollout
   fails → evaluator localizes the failure → MuJoCo restores a full-state
   branch (qpos, qvel, actuator/controller state, randomization identity —
   the verified T18.4 snapshot surface) at the **causal divergence, not the
   terminal predicate** (release fails formally at frame 219 but lags
   ~17–20 frames earlier; record both `terminal_failure_frame` and
   `causal_intervention_frame`) → the geometry expert **replans from that
   exact branch state** (never pastes the original tail) → one correction
   record with supervision masked to the corrected tail, labeled
   `context_role/context_policy/failure_predicate/correction_owner/
   supervision_mask`. For today's one-observation ACT this is honestly
   "policy-induced branch states as corrective training starts"; it becomes
   literal failure-as-context only once a history stack exists. Admission
   only through the design-rule-8 gate, as a **bounded mixture fraction
   with the nominal expert episodes preserved as the training floor**.
3. **Demo hierarchy with honest labels.** Level 1: pure learned policy
   passes strict-v2. Level 2: labeled hybrid — learned policy through
   lower, explicit state controller for release/verify/retreat. Level 2 is
   the **strongest simulation fallback** (ACT fails only release) and the
   most promising physical candidate *after* gateway, calibration, shadow
   mode, and a bounded canary; the near-guaranteed **physical** fallback is
   state-based primitives with the explicit release controller. Level 3:
   teleop, proving only the gateway and calibration. Never blur the labels.
4. **NVIDIA lane ordering.** π0.5 release-fixed continuation stays the
   *primary* NVIDIA run — proven end-to-end at ~$5.5 — and GR00T N1.7 runs
   as a **bounded parallel challenger**, never a gate on π0.5. Challenger
   path order: **native pinned-LeRobot `groot` policy first** (verified
   present in the pinned checkout at
   `external/lerobot/src/lerobot/policies/groot/`; consumes v3 datasets
   through the normal stack — still run a dependency preflight, the
   T20.35u lesson, since groot may pull extras beyond the pinned lock);
   the **V3→V2 conversion plus `modality.json` applies only to the
   standalone Isaac-GR00T fallback path**. Both paths gate on exact
   camera-key/action-order/units/gripper/normalization parity before any
   training. Parallel means data-mapping/smoke/gateway work may overlap;
   only one expensive VLA training campaign occupies the lane at once.
   SmolVLA stays parked. Fine-tune wants 40 GB+ VRAM; inference 16 GB+.
5. **Experiment registry, not a framework — with evaluation ownership
   preserved.** `RUN_RECEIPT.json` gains `parent_checkpoint`,
   `hypothesis_id`, `candidate_id`, `doctrine_commit` (the exact annex
   revision the run operated under — the doctrine evolves on the branch
   past `sim2claw-genesis`), and `evaluation_decision_ref: null`. **A
   training runner never writes its own promotion**: the separately owned
   evaluator emits its own signed decision artifact (`candidate_id`,
   `evaluator_commit`, `frozen_evaluation_set`, `promotion_decision`
   promote/reject/retain_as_counterexample — the last feeding the T20.39
   archive — `decision_reason`, `selected_checkpoint`, identity). The
   studio server joins the two records by `candidate_id`. The six-act demo
   narrative is assembled from artifacts every run already emits.
6. **Video-conditioned task specification** (VLM extracts object/target/
   operation → LLM emits the structured task → state policy executes),
   honestly labeled as task specification, never as one-shot motor
   imitation.

Doctrine, updated: **agents for improvement, MPS for fast hypotheses,
NVIDIA for foundation models, corrections from the expert, state for
reliable transfer, pixels for generalization.**

## Two scar-tissue warnings

- Watch for **smooth-but-timid** convergence (seen in the SmolVLA rung: the
  smoothest, best-tracking checkpoint grasped least — mode averaging). If
  agents plateau smooth, weight the grasp phase explicitly via the margin
  receipts instead of adding training steps.
- Non-monotonic checkpoints are normal (first contacts appeared at update
  1,000, vanished by 2,500): evaluate rollouts at several checkpoints and
  select by rollout metric, never by loss.
