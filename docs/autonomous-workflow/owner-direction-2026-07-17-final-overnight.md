# Owner Direction — Final Overnight Exploration (2026-07-17 ~02:15–10:00 CDT)

Recorded ~02:15 CDT by Claude at the owner's explicit chat instruction. This
is the last exploration window before the sim2claw fork. Task-ordering
source, not an authority source; each lane still runs its own reviewed
ceremony (fork-lane work uses the lightweight RUN_RECEIPT style).

## New owner resource grant (recorded)

The owner explicitly authorizes, for this window and the weekend:

- **Brev external compute and the network access it requires** (instance
  provisioning, pinned-repo clones, HF model/dataset pulls, artifact
  upload/download), scoped to the F1 lane below. Tonight's spend cap: $100
  of the $500 credits; per-run spend logged; **all instances stopped and the
  Brev inventory receipt written by 09:30** regardless of outcome.
- The NVIDIA box and local Macs without restriction for simulation/training.
- Hardware motion remains closed tonight. The leader-arm teleop fallback is
  documented below for the weekend, not executed now.

## The fact this window is built on

T20.43c-R2 (Reviewer 318): ACT-on-R0 is a clean trained negative that learned
strict grasp, unassisted lift (37.7–45.7 mm), unsupported hold, and lower at
every late checkpoint, failing only `release_final_contact_clear` (update
5000 also failed retreat). Receding-10 lost grasp entirely (0.502 mm) —
chunk-50 is the working execution semantics. **Gate C is one phase away.**

## F0 — Close the release gap (local lane, start immediately)

Design from the preserved release-phase counterexample. Candidate mechanisms
to check, in order:

1. **Window-tail under-representation:** with unpadded horizon-50 windows on
   244-frame episodes, the final frames appear in almost no training windows
   (the last frame in exactly one of 195 starts). Release is structurally
   undertrained. Fixes: regenerate/augment episodes with ~50 post-release
   dwell/retreat frames so release sits mid-window (the constructive expert
   makes this cheap), and/or admit tail-padded windows, and/or oversample
   late-start windows via the existing task-phase mixture buckets.
2. **Open-gripper normalization headroom:** T20.12 found the open command at
   92.43% versus an 81.03% normalizer max on the old stats. Verify the open
   command sits inside the R0 MEAN_STD envelope; if not, that is the bug.
3. **Release-phase mixture weight and gripper loss weight** (the T20.35x
   physical-weighting precedent applied to the release phase).

Then exactly one bounded corrective ACT rung — either a fresh 10k-update run
on release-fixed data or a short (~2k) continuation from the update-10000
checkpoint with release-weighted mixture, whichever the diagnosis favors —
with rollout-primary evaluation, chunk-50 primary. **A Gate C pass triggers
immediate preservation, kit fold, and the F2 serving rehearsal.**

## F1 — π0.5 on Brev A100 (parallel lane)

ABEJA-parity full fine-tune of cached `pi05_base` on the R0 dataset
(release-fixed data if F0's data lands in time, else R0 as-is): single
A100-80GB, ~5k steps, pinned stack per the kit's THIRD_PARTY versions,
on-instance CPU-MuJoCo dual-semantics rollouts at fixed checkpoints,
compact receipts and best checkpoint returned; multi-GB trees stay on the
instance or object storage, never in git. Purpose: the owner's
"harder-to-serve-on-MPS" bet — π0.5's manipulation priors may solve release
naturally, and its checkpoint is servable all weekend through the gateway.
Budget/teardown rules above; completion-budget check before launch; one run,
no automatic retry.

## F2 — Gateway serving rehearsal (after any grasping checkpoint exists)

Serve the best checkpoint (ACT or π0.5) from a policy server — pinned
LeRobot async inference, NVIDIA box or Brev endpoint — to a MuJoCo sim
client over the network, timing fields recorded. This is the demo plumbing
proven before the demo matters.

## F3 — Morning fold (by 09:45)

K2/kit refresh with the R2 result, tonight's outcomes, and receipts; stamp
the fork name **sim2claw — "Simulation to Closed-Loop Autonomous Workcell"**
into the kit README and annex (owner may veto by morning); morning summary;
sync pointers; push; tag `freeze-2026-07-17-hackathon-fork`.

## Teleop fallback (weekend, documented, not tonight)

If sim-trained policies fail the physical demo by Saturday evening: one
owner-present leader-arm session, 25–50 teleop episodes of the single atomic
task at a fixed pose, ABEJA-parity fine-tune on Brev with the real frames,
honest labeling as teleop-assisted data (outside the autonomous-flywheel
claim). Spec the session checklist in the kit so invoking it costs an hour,
not a day.

## Rules

F0 and F1 run in parallel under separate workers; F0 outranks F2, F1 does
not block on F0. Receding-10's grasp fragility is a weekend investigation,
not tonight's. No hardware motion. Prefer one completed lane over two
half-finished ones; if forced to choose, F0 is the priority — the cheapest
path to the project's first Gate C pass.

## Addendum (06:35 CDT) — F0c corrective rung survives the fold; F1 outcome recorded

Checkpoint findings at 06:23: F0/F0a/F0b verified a complete diagnosis chain
(20-frame release localization, tail observation aliasing, and a terminal
cadence negative — re-observation at frame 176 widened retreat contact from 1
to 17 frames yet `release_final_contact_clear` still fails; the policy holds
until the anchor is back at desk height). The one authorized corrective ACT
rung was never consumed. Separately, the F1 lane completed off-ledger in the
Codex workspace `~/Documents/Codex/2026-07-17/sim-link-f1-pi05-brev`: the sole
5,000-step `pi05_base` full fine-tune on one A100-80GB cost $5.526 with
confirmed teardown and zero remaining resources; best checkpoint (step 1,000,
chunk-50) lifted 37.519 mm and failed only `grasp_hold_strict_v2`. Signed
receipts live in that workspace; the next ledger fold should ingest them.

The owner direction therefore clarifies:

1. **The single authorized corrective ACT rung (F0c) remains open after the
   F3 fold and freeze tag.** The tag is a source boundary, not a stop order;
   an F0c result lands as a post-tag addendum and day-one evidence for the
   fork. Deadline discipline: completion-budget check first; if the budget
   does not fit before ~10:00, F0c becomes the fork's first training task
   instead, exactly as specced.
2. **F0c design, from the verified diagnosis:** attack the learned release
   deficit with release-targeted data, not cadence. Preferred: a short
   (~2,000-update) continuation from the retained update-10,000 R2 checkpoint
   on a release-corrected view — post-release dwell/retreat augmentation via
   the turnkey W2-style regeneration or a release-phase-oversampled mixture
   with gripper-weighted loss (T20.35x precedent) — chosen by whichever the
   evidence favors after checking open-gripper normalization headroom. One
   bounded run, rollout-primary chunk-50 evaluation, no retry.
3. **F1 is closed cleanly within its cap** and needs no further action;
   $494 of Brev credit remains for the weekend.
