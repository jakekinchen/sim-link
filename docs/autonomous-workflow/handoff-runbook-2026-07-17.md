# sim2claw Day-One Runbook (2026-07-17)

Recorded ~10:40 CDT by Claude at the owner's instruction, after all agent
lanes closed. This is the four-person start plan. Task-ordering only.

## Clone point — use `sim2claw-genesis`, the final authoritative tag

Clone/export at **`sim2claw-genesis`**. It supersedes both earlier tags:
`freeze-2026-07-17-hackathon-fork` predates the F0c package and F1 fold, and
`handoff-2026-07-17-f0c-packaged` predates this runbook and the weekend
compute-and-model doctrine. Kit export flow:
`reconstruction-kit/scripts/kit.py verify && ... export` per QUICKSTART.

## State inherited at handoff

- ACT (R2, update-10000): grasp, lift 37.7–45.7 mm, hold, lower — fails only
  `release_final_contact_clear`. Diagnosis chain F0/F0a/F0b proves the
  deficit is learned, not cadence. Gate C is one trained phase away.
- π0.5 (F1, step-1000): 37.5 mm lift, fails only strict hold. $5.53 spent;
  teardown receipted; **$494 Brev credit remains.**
- F0c — the release-targeted ~2k continuation from the R2 update-10000
  checkpoint — is fully packaged as the fork's first training task
  (`configurations/robot_lab/f0c_release_targeted_continuation_spec.json`,
  Brief 234, Reviewer 327). The fork must supply: a reviewed runner, the
  checkpoint bytes, and its own fork-native RUN_RECEIPT authority.
- **Checkpoint acquisition gotcha:** the R2 checkpoint tree is gitignored and
  lives only at
  `outputs/robot_lab/t20_43c_r2_act_replacement_run_001/` on the Mac Studio.
  Copy it (or at minimum the update-10000 checkpoint) to the F0c machine and
  verify its signed tree identity before running.
- Loose ends carried forward: W3 portability rehearsal is 0-of-3 (it
  completes naturally as each member bootstraps); W5 gateway is
  transport-only evidence (needs the serving loopback).

## Four lanes for four people

1. **Fork + F0c (highest value; Kelly).** Export at the handoff tag, run the
   W1 bootstrap, copy the R2 checkpoint, build the F0c runner per spec, run
   the one bounded continuation, chunk-50 rollout evaluation. Expected ~2 h;
   this is the most likely first Gate C pass in project history.
2. **Hub + evaluator (person 2).** Stand up the episode hub and CPU-pinned
   frozen evaluator from the W4 assets; freeze the fork's held-out scene/seed
   set BEFORE anyone trains; post the constructive expert as leaderboard
   entry #1. Their bootstrap doubles as a W3 instance.
3. **NVIDIA box (person 3).** `nvidia-smi` first (settle the "800 GB"
   question); host the hub; finish W5 into a real serving loopback (policy
   server → sim client); RealSense depth as observer-role. Their bootstrap
   is another W3 instance.
4. **Physical/demo lane (person 4).** Camera mounts per the RGB census
   (D405 UVC + C922 fallback), AprilTag mat placement, demo scene build,
   and the teleop-fallback session checklist kept warm but unused.

## Budget and doctrine reminders

Brev: $494 remains and is a standing lane at ~$5.5 per π0.5 run (soft cap
~$50/day, always the F1 receipt pattern). After F0c, launch π0.5 iteration
2 on Brev with release-fixed data and early stopping near step 1,000. Full
compute-and-model doctrine: see the annex's "Weekend compute-and-model
doctrine" section (state-first demo path via AprilTag poses; VLAs as the
robustness/sim2real bet, off the demo critical path).
Three rules everywhere: held-outs frozen first, every claim has a replayable
artifact, evaluation code owned separately. Chunk-50 is the demo semantics.
North star: language-commanded pick-and-place live on hardware; chess is the
encore only at ≥85% per-move reliability.
