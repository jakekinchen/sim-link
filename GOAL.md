# GOAL

## Active Mission

Complete SceneSmith's first reliable SO-101 grasp of one lightweight anchor
object through a bounded, Git-tracked goal loop. Correct the simulation's
gripper/contact semantics, obtain a strict unassisted MuJoCo grasp, calibrate
the physical twin under finite owner-present permits, and compile immutable
grasp experience before any training. Continue through training and policy
comparison only after the central authority composer grants readiness. Update
the active ledger at every verified slice and continue until the acceptance
criteria are met or a genuine human-authority blocker is recorded.

The physical SO-101 follower must never be opened before verified T16.5a or
commanded outside the exact verified T16.6 session permit. The final owner
confirmation covers only the initial no-op-equivalent then one-small-joint-
delta-and-return permit under an active owner-presence lease. Neural-policy,
contact-stabilized, controller-assisted, supervised-motion, and physical-robot
proof states must remain distinct.

## Active Run Window

- Actual start: `2026-07-15T07:27:47-05:00`.
- No new major slice after: `2026-07-15T22:42:47-05:00`.
- Hard closeout: `2026-07-15T23:27:47-05:00`.
- Owner evening extension recorded at `2026-07-15T10:20:00-05:00` for the
  tonight MVP demo composition in the MVP execution plan; scope, gates, and
  all closed authorities are unchanged.
- This owner-requested continuation is simulation-only diagnostic and bounded
  training work under M20. The active loop is
  `docs/autonomous-workflow/t20-capability-ladder-goal-loop.md`; it starts at
  T20.35's single rank-16 Gate B discriminator and follows only the lowest
  unmet evidence-routed gate in `docs/sim-link-mvp-execution-plan.md`. It
  grants no hardware,
  physical-transfer, promotion, external-compute, or Brev authority. Historical
  physical-session notes below are retained only as consumed-gate history.
- Reviewer 098's one-session gate was consumed and closed at `08:42` CDT after
  the candidate rejected live camera-frame fields. Reviewer 101 preserves the
  rejected boundary; no second session is allowed under that gate. After the
  verified Brief 076 correction, Reviewer 103 opens one new finite session from
  `08:55` through `09:30` CDT only after remote confirmation and fresh preflight.
  That session was consumed and closed at `08:56` after the frame adapter passed
  and the next strict camera-audit boundary rejected. Brief 079 verifies the one
  permitted narrow offline correction. Reviewer 106 opens one fresh finite
  session from `09:10` through `09:45` CDT only after remote confirmation and
  complete fresh preflight. That session produced a verified candidate at
  `09:12` and closed cleanly. Brief 082 corrects the exact redacted-review
  hardware-profile contradiction, and Reviewer 108 accepts the session as a
  static-pose bracketed observation. Reviewer 109 issues its reviewed semantic
  input bundle. Brief 084 and Reviewer 110 verify private source-bound frame
  retention for a future session; the accepted 09:12 session remains v1 and
  still has no current pixel bytes. Reviewer 111 opens one distinct fresh
  current-frame session from 09:58 through 10:38 CDT only after its transition
  is confirmed on origin. That session is consumed and closed: Reviewer 112
  accepts the zero-drift private-v2 bracket and current camera roles, while
  rejecting sorting-scene match because the required cubes and trays are not
  visible.
- Prior windows are retained in
  `docs/autonomous-workflow/project_state.json`.

## Current Milestone

M20 - Simulation-Only Clean Supervision And Capability Falsification

## Current Slice

