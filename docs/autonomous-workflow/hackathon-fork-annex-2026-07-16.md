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
   (b) Markov-complete state: add joint/object velocities and previous
   action → (c) ACT `n_obs_steps` 2–4 (a config knob, not an architecture)
   → (d) 8–16-step learned history (small GRU/state transformer) only if
   (a–c) leave signed evidence demanding it. Same scene, same data, same
   evaluator across variants — the ablation is itself a demo asset.
2. **Auto-correction episodes (the best new mechanism).** Candidate rollout
   fails → evaluator locates the first failed margin → MuJoCo forks shortly
   before it (verified T18.4 branching) → the geometry expert completes the
   corrected tail → one correction record: failed prefix as context,
   expert tail as supervision (mask on the tail only), labeled
   `context_role/context_policy/failure_predicate/correction_owner/
   supervision_mask`. Admission to training only through the design-rule-8
   gate (mixture + authority decision). Failures are context; corrections
   are targets — no fast weights required.
3. **Demo hierarchy with honest labels.** Level 1: pure learned policy
   passes strict-v2. Level 2: labeled hybrid — learned policy through
   lower, explicit state controller for release/verify/retreat (given ACT
   fails only release, this is the near-guaranteed working demo and its
   runs generate correction episodes). Level 3: teleop, proving only the
   gateway and calibration. Never blur the labels.
4. **NVIDIA lane ordering (amended from the proposal).** π0.5
   release-fixed continuation stays the *primary* NVIDIA run — proven
   end-to-end at ~$5.5 — and GR00T N1.7 runs as a **bounded parallel
   challenger**, never a gate on π0.5: official SO-100/101 smoke → dataset
   conversion (LeRobot **V3→V2** — budget real time; camera-key/count
   mismatches killed a prior VLA attempt) → short pilot with early
   evaluation → same frozen evaluator. One VLA campaign at a time on the
   lane; SmolVLA stays parked. GR00T fine-tune wants 40 GB+ VRAM (Brev
   A100 or the local box if real); inference 16 GB+ fits the gateway.
5. **Experiment registry, not a framework.** Extend `RUN_RECEIPT.json` with
   `parent_checkpoint`, `hypothesis`, and `promotion_decision`; render the
   hypothesis tree and leaderboard through the *existing* studio server
   rather than building an ENPIRE clone. The six-act demo narrative
   (failure → hypothesis → parallel training → before/after → perturbation
   → hardware switch) is assembled from artifacts every run already emits
   (mirrors, margins, receipts) — no bespoke theater code.
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
