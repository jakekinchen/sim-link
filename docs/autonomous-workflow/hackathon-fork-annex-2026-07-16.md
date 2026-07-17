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

- 96 GB Macs: local ACT/SmolVLA training and all simulation work.
- The NVIDIA box ("800 GB" is almost certainly system RAM, not VRAM): episode
  hub, central evaluator, and RealSense **depth as observer-role only**
  (librealsense is first-class on Linux; depth stays out of policy inputs).
- $500 Brev credits: reserve for one π0.5 fine-tune (ABEJA-parity reference
  is ~5–20 A100-hours) only after local candidates prove the dataset.

## Camera decision (2026-07-16)

Policies remain RGB + joint-state (Gate A parity with sim training). The D405
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

1. Clone at tag `freeze-2026-07-16-hackathon-fork`; run the kit quick start.
2. Run the T20.43c ACT ready-package — it validates the transplanted stack
   end-to-end and answers this project's biggest open question as a side
   effect.
3. Freeze the fork's held-out scene/seed set before anyone trains.
4. Per-device camera RGB checklist (resolution/fps/latency); stand up the
   episode hub and central evaluator; post the expert to the leaderboard.

## Two scar-tissue warnings

- Watch for **smooth-but-timid** convergence (seen in the SmolVLA rung: the
  smoothest, best-tracking checkpoint grasped least — mode averaging). If
  agents plateau smooth, weight the grasp phase explicitly via the margin
  receipts instead of adding training steps.
- Non-monotonic checkpoints are normal (first contacts appeared at update
  1,000, vanished by 2,500): evaluate rollouts at several checkpoints and
  select by rollout metric, never by loss.