T20.17 is `verified` as a bounded negative clean-base result; T20.18 is
`verified` through Brief 149, T20.19 is `verified` through Brief 150, and T20.20
is `verified` through Brief 151; T20.21 is `verified` through Brief 152, and
T20.22 is `verified` through Brief 153. T20.23 is `verified` through Brief 154
and Reviewer Decision 184: the source-bound LeRobotDataset contains only six
nominal successes plus four strict-success recovery branches; near-failures,
failures, and seeds 6-7 remain outside training and statistics. Central
composition grants only `simulation_training_ready`; no optimizer ran, and a
separate brief must activate the frozen 500-update local-MPS campaign. Brief
155 now opens T20.24 for that exact campaign and one frozen unassisted strict-v2
evaluation each on seeds 6 and 7. T20.24 is now `verified` negative through
Reviewer Decision 185: 500 finite updates yielded zero strict contact on both
seeds and 0/2 strict successes. No result was promoted; the next safe slice is
offline output/failure localization before any additional optimizer budget.
Brief 156 now opens T20.25 to compare the frozen T20.17 and T20.24 requested
actions and visited states against exact held-out source trajectories on seeds
6 and 7. T20.25 is now `verified` through Reviewer Decision 186: recovery
training regresses sampled frame-zero MAE but improves sampled pre-contact MAE,
while the clean adapter's prior action hash is not cross-process reproducible.
Training attribution is therefore blocked pending repeated frozen-inference
variability measurement; no optimizer or policy acceptance follows.
Brief 157 now opens T20.26 for two independent frame-zero inference batches per
adapter on one identical seed-6 observation. It applies no action, runs no
optimizer, and T20.26 is now `verified` through Reviewer Decision 187. Both
adapters are bit-exact for fixed-seed repeats within and across processes;
distinct inference seeds span 0.18478 / 0.14797 rad. Future training comparison
must therefore pair multiple inference seeds. No policy is accepted.
Brief 158 now opens T20.27 to compare the already captured clean/recovery
frame-zero actions against the exact source action over five paired inference
seeds. T20.27 is now `verified` through Reviewer Decision 188: recovery is
worse on all 5/5 seeds, raising source-action MAE by 0.11094 rad. Only gripper
improves marginally; arm joints regress. No new training is justified yet.
Brief 159 now opens T20.28 to reconstruct the exact clean and recovery-campaign
sampler orders and quantify early-phase exposure. It runs no model or optimizer
and T20.28 is now `verified` through Reviewer Decision 189. Recovery saw 26
approach and 3 frame-zero samples versus clean's 14 and 0, so low early-phase
exposure is rejected. Dataset quantile/postprocessor shift is next.
Brief 160 now opens T20.29 for a five-seed postprocessor-only quantile
counterfactual holding normalized candidate outputs fixed. It runs no model or
optimizer and predeclares no statistics-freezing conclusion. T20.29 is now
`verified` through Reviewer Decision 190: recovery action quantiles reproduce
the observed frame-zero regression within 0.00208 rad in the bounded
postprocessor-only counterfactual. Full training causality remains unproven;
freezing nominal action quantiles is the next separately reviewed ablation.
Brief 161 opens T20.30 to materialize and centrally authorize the exact
recovery dataset view whose only statistics change is replacing action q01/q99
with the clean nominal values. It runs no model or optimizer; the actual
same-seed 500-update ablation remains a separate T20.31 slice.
T20.30 is now `verified` through Reviewer Decision 191: all five dataset files
are separately copied, only `meta/stats.json` differs, and only action q01/q99
within that file use clean nominal values. Central composition grants exactly
`simulation_training_ready`; no model or optimizer ran.
Brief 162 opens T20.31 for the exact same-seed 500-update local-MPS campaign
and one frozen unassisted strict-v2 evaluation each on held-out seeds 6 and 7.
No policy is accepted or promoted by the brief.
T20.31 is now `verified` negative through Reviewer Decision 192: 500 finite
updates reduced loss from 1.544 to 0.413, but both frozen held-out policies made
zero strict contact and achieved 0/2 strict successes. The previous window's
no-new-major-slice cutoff passed after that verification.
Brief 163 now opens T20.32 in the fresh owner window recorded above: capture
complete requested/applied action and state traces for the frozen T20.24 and
T20.31 adapters, localize the earliest closed-loop divergence against the exact
source trajectories on held-out seeds 6 and 7, and run one bounded
training-seed closed-loop reproduction probe per adapter as capability-ladder
Gate C evidence. No optimizer, dataset, statistics, twin, hardware, or
authority change is permitted; the verified outcome routes the next gate in
the MVP execution plan.
T20.32 is now `verified` through Reviewer Decision 193 and implementation
boundary `7bbf7cf`. Six complete 244-frame traces reproduce all four frozen
held-out action hashes exactly. Both adapters fail the seed-0 reproduction
probe and already exceed the declared action threshold at frame zero; state
divergence begins at frame one. The evidence therefore rejects a Gate C-first
cadence/chunk/feedback correction and routes T20.33 to Gate B
one-batch-memorization/model-plumbing proof before any additional optimizer
campaign.
T20.33 is now `verified` negative through Reviewer Decision 195. The one
predeclared fixed-batch run completed 500 finite updates, but its five-seed
objective ratio is `0.528248` rather than the required `0.10`, and every
decoded horizon-50 chunk exceeds the `0.05` rad maximum-error gate (observed
range `0.843707` to `1.250647` rad). Gate B remains unmet. Gate C and broader
campaigns stay closed; the next task is optimizer-free base-versus-adapter
plumbing and objective-to-inference localization.
T20.34 is now `verified` through Reviewer Decision 196. The saved adapter is
not dead or misbound: 321,688 values are nonzero, all five prior decoded hashes
replay exactly, mean action error improves on every seed by 0.0553-0.0826 rad,
and movement-to-target cosine is positive on every seed. The remaining Gate B
fault is insufficient rank-4 capacity or optimization budget. The next safe
discriminator is one separately authorized same-batch/same-seed rank-16
ablation, not Gate C work or a broad campaign.
Brief 166's T20.35 pre-run implementation is remotely preserved at `579855f`
and accepted by Reviewer 198. Its signed specification differs from T20.33
only in artifact identity metadata plus LoRA rank/alpha 4 to 16, and central
composition grants only `simulation_training_ready` through the active window.
Exactly one local-MPS run is next; no model load or optimizer occurred at the
pre-run boundary.
T20.35 is now `verified` negative through result boundary `fd9399d` and
Reviewer Decision 199. The sole counted rank-16 attempt completed 500 finite
updates and improved the objective ratio from `0.528248` to `0.155307`, but
still missed the `0.10` gate; all five decoded chunks also missed the `0.05`
rad maximum-error gate. Gate B remains closed. The next safe task is the
optimizer-free T20.35a audit that enumerates the exact modules and tensors
wrapped by PEFT before another learning-rate or update-budget rung.
T20.35a's tensor enumeration is preserved at `d1109ae8`, but its generic
five-pathway decision is superseded by T20.35b's pinned-source correction
`446a0686`, implementation `b630930`, and Reviewer Decision 201. PI0.5
intentionally has no `state_proj`; its real modules are action in/out plus
`time_mlp_in/out`. The default PEFT regex uses stale `action_time_mlp` names,
so both real time-MLP layers are genuinely uncovered. The next safe
discriminator remains a separately authorized no-LoRA expert-only unfreeze
capacity ceiling, now grounded in the actual PI0.5 module tree.
Brief 169's T20.35c pre-run implementation is remotely preserved at `82614ec`
and accepted by Reviewer 202. Spec `6c10a1c7...` preserves the exact T20.33
batch, learning rate, 500 updates, seeds, processors, and gates while replacing
PEFT with a PaliGemma-frozen, complete-expert-plus-real-projections trainable
boundary. Central decision `75dc9c7d...` grants exactly one local-MPS attempt;
no model load or optimizer occurred at the pre-run boundary.
T20.35c is now `verified` mixed-negative through result `f6f6b024`, run
`9b1af8ee`, and Reviewer Decision 203. The sole expert-only attempt completed
500 finite updates, passed the objective gate at ratio `0.004252`, and improved
all five decoded seeds over rank 16. Gate B still fails because maximum action
errors remain `0.091908` to `0.150321` rad versus the `0.05` limit. T20.35d is
next as an optimizer-free exact checkpoint replay and per-joint/per-timestep
residual localization; no additional training or Gate C work is justified yet.
T20.35d is now `verified` through exact replay report `13b08e70` and Reviewer
Decision 205. All five hashes reproduce. Of 366 errors above `0.05` rad, only
9.29% are at chunk boundaries; wrist roll plus gripper account for 77.87%,
while shoulder pan and elbow account for none. The signed single-joint
classifier still says distributed because wrist roll alone is 44.81%, so
T20.35e must correct that model-free classification before selecting a decoder,
normalization, projection, or gate correction.
T20.35e is now `verified` through correction `f2a8aa80`, implementation
`292a109`, verifier correction `3013ded`, and Reviewer Decision 206. The
immutable T20.35d report remains unchanged. Wrist roll plus gripper hold
285/366 exceedances (77.87%), passing the declared 75% top-two threshold while
neither the single-joint nor boundary
threshold passes. The corrected class is multi-joint output-channel
concentration. T20.35f is next as a model-free audit of normalized-space
residuals and target saturation for those two channels before any decoder,
normalization, projection, threshold, training, or Gate C correction.
T20.35f is now `verified` through audit `85c24c5c`, implementation `dea54fb`,
and Reviewer Decision 207. Exact PI0.5 quantile-space conversion preserves all
164 wrist-roll and 121 gripper physical exceedances. The normalizer does not
clip and neither channel hits a physical bound. Systematic bias explains
84.81% and 82.33% of their normalized squared error, versus 15.19% and 17.67%
seed variance. T20.35g is therefore next as a separately reviewed,
inference-only denoising-cadence discriminator against the pinned 10-step
default; no new training or Gate C work is justified yet.
Brief 173's T20.35g pre-run implementation is remotely preservation-ready at
`88602b0` and accepted by Reviewer 208. Spec `be1c50f3...` and one-use permit
`ca3dbd3f...` freeze the expert-only checkpoint, exact batch, five seeds, and
10/20/50-step comparison. The 10-step row must reproduce all prior hashes
before candidate interpretation. This boundary authorizes one local-MPS
load/inference attempt only; no optimizer, mutation, rollout, or Gate C work
has occurred.
T20.35g attempt 001 `788015fa...` consumed its permit but failed under Python
3.14 after CPU checkpoint validation and before model construction or inference.
The old permit is not reusable. Runtime preflight `d476382b...` proves the same
pinned PI0.5 config parses under Python 3.12 without checkpoint/model access.
Correction `b077d19`, replacement spec `44076248...`, permit `b3078ea0...`, and
Reviewer 209 authorize exactly one distinct Python 3.12 replacement attempt;
the cadence, seeds, hashes, gates, and no-optimizer boundary are unchanged.
T20.35g is now `verified` negative through signed result `57f1f0dd...`, result
boundary `48e2b3f`, and Reviewer Decision 210. The 10-step row reproduced all
five baseline hashes exactly. Neither candidate is directionally positive:
20 steps worsened worst/mean error from `0.150321`/`0.030990` rad to
`0.159251`/`0.033813`, and 50 steps worsened them to
`0.167722`/`0.035237`. Gate B remains closed. T20.35h is next as a model-free
leave-one-seed-out output-bias correction ceiling; no additional model load,
optimizer, training, or Gate C work is justified.
Brief 174 opens T20.35h as that exact model-free ceiling. It binds the signed
10-step chunks and target, fits each held-out seed only from the other four,
and compares a six-channel global decoded-action offset with a
time-and-channel-conditioned offset. A post-hoc ceiling can route a later
model-internal correction but can never itself pass Gate B or become a policy.
T20.35h is now `verified` mixed-negative through artifact `63e1181b...`,
implementation `68b7115`, and Reviewer Decision 211. A global channel offset
improves worst/mean error to `0.113302`/`0.019781` rad but leaves 159
exceedances. The time-conditioned offset lowers mean error to `0.017710` and
exceedances to 96, yet its worst fold is `0.136460` rad. Neither ceiling passes,
so T20.35i is next as model-free seed/channel residual-variance localization.
Brief 175 opens T20.35i with the exact time-conditioned held-out folds and raw
10-step chunks as immutable sources. It classifies the 96 remaining
exceedances by seed, channel, timestep boundary, seed-channel pair, and decoded
pairwise spread under frozen 50%/75%/60% concentration thresholds. Only a
distributed classification may route a separately reviewed initial-noise-scale
discriminator; this slice has no model or correction authority.
T20.35i is now `verified` through report `ac87de7b...`, implementation
`aa15de8`, and Reviewer Decision 212. All five seeds retain failures; the top
two seeds hold 56.25%, the top two channels 67.71%, and boundaries 31.25%, all
below their concentration gates. Seventy-six unique positions have failures
and raw decoded spread reaches `0.183018` rad. The result is distributed and
routes T20.35j to one separately reviewed inference-only initial-noise-scale
discriminator; Gate B remains closed.
Brief 176 opens T20.35j. It freezes initial-noise scales `1.0`, `0.5`, and
`0.0`, the existing 10 denoising steps, exact expert-only checkpoint/batch,
five seeds, source sampler hash, baseline hashes, and unchanged 0.05-rad Gate B
threshold. Scale 1.0 must reproduce before candidates count. A separate
pre-run review and remote-preserved one-use permit are required before one
local-MPS inference-only attempt; no optimizer or Gate C authority exists.
T20.35j pre-run implementation `ed05689`, spec `a3dc0acb...`, permit
`545a71c6...`, and Reviewer Decision 213 are remotely preservation-ready. Five
focused and 86 relevant tests pass; spec/permit verification agrees under both
configured Python runtimes. Exactly one Python 3.12 local-MPS model-load and
inference attempt is authorized after remote confirmation. No model,
checkpoint tensor, inference, optimizer, mutation, or rollout has occurred at
this boundary.
T20.35j is now `verified` directionally positive but Gate-B-negative through
result `e9bbff84...`, result commit `06b3a0a`, and Reviewer Decision 214. The
exact scale-1 baseline reproduced. Scale 0.5 reduced worst/mean/spread from
`0.150321`/`0.030990`/`0.046392` rad to
`0.084120`/`0.024630`/`0.018129`; scale 0.0 reduced them to
`0.073360`/`0.024130`/`0.0`, but neither candidate met the 0.05-rad action
gate. Brief 177 opens T20.35k as a model-free sampler/noise-distribution audit
of the exact active PI0.5 source, including the six active versus 26 padded
action dimensions. Gate B and Gate C remain closed.
T20.35k is now `verified` through audit `bc9f0845...`, implementation
`357cd6e`, and Reviewer Decision 215. The exact active runtime uses the same
standard-normal sampler for training and inference, with the expected affine
Beta training-time contract and 10-step Euler path. It also pads six supervised
actions to 32, injects stochastic noise into all 32 through the shared action
projection, and truncates direct loss and returned actions to six. This is an
exposure mechanism, not causal proof. Brief 178 opens T20.35l to evaluate only
the two mixed active-six/padded-26 noise masks while reusing T20.35j's signed
all-normal and all-zero endpoints. No optimizer or Gate C authority exists.
T20.35l pre-run implementation `2f04395`, spec `4c346688...`, permit
`5b990e78...`, and Reviewer Decision 216 are preservation-ready. Sixty relevant
tests and 17 subtests pass; spec/permit verification agrees under Python 3.11
and 3.12. After this review is confirmed on origin, exactly one Python 3.12
local-MPS model-load/inference attempt may evaluate the two mixed masks. No
model, checkpoint tensor, inference, optimizer, mutation, or rollout has
occurred at this boundary.
T20.35l is now `verified` joint-positive but Gate-B-negative through result
`b4fc6060...`, result commit `1040478`, and Reviewer Decision 217. Removing
padded noise alone lowers worst error from `0.150321` to `0.114173`; removing
active-six noise alone lowers it to `0.066398`, the best condition, while
all-zero reaches `0.073360`. Both mixed masks improve worst/mean/spread, but no
condition meets 0.05 rad. Brief 179 opens T20.35m as a model-free signed 2x2
interaction audit before any new inference. Gate B and Gate C remain closed.
T20.35m is now `verified` through audit `83105424...`, implementation
`2ba6d8e`, and Reviewer Decision 218. Active noise increases worst error by
`0.040813` with padded zero and `0.083923` with padded normal; the worst-error
interaction is `0.043111`. Active noise is harmful at both padded settings for
worst, mean, and spread, while padded noise changes sign for the two accuracy
metrics. Brief 180 opens T20.35n to inherit active-scale 0 and 1 with padded
noise normal and evaluate only active scales 0.25 and 0.5. No optimizer or Gate
C authority exists.
T20.35n pre-run implementation `04f7d3b`, spec `155d9336...`, permit
`f821bd57...`, and Reviewer Decision 219 are preservation-ready. Fifty-seven
relevant tests and 24 subtests pass; spec/permit verification agrees under
Python 3.11 and 3.12. After remote confirmation, exactly one Python 3.12
local-MPS attempt may evaluate active scales 0.25 and 0.5 with padded noise
fixed normal. No model, checkpoint tensor, inference, optimizer, mutation, or
rollout has occurred at this boundary.
T20.35n is now `verified` endpoint-optimal but Gate-B-negative through result
`d3e6e5d9...`, result commit `4e37e19`, and Reviewer Decision 220. With padded
noise fixed normal, worst error rises monotonically from `0.066398` at active
scale 0 to `0.082665`, `0.102040`, and `0.150321` at scales 0.25, 0.5, and 1.
Further active-scale tuning is rejected. Brief 181 opens T20.35o to instrument
the exact active-zero/padded-normal 10-step trajectory and compare each learned
velocity with the deterministic single-target straight-flow velocity. Gate B
and Gate C remain closed.
Brief 145 established T20.17's first boundary at
`af317bc`; its second at `1f5154a`; and its third at `cf1d05d`: preserve the
compact bespoke IP (content-addressed contracts, strict grasp semantics,
geometry-derived episode generation, the SO-101 processor, and thin
authority/stack locks); delete only unreferenced test-only modules; then
replace shadow-preprocessing derivation by invoking the pinned PI0.5 processor
on a source-bound actual `LeRobotDataset` sample and hashing its finite output
descriptors. This creates no model, training, or policy evidence. Historical
artifacts remain immutable, no clean-base training starts until a source
dataset—not a fixture—satisfies the new LeRobot-native boundary. Its fourth
boundary is verified at `1aceebe`: the live constructive geometry/contact
primitive is named and the eight dead T19 wrapper modules are retired, while
historical signed diagnostics remain immutable. Its fifth boundary is verified
at `61f2d8c`: the few-page owner-present/read-only/content-addressed contract
for a future LeRobot camera/robot adapter preserves historical physical
evidence and creates neither hardware objects nor motion authority. Its sixth
boundary is verified at `69416bc`: a front door, architecture/tech-stack,
requirements/contracts, decision index, and current-versus-historical guides
now route readers to canonical sources. Its seventh boundary is verified at
`890058b`: the separate Robo Scan repository is documented as a fail-closed
scene-scan/calibration artifact handoff, with no package import, artifact
ingestion, or physical claim. Its eighth boundary is verified at `d695ed4`:
the exact cross-repository integration, compatibility, and deduplication
roadmap preserved the separate Robo Scan thread's ownership until Brief 054 was
committed and accepted at `72eb02e`, then gated sim-link consumption on that
immutable receipt. Its ninth boundary
now independently validates only a copied receipt and emits a non-authorizing
candidate descriptor at `67daad9`/`cb4e5a0`/`d01416b`. It does not change system authority or the
broader T20.17 training task. Only repeatable strict semantic success can
promote a policy.

Brief 146 is verified at `81c9a25` and reviewed by Decision 176. It records the
owner-approved MVP cut and a sim-link-only dependency queue while Robo Scan
waits for its real metric-capture path. The completed T20.17 campaign used
clean `pi05_base`, exact source-dataset statistics from
initialization, a realistic bounded local update budget, and frozen unassisted
strict-v2 evaluation. Later planned tasks are state-fork recovery data, a small
discrete ensemble, an observer-role evaluator, a thin paired trace runner, and
timing evidence. No queued task inherits hardware, physical-transfer,
promotion, external-compute, or Brev authority from the plan. Brief 147 is
verified at `b826e3f` and reviewed by Decision 177: the six-episode LeRobot
training dataset is persistent, seeds 6-7 are frozen outside its statistics,
the complete local `lerobot/pi05_base` snapshot is byte-bound, and central
composition grants only `simulation_training_ready`. No model load, optimizer,
rollout, or policy result occurred at that boundary.
Brief 148 is verified through `dce1995` and reviewed by Decision 178. Official
LeRobot completed 250 finite rank-4 local-MPS updates from the clean base; the
frozen seed-6 candidate then ran 244 unassisted frames with zero projected or
assisted actions, no strict grasp contact, and 0.000307 mm lift. This is a
verified negative result, not policy acceptance. Brief 149 is verified through
`9b359a5` by Reviewer Decision 179. The exact failed candidate reproduced while
capturing 244 pre-action MuJoCo states; eight deterministic children produced
four recoveries, two near-failures, and two failures. The durable supplement
retains 1,290 child frames and 2,580 branch-rendered observations. Brief 150
activates T20.19's fixed 12-cell, same-seed discrete ensemble around the strict
approach recovery. Brief 150 is verified through `2436a14` by Reviewer Decision
180: 11/12 cells passed, while gripper scale 1.05 lifted 31.849 mm but failed the
full stable-hold and lower counts. This is an uncalibrated grid result. T20.20 is
verified through `50abb80` by Reviewer Decision 181. Its two roles share eight
strict-v2 predicates; complete positive/negative simulator fixtures agree,
while missing, privileged, spoofed, camera/VLM, malformed, and undeclared
evidence fails closed. This is not hardware observation or physical
qualification. Brief 152 is verified through `7f264ab` by Reviewer Decision
182. Its two separately signed synthetic traces match exactly, and nine fixed
diagnostics route `q0`, action, joint, clock, and event mismatches without
calibration or twin mutation. This is not paired real/sim evidence. Brief 153 is
verified through `98a79a2` by Reviewer Decision 183: one synthetic timing
certificate passes and eleven one-factor timing failures each block dynamics
attribution. Brief 154 verifies T20.23's narrow policy-data preflight and Brief
155 verifies its exact bounded training/evaluation successor as negative,
but the broader MVP exit remains unmet by the failed learned policy, absent real Robo Scan/I5
bundle, and absent newly authorized physical canary. No hardware, live-probe,
clock-sync, calibration/twin, optimizer, posterior, policy-acceptance, or
physical-qualification grant was created.

T20.9 is `verified` through Brief 129/Reviewer 159. The immutable seed-2 expert
actions reproduce the source trajectory exactly through the policy adapter:
zero action/state/object/contact divergence, no projection or assistance,
36.3853 mm lift, and all grasp/hold/lower counts pass. T20.7 still rejects the
oracle only because its release-clear gate treats a zero-force fixed-pad
collision pair as active contact, while the T17.5b source contract omits that
gate and T20.6 defines release by fingertip contact. T20.10 is `verified`
through Brief 130/Reviewer 160: the exact oracle now passes all gates under an
explicit force-bearing release basis while final retreat remains geometrically
clear; legacy T20.9 still verifies unchanged. T20.11 is `verified` through
Brief 131/Reviewer 161. All four models diverge at frame 0. PI0.5 isolates the
narrowest issue: 0.03097 rad initial non-gripper MAE but 0.75432 rad gripper
error. T20.12 is `verified` through Brief 132/Reviewer 162. All 732 actions
round-trip within 3.606e-9 rad versus 1e-8, and all six action dimensions have
equal loss weight. The supported fault is instead a broad checkpoint-normalizer
domain mismatch: shoulder lift, wrist flex, wrist roll, and gripper exceed its
observed min/max. T20.13 is `verified` through Brief 133/Reviewer 163. Its
train-only population statistics balance average target mean-square near 1.0
per joint and inverse-transform within 1.23e-9 rad, while held-out values remain
evaluation-only and unclipped. T20.14 is `verified` through Brief 134/Reviewer
164. Its exact 20-update local-MPS rung reduced initial gripper error from
0.75432 to 0.23898 rad, but initial non-gripper MAE regressed from 0.03097 to
0.74683 rad. The fixed seed-2 rollout retained zero strict-v2 frames and only
0.0003007 mm lift; five reviewed keyframes visibly show the gripper displaced
from the cube. T20.15 is `verified` through Brief 135/Reviewer 165. Its exact
2x2 frame-zero ablation isolates action postprocessing as the dominant arm
regression: 0.95872 rad non-gripper displacement versus 0.23586 from state
preprocessing and 0.26037 interaction. T20.16 is `verified` through Brief
136/Reviewer 166. Its no-training hybrid retained checkpoint state and arm
scaling while substituting dataset-derived gripper mean/std. The frame-zero
prediction passed at 0.03088 rad arm MAE and 0.12015 rad gripper error, but the
244-frame policy-owned rollout diverged to 0.90603 rad trajectory MAE, made
zero strict contacts, and lifted only 0.0003007 mm. Coordinate conversion and
simulator projection counts were both zero; five reviewed keyframes visibly
show the gripper below-left of the cube. The hybrid is retired. T20.17 is
pending for the next run window: bind a clean `pi05_base` source to dataset
statistics from initialization, scale source supervision and optimizer budget,
and grade progress on the T20.6 ladder while retaining strict success as the
only promotion gate. No learned policy is accepted. Hardware, physical
transfer, promotion, external compute, and Brev remain closed.

The paragraphs below retain earlier verified history and do not supersede the
canonical current task in `docs/autonomous-workflow/project_state.json`.

T16.5c is `verified` as a successful no-actuation diagnostic experiment with a
negative sorting-checkpoint transfer result. T19.0 is `verified` through Brief
095, T19.0b is `verified` through Brief 096, T19.0c is a verified negative
geometry search, and T19.0d verifies unilateral fixed-pad proxy contact. T19.0e
is `verified` through Brief 099 with bilateral explicit-pad contact in two
candidates but zero strict-v2 frames or geometry-eligible grasps. T19.0f is
`verified` through Brief 100: passive yaw/table settling is separated from
approach motion, six candidates pass the motion gate, but both bilateral
candidates still fail strict contact geometry. T19.0g is `verified` through
Brief 101: four wrist-roll-aligned candidates were reachable, two passed the
motion gate, but preserved wrist-flex tilt prevented all moving-pad contact.
T19.0h is `verified` through Brief 102 as a bounded negative result: no wrist
pose inside the existing ranges satisfies both the 0.95 anchor-x alignment and
0.1 vertical-component gates. T19.0i is `verified` through Brief 103:
eight horizontal y-axis poses are valid and two retain bilateral contact, but
both fail motion and strict contact geometry. T19.0j is
`verified` through Brief 104: selected-axis centering raises one bilateral
candidate above the strict span threshold, but normal alignment and preclose
motion still fail. T19.0k is `verified` through Brief 105: source-identical
diagnostics prove the fixed pad contacts the anchor top while the moving pad
contacts the side; normal convention and geom ordering are valid. T19.0l is
`verified` through Brief 106: geometry-derived aperture, object-center pad
height, and fixed-jaw clearance produce an exact two-pass unassisted MuJoCo
grasp with strict-v2 contact through hold, 40 mm lift, unsupported hold, and
lower, followed by a contact-clear final retreat. T17.1 is `verified` through
Brief 107: a signed immutable rollout/frame contract binds the grasp, twin, and
coordinate identities while quarantining the aggregate source projection
rather than calling it training data. T17.2 is `verified` through Brief 108: a
named canonical SO-101 processor keeps pure unclamped transform, fail-closed
validation, and requested-versus-executed safety limiting mechanically
separate. T17.3 is `verified` through Brief 109 as an immutable fixture-scoped
normalization/preprocessing bundle bound to actual cached processor parity; it
remains production-ineligible. T17.4 is `verified` through Brief 110: its
source-bound frame and hard-boundary segment compiler retains the incomplete
two-frame projection in quarantine, yielding zero eligible segments. T17.5 is
`verified` through Brief 111: its source-bound unpadded index yields zero rows
at horizons 5, 10, 15, and 50 without padding or inferred actions. The next
eligible offline slice is T17.5b, which must record the already-verified
geometry-derived scripted grasp as complete raw experience; it must first make
explicitly derived action variants fail-closed and verifiable rather than
mislabeling them as observed. T17.5b is `verified` through Brief 112: eight
deterministic unassisted episodes compile to 1,952 eligible frames, 88
hard-boundary segments, and 3,744 unpadded windows (including 120 at horizon
50), with zero quarantines. T17.6 is `verified` through Brief 114: all three
bounded legacy canary descriptors are reasoned quarantines (zero accepted
records), and its source-bound compiler view is explicitly empty. T17.7 is
`verified` through Brief 115: it traces 100 deterministic windows (25 at each
of horizons 5/10/15/50) across all eight scripted grasp rollouts from raw-frame
identity through compiler and window rows, with canonical actor-input/action
descriptor parity but no model call. M17 is closed. T18.1 is `verified` through
Brief 116: one unique valid window per realized episode in each of 24
source/phase/control/horizon buckets produces a 192-window signed selection;
T18.2 is next. The
live gate and training lock remain closed. The
following paragraphs
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
selected RealSense UYVY 640x480 and C922 YUYV 640x480. Original v4 manifest
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

Brief 050 implementation `4f75a7a` is remotely preserved. The injected fixture
runtime proves pre-open zero holders, exact connect/read/camera/read/no-torque-
close ordering, post-close holder stability, strict global monotonic time, and
preservation of construction, primary, camera-release, close, and holder
failures. It refuses a live-marked adapter before connect and grants only
`fixture_static_pose_bracket_runtime_conformant`. Twenty-seven focused tests
pass in both pinned runtimes and the 265-test broad gate passes. No hardware or
policy ran; the live gate remains closed.

Brief 051 implementation `bff160d` is remotely preserved. The accepted private
attempt-006 evidence remains identity `125de28f...`; tracked manifest v5
`5218c3bd...` retains the original full capture-selection digests for audit and
adds stable camera digests `69d55167...` and `9931d030...` over exact name,
unique ID, model ID, and input mode while excluding only the volatile numeric
index. CalibrationProfile `24db6f24...`, static contract `7260be3e...`, fixture
observation `9ad35d18...`, and fixture result `6b40e275...` are re-bound to that
v5 source. Sixty-seven focused tests pass in both robotics runtimes, all offline
verifiers pass, and the 266-test authority/twin gate passes. This grants only
`stable_camera_identity_binding_valid` in addition to the prior local fixture
capabilities. No hardware or policy ran; the live gate and training lock remain
closed.

Brief 052 implementation `79eee89` and verification follow-up `2c0b903` are
remotely preserved. Its fixed production and deterministic-fixture classes bind
fresh camera-index resolution to the stable v5 digests, the exact follower USB/
alias identity, an active lease, an open one-session project-state gate snapshot,
the pinned calibration/static sources, and a no-write lifecycle. The production
runner can emit only a candidate result with no physical proof label; fixture
execution records `hardware_opened=false` and cannot be relabeled live by
re-signing. Seventy-seven focused tests pass in both robotics runtimes, the
accepted private discovery resolver passes, and the 276-test authority/twin gate
passes. No hardware or policy ran. Brief 053 now satisfies the separate offline
factory/evidence/profile prerequisite. A fresh finite run window, a new parent
whose active persisted policy is actually `on-request`, a separate reviewed
remote gate transition, fresh lease, and fresh discovery/zero-holder snapshots
remain missing. The live gate and training lock stay closed.

Brief 053 implementation `d76baf5` is remotely preserved. The committed project
default is now `workspace-write`/`on-request`; separate content-addressed
hardware-supervised and offline-autonomous profile fragments encode
`danger-full-access`/`on-request` and `danger-full-access`/`never`. Hardware
profile evidence cross-checks the exact explicitly configured `codex doctor`
report against the latest persisted `turn_context` for the active
`CODEX_THREAD_ID`, before and after capture. A child config can no longer mask a
`never` parent. The current thread is therefore mechanically live-ineligible.

The Feetech and FFmpeg factories reverify the full candidate contract and active
same-thread profile before exposing a one-shot constructor. Feetech sources,
protocol 0, the follower canonical/TTY identity, no-handshake raw position reads,
and no-torque close are pinned; FFmpeg 8.0.1 is path- and hash-pinned and each
exact named camera can be consumed once. Candidate result schema v2 binds the
hardware-profile identity. Fixed private success/failure artifacts embed the
contract and profile and use one exclusive content-addressed artifact per
session, rejecting class drift, substitution, path escape, and symlinks.

Ninety focused tests pass in both robotics runtimes, source verifiers agree, and
289 broad tests pass. No production constructor, serial/camera/Studio path,
policy, simulation replay, training, or paid compute ran. Only local factory,
private-evidence, and runtime-profile conformance is granted.

Brief 054 implementation `ce7a794` is remotely preserved. One production
session entry point now reverifies the active same-thread profile, full candidate
contract, and a new non-aliased private destination before composing the exact
one-shot factories and candidate runner. A started session attempts one
immutable private success or failure artifact; result return is withheld until
the success artifact, reference, and signed candidate-only receipt independently
verify. Primary, cleanup, timing, and persistence failures remain visible
without a second write attempt. The receipt binds the contract, profile, result,
private evidence, canonical reference hash, and private-root identity while
granting no proof label or global authority.

Same-agent review strengthened outcome-clock failure handling and expanded
private-root alias rejection across all path ancestors. One hundred one focused
tests pass in both robotics runtimes, every offline source/artifact verifier
passes, and the 300-test authority/twin regression gate passes in 92.360
seconds. No production constructor, hardware path, policy, MuJoCo, training, or
paid compute ran. Only
`fail_closed_static_pose_live_session_orchestrator_conformant` is newly granted.
The current parent remains mechanically live-ineligible; the live gate and
training lock stay closed. A separate offline redacted candidate-session review
manifest is next.

Brief 055 implementation `411e5cc` is remotely preserved. A future successful
private candidate and Brief 054 receipt can now be fully reverified and reduced
to a deterministic signed review manifest containing only source/receipt
identities, private-artifact hashes without its path, high-level drift/timing/
operation summaries, stable camera and frame hashes, all-alias zero-holder
summaries, and lifecycle/audit hashes. The exclusive writer permits only a new,
session-named, non-aliased file beneath `configurations/robot_lab`, rereads the
stored bytes, and rejects escape, overwrite, alias, or corruption.

The manifest explicitly remains `candidate_observed_pending_review`; it embeds
no private path/root, contract/profile/result/evidence, doctor report, rollout
path, USB serial, device path, raw camera identity/index, raw joint position, or
frame bytes. Same-agent review also corrected boolean-as-integer acceptance in
the underlying static-pose operation counts and frame indexes. One hundred
seven focused tests pass in both robotics runtimes, all offline source/artifact
verifiers pass, and the 306-test broad gate passes in 69.782 seconds. No actual
live review manifest was created or accepted. Only
`redacted_static_pose_live_candidate_session_review_conformant` is newly
granted; the live gate and training lock stay closed.

Brief 056 is verified and remotely preserved at implementation `fd49820`. The
signed `blocked_missing_inputs` contract pins the executable PI0.5 source,
checkpoint processor, tokenizer, coordinate, normalizer, and sole CUDA-to-CPU
preprocessing override without naming or reading model weights. No accepted
live review decision, reviewed camera-role binding, or reviewed task prompt
exists, so no policy input, tokenizer/model construction, preprocessing,
inference, replay, policy label, or actuation is permitted. Only
`pi05_policy_input_preprocessing_source_contract_conformant` is newly granted;
the live gate and training lock stay closed.

Brief 057 is verified and remotely preserved at implementation `44dd871`. The
separate reviewed-input issuance gate mechanically requires same-session,
same-source, issuer-allowlisted, review-record-bound, time-valid acceptance,
camera-role, and task inputs while keeping fixture and production evidence
distinct. Its checked artifact remains `blocked_missing_reviewed_inputs`: no
real acceptance, role assignment, or task prompt exists. Only
`pi05_reviewed_input_issuance_gate_conformant` is newly granted; no policy input,
weight load, preprocessing, inference, replay, policy label, hardware access,
or live-gate transition is permitted.

Brief 058 is verified and remotely preserved at implementation `77724e1`. An
accepted-review-shaped deterministic static fixture now becomes exact
model-ready PI0.5 bytes and tensors through the pinned CPU preprocessor and
image transform, including three ordered image tensors/masks and exact prompt
tokens. Brief 059 supersedes its initial range interpretation: wrist-flex and
gripper exceed mean±std, but `[-1, 1]` is not a hard domain for this serialized
MEAN_STD checkpoint and gripper remains inside observed training support.
Only `fixture_pi05_model_ready_tensor_parity_conformant` is newly granted. The
real Brief 057 gate, live gate, model/weight/inference/replay, hardware,
policy-shadow, motion, and training authorities remain closed; the decisive
live experiment requires a fresh hardware-supervised no-prompt parent.

Brief 059 is verified and remotely preserved at implementation `f6b6c08`. The
v2 artifact binds all training-support statistics and preserves serialized
mean/std normalization, exact textual bins, and every Brief 058 model-facing
byte. Only fixture wrist-flex is outside observed training min-max; gripper is
inside q01-q99 and min-max support. The new local capability is only
`fixture_pi05_training_support_audit_conformant`; it grants no real input,
shadow, model, replay, hardware, motion, or training authority. The next live
experiment still requires a fresh hardware-supervised no-prompt parent.

Brief 062 is the latest reviewed implementation boundary at `d4047785`.
Reviewer 088 is remotely preserved in review commit `a514402f` and grants
runtime-profile eligibility only to its exact earlier thread/turn; it opens no
live gate and grants no hardware authority to a later thread. The canonical
state records implementation and review boundaries separately so a later
documentation commit cannot become a stale self-reference.

The current thread `019f5804...` failed its formal pre-device profile capture
because its active approval policy is not `on-request`. The failure occurred
before lease issuance, discovery, holder census, candidate-contract issuance,
or any serial/camera/device access, so no live gate was opened and no candidate
session started. Accepted T16.5b frame content nevertheless resolves the
physical camera semantics: stable RealSense `69d55167...` is rigidly
wrist-mounted and maps to `observation.images.left_wrist_0_rgb`; stable C922
`9931d030...` is the external workcell overview and maps to
`observation.images.base_0_rgb`. This reverses the fixture hypothesis. The
checkpoint prompt is pinned exactly as: `Sort each cube into the same-colored
tray: red cubes into the red tray and blue cubes into the blue tray.` These
review decisions cannot become production inputs until bound to a newly
accepted static-pose session.

Brief 071 implementation `19b7e766` and Reviewer 097 are verified under the
owner's explicit 2026-07-13 direction to use Full Access without approval
prompts. The future Codex runtime contract is `danger-full-access`/`never`
across the project default, explicit hardware profile, formal doctor/active-turn
verifier, candidate gate snapshot, and redacted review. Historical on-request
evidence above remains historical.
This exact current task now mechanically proves that profile as identity
`77f39177...`. Reviewer 098 opens one finite candidate gate only after its
scoped transition is confirmed on origin; the fresh lease and preflight remain
mandatory, and the training lock remains closed.

Fresh discovery later added an AVFoundation-only screen-capture source. Brief
074 corrects only unselected-source handling: the exact signed RealSense and
C922 still require unique system identities and modes, and selecting the screen
source rejects. Actual candidate construction now passes without hardware open;
the subsequent one-shot live session is rejected by a separate frame-field
contract mismatch. Failure `b117e797...` grants no observation or policy label;
shutdown leaves the follower disconnected, torque false, and both aliases free.
Brief 076 corrects that exact mismatch offline by validating and removing only
the pinned reader's two lower-level receive timestamps at the live adapter
boundary. The strict semantic frame contract is unchanged, and any new live
attempt requires a separately reviewed remote gate. The post-correction attempt
advanced to camera-audit validation and failed there; immutable failure
`33c8e4b1...` grants no observation or policy label and shutdown remains clean.
Brief 079 validates the complete successful finite FFmpeg backend audit before
projecting the exact static-pose lifecycle view; it grants adapter conformance
only and does not reopen the consumed gate.
Session `t16-5c-20260713-0912-cdt` then observed zero q drift, two 640x480 frames
per camera, 12 successful position reads, zero writes/torque changes/motion,
and clean zero-holder shutdown. The receipt and private success verify, but the
candidate is not accepted until the redacted review schema mismatch is fixed
offline and reviewed. That review now passes with manifest `75d8aae3...` and
accepts the bracket only. The current frames' hashes and dimensions were
retained, but their pixel bytes were not, so no model input, preprocessing,
shadow, or replay label follows from this acceptance.
Reviewer 109 now issues the production-valid acceptance, exact stable-camera
role, and exact task-prompt artifacts. Gate `d48165d1...` has no missing
reviewed inputs and permits production issuance, while explicitly keeping
`accepted_live_policy_input=false` until current pixel bytes exist.
Brief 084 and Reviewer 110 now verify the smallest backward-compatible private
retention correction. Future successful sessions can retain four exact
source-bound PNGs in private-success v2 while candidate and tracked review
artifacts stay hash-only. The accepted session remains v1; a fresh separately
reviewed bracket is the next experiment. Reviewer 111 opens exactly one such
session after remote confirmation, with complete fresh preflight and mandatory
private-success v2 on success. Session `t16-5c-20260713-0958-cdt` satisfies that
physical bracket and shutdown boundary. Current pixel review confirms the wrist
and external roles but finds the exact sorting prompt does not match the visible
workcell; tensor preprocessing may continue diagnostically, but policy-input
and actuation authority remain withheld.
Brief 087 then produced exact current tensors, one deterministic real MPS
proposal, and 5/10/15 MuJoCo prefix diagnostics, while Reviewer 113 rejected
shadow, matched replay, and motion. Brief 088 and Reviewer 114 correct one
diagnostic artifact from that rejection: the legacy simulation-policy offsets
were inappropriate for the pinned midpoint-calibrated physical-pose model.
Under the separately versioned midpoint-direct candidate, measured `q_after`
and every proposal prefix require zero projection and remain robot-self-contact
free. The candidate is accepted only for offline replay, not as a metric
physical transform. Scene mismatch, missing metric camera/workcell calibration,
checkpoint-support mismatch, the 54.4099-degree first wrist-roll change, and
5.43238 rad/s maximum replay velocity keep `DO_NOT_ACTUATE`, T16.5c in progress,
T16.6 pending, and the training lock closed.
Brief 089 and Reviewer 115 now accept the first grasp-specific executable
semantic boundary: one analytic-expert positive satisfies the ordered strict
grasp phases while remaining explicitly non-policy, and all twelve adversarial
negative traces fail through the same evaluator for their expected reasons.
The accepted external frame is bound only to a visible turquoise anchor
candidate; physical dimensions, mass, COM, material, friction, and pose remain
unknown. The nominal analytic cousin is not physical evidence. The next offline
experiment is a deterministic anchor-cousin MuJoCo grasp evaluated through the
unchanged semantic gate; no policy, twin, training, or motion authority follows
from the analytic fixture.
Brief 090 and Reviewer 116 preserve that first physics experiment. Two exact
371-frame replays lift and place the nominal anchor cousin only after a
contact-gated weld, so the legacy placement score passes while strict grasp
fails. The measured selected trace reaches 17.081659463 N contact force, has
only one gripper-side contact at confirmation and release, and lacks calibrated
current and metric aperture. The next offline correction is a lower-force
object-relative close that establishes simultaneous fixed- and moving-jaw
contact, stable hold, and clean release, with a nominal simulation-only aperture
profile. No threshold was relaxed and no physical value was inferred.
Brief 091 and Reviewer 117 isolate wrist roll as the missing contact variable.
A fixed 20-candidate search selects -1.5 rad wrist roll and 0.018 m pregrasp
height: 11 close frames and all 8 pre-lift hold frames have simultaneous fixed-
and moving-jaw contact at a 4.1971684 N peak. With no weld assistance, contact
survives only 4 lift frames, disappears for the complete 12-frame lift hold,
and the object returns to 0.324974 m. This is a low-impact contact candidate,
not a grasp. The next experiment must derive metric aperture from pinned jaw
geometry and sweep contact friction/compliance and close-hold parameters with a
held-out setting; normalized gripper percent is not relabeled as aperture.
Brief 092 and Reviewer 118 show why that contact still cannot grasp. The nominal
MuJoCo contact-point span collapses from 32.86691 mm during closure to 4.907838
mm during hold, so the fixed and moving jaw bodies converge on one local object
region rather than opposing faces. None of 12 friction/contact-time training
settings or the untouched holdout retains lift. Friction-only tuning is
rejected. Future MuJoCo strict evaluation must require opposing contact normals,
span, and wrench closure rather than a two-contact count alone; the next
experiment searches wrist pitch, object yaw, and lateral pregrasp offset under
those stricter geometry criteria.
Brief 093 and Reviewer 119 now provide those criteria as a separate v2 analytic
gate while preserving v1 byte-for-byte. V2 requires distinct jaws, at least 20
mm contact span, normal dot at most -0.8, and contact-axis alignment at least
0.8. It rejects the observed 4.907838 mm collapsed span plus same-jaw,
same-side, misaligned, malformed, and non-finite witnesses. This is an
antipodal two-jaw proxy, not actual MuJoCo grasp or full 6D wrench closure. The
next simulation search must compile consistently oriented MuJoCo normals and
complete unassisted lift, hold, lower, release, and retreat through v2.
The current M20 capability ladder has since closed PI0.5 and ACT Gate B retry
paths through signed localization. T20.36g is now verified by Reviewer 249:
spec `fb217f3e...` freezes exact offline SmolVLA policy/VLM snapshots, the real
two-camera canonical batch, MPS-only preflight, one bounded constant-LR
schedule, and the unchanged 0.10 objective/0.05-rad physical conjunction.
Brief 199 opens T20.36h pre-run implementation and central authority only. No
attempt, model access, optimizer, Gate C, hardware, external compute, or Brev
is authorized before that boundary is remotely reviewed.
Reviewer 250 now accepts implementation `29b9525`, raw-checkpoint preflight
`b7e2938f...`, and one-use permit `5fa7c1d2...`. Exactly one local-MPS attempt
may begin only after this boundary is confirmed on origin; runtime smoke
consumes the permit on failure, and neither result can select a policy or
execute Gate C by claim.
That attempt is now consumed by signed runtime failure `56415b28...`: exact
local VLM construction stopped on missing `num2words` before policy checkpoint
load, inference, or optimizer creation. Gate B was not evaluated. Reviewer 251
opens Brief 200 for a read-only recursive SmolVLA dependency-closure audit;
installation and any replacement attempt require new owner authority.
T20.36i now verifies closure `0804fd4f...`: LeRobot and Transformers pass,
while num2words and Accelerate are missing. Reviewer 252 requires recursive
closure validation and offline AutoProcessor construction before any future
marker. T20.36j-A result `8dec69ae...` now proves the full closure resolves
offline: 24 existing distributions plus four cached additions bound by manifest
`6cc7235c...`; network acquisition is unnecessary. Reviewer 253 verifies the
read-only audit. Reviewer 254 now verifies corrected fail-closed preflight
contract `cb018b69...`: recursive installed closure and offline AutoProcessor
construction must pass before a marker, while full policy construction stays
counted. The contract itself grants no permit or readiness. On 2026-07-16 the
owner explicitly authorized the exact four-package offline installation, live
corrected preflight, and at most one unchanged-Gate-B replacement attempt.
Brief 203 opens the implementation and execution boundary; central authority,
remote preservation, signed closure/processor evidence, and a fresh one-use
permit remain mandatory before a marker.
Implementation `b35acd1` and central decision `aa0992e6...` are now verified
and preserved on origin. Reviewer 255 permits the exact four cached packages
to be installed offline and the corrected preflight to run. The attempt marker
remains closed until the resulting closure, processor smoke, preflight, and
one-use permit are committed, pushed, and origin-confirmed.
The four-package offline correction is complete. The first uncounted preflight
stopped before AutoProcessor on editable LeRobot's `PKG-INFO` metadata variant;
correction `9e9272c` is remote and live recursive closure `ac8abed1...` passes
across 57 active packages. Reviewer 256 permits one corrected preflight retry.
No attempt marker exists.
That retry constructed AutoProcessor offline but rejected empty opened-file
evidence because Hugging Face resolved snapshot symlinks to blob paths.
Correction `54339c2` is remote; real guarded smoke `3f9a4a0c...` now records six
safe files, exact classes, no network, and no weights. Reviewer 257 authorizes
the corrected preflight retry. No marker exists.
The next uncounted preflight exposed only the offloaded-cache spelling seam:
physical resolution changed the spec's exact `~/.cache` path to
`/Volumes/cerebro`. Correction `ad051d0` preserves lexical contract identity
and resolves only for access control; smoke `5223d8f0...` now verifies.
Reviewer 258 authorizes the corrected preflight retry. No marker exists.
Corrected preflight `3c9b5af9...` and one-use permit `effa3b65...` now verify
and are preserved on origin with closure `ac8abed1...` and processor smoke
`5223d8f0...`. Reviewer 259 authorizes exactly one local-MPS counted
replacement under unchanged Gate B; its first marker consumes the permit.
That sole attempt now verifies negative as result `08ef923d...`: objective ratio
`0.022866` passes, but deterministic maximum physical error `0.266024` rad
fails the unchanged gate after 2,000 updates. Reviewer 260 closes the SmolVLA
replacement alphabet. Brief 204 opens the owner-pre-authorized model-free
consequence-calibration design; strict uniform error remains report-only, no
gate changes now, and no ACT/SmolVLA retry or Gate C execution is authorized.
T20.36k now verifies result `a3b39178...`: the exact source replay passes and
252 fixed symmetric perturbation pairs produce 202 passes, 50 failures, and
zero non-monotonic phase/joint cells. Wrist roll remains insensitive through
0.4 rad in every phase, while shoulder lift and gripper retain task-critical
0.025/0.01-rad phase ceilings. Implementation `fbdb0aa` is on origin and
Reviewer 261 verifies the non-authorizing calibration. Brief 205 now freezes
that evidence before scoring retained ACT/SmolVLA tensors; it cannot load a
model, fit to candidate errors, execute Gate C, or accept a policy.
T20.36l now verifies owner decision `32d7e193...`, frozen amendment
`463477dc...`, and fail-closed result `0f8ae393...`. ACT still fails on shoulder
lift t0, wrist roll t0, and gripper t49. SmolVLA retained only deterministic
hashes and aggregate errors, not its 50x6 tensors, so its amended score is
indeterminate and no Gate C route opens. Implementation `e4c00bd` is on origin
and Reviewer 262 closes the authorized slice. Proposed Brief 206 requests one
exact inference-only tensor reproduction; it grants nothing without fresh
owner and central authority.
At 2026-07-16T01:44:12-05:00 the owner opened a fresh eight-hour autonomous
research/critique window through 09:44:12 CDT and explicitly activated Brief
206. T20.36m may construct/load the exact retained SmolVLA model once and
reproduce only the five registered seeds with two repeats after a fresh central
decision, verified preflight, committed one-use permit, and remote parity. No
optimizer, threshold change, Gate C, hardware, network, external compute, or
Brev authority follows from the window.

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
- MVP capability ladder and task queue: `docs/sim-link-mvp-execution-plan.md`

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

## Proof-State History Pointer

Verified historical proof-state prose is retained in
`docs/autonomous-workflow/proof-state-history.md`. Append new entries there
with the corresponding brief and reviewer decision; keep this file limited to
the active mission, window, milestone, and pointers.
