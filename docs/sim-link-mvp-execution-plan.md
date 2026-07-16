# Sim-Link MVP Execution Plan

## Decision

The program will optimize for the first truthful, runnable learned-policy demo
while preserving the complete physical-product exit condition. T20.42/R0 is
verified at result `d238379b...`: 119 new training successes, nine fresh-held-
out successes, exact base once, and a 129-episode package. The immediate
sim-link long pole is now T20.43 ACT with a standard recipe and immediate
closed-loop strict-v2 evaluation. SmolVLA follows after the ACT boundary;
PI0.5 remains conditional. Robo Scan proceeds independently toward the real
metric export required by I5.

This plan is a task-ordering source, not an authority source. Live authority,
training readiness, and proof labels remain mechanically owned by
[`project_state.json`](./autonomous-workflow/project_state.json) and the central
authority composer.

The next-hours convergence order, demo checkpoint, proof bundle, and full-MVP
proof stack are fixed by
[`Manager Intervention 018`](./manager-log/018-mvp-demo-convergence-directive.md).

## Product Cut

### Build in the current sim-link lane

- T20.42 fixed R0 dataset construction, followed by standard-recipe ACT and
  SmolVLA rungs with rollout-primary strict-v2 evaluation.
- An explicit, reusable learning/plumbing evidence surface: exact R0 parity
  checks plus the existing signed T20.35x one-batch proof, kept distinct from
  any accepted product policy.
- Recovery and perturbation episode expansion from the already verified MuJoCo
  state-branching primitive.
- A small discrete robustness grid using the existing randomization path.
  Twin-uncertainty factors (friction, command latency/action hold, gripper
  mapping) are declared separately from episode-variation factors (cube pose,
  initialization deltas, fork perturbations); cube pose is start-state
  variation, never a physics parameter. Roughly 10-20 hand-selected cells give
  pairwise coverage, with declared training cells and held-out evaluation
  cells; no full Cartesian product.
- A hardware-observable evaluator with an explicit observer role; privileged
  MuJoCo state remains a separate oracle.
- A thin paired trace runner that starts from the same measured/declared `q0`,
  replays the same commands, and compares joint tracking and event times.
- Timing evidence for clock source, observation age, command latency, action
  hold, control period, and jitter.

### Add schema fields when their owning task is implemented

- `observer_role`: `privileged_simulator` or `hardware_observable`.
- `generation_reason` for each cousin/intervention.
- `clock_source` for every timestamped stream.
- Separate proposed, issued/safety-modified, and measured/applied action fields.
  Existing requested/executed semantics must be extended, not relabelled.
- `human_video` raw-record type with capture, consent, license, and
  PII-handling fields; a pairing manifest binding human video to a
  twin-reconstructed robot episode; `event_label_source` distinguishing
  robot-side strict-v2 event times from human-side weak labels. Schema stubs
  only until the paired-corpus track opens post-Gate-D.

### Defer until the first verified sim-to-hardware task success

- Posterior inference and posterior-driven calibration.
- A generalized cousin algebra or full taxonomy.
- Fidelity certificate v1 beyond a plain task scorecard.
- Event-triggered flight recorder, drift monitor, live scene deltas, and
  renderer qualification.
- A dependency-light shared contracts package, unless two real schema versions
  first demonstrate repeated semantic drift.

### Prepare now for the Gate F scene adversary

- T20.38's quantitative strict-v2 receipt and T20.39's content-addressed
  counterexample archive are verified. T20.40 replay remains inactive until a
  learned policy mechanically passes Gate C.
- T20.19's gripper-1.05 seed remains evidence-only rather than a learned-policy
  counterexample because it did not compare a policy with a freshly re-derived
  expert on the same perturbed scene.
- After Gate C, every checkpoint eligible for selection must replay the fixed
  active archive. Scene mutation/search remains blocked until a policy passes
  Gate D; operationally, a Gate E nominal success should precede Gate F search.
- Replace T21.6's generic curriculum with the bounded, expert-competence-gated
  CEGIS scene adversary described in
  [`cegis-scene-adversary-adoption-plan.md`](./autonomous-workflow/cegis-scene-adversary-adoption-plan.md).

### Prepare for human-video paired-corpus steering (post-Gate-D)

- Adopt the direction in
  [`human-video-paired-corpus-adoption-plan.md`](./autonomous-workflow/human-video-paired-corpus-adoption-plan.md):
  the twin plus constructive expert manufacture the robot side of
  human↔robot pairs without teleoperation; the pair corpus is the durable
  data-scaling asset independent of which external adaptation method wins.
- Now: schema stubs only (listed above). Human-viewpoint renders are derived
  later from R0 episodes by deterministic replay; the T19.2 printed
  checkerboard doubles as the human-recording registration mat.
- Governance: human video is evidence before it is data — no human-derived
  frame enters training without a separate source-bound compiler, mixture,
  and central-authority decision (mirrors design rule 8).
- No pairing pipeline, video perception, or test-time adaptation module
  before a Gate D pass and a fresh owner decision.

### Cut until evidence creates a need

- A generalized reward/curriculum compiler, learned scene adversary, or
  automatic counterexample-to-training path. The bounded Gate F CEGIS
  falsifier is a later evaluation task, not an exception that opens these
  learning systems now.
- Learned world models or residual dynamics.
- Skill-graph infrastructure or a new scientist-agent module.
- Gaussian splats, dual renderers, tactile distillation, Genesis backend,
  deformables/multiphysics, cross-workcell learning, or a third repository.

## Governing Design Rules

1. **Construct before search.** Prefer deterministic geometry, exact package
   behavior, and computable checks everywhere except the policy itself.
2. **Keep learning surfaces separate.** Successful episodes may update a
   policy; paired sim/real evidence may update the twin; transition data may
   someday update an optional dynamics model. None implies another.
3. **Use a discrete ensemble before posterior machinery.** The MVP needs roughly
   10–20 declared combinations, not a new inference subsystem.
4. **Success is not reward.** Strict-v2 remains the simulator success oracle.
   No dense reward compiler is needed for the imitation-learning MVP.
5. **Package behavior is executed, not recreated.** Pinned LeRobot owns data,
   processors, policies, and training; MuJoCo owns physics/state transitions.
6. **Repository boundaries follow present evidence.** Robo Scan and sim-link
   exchange sealed artifacts. No merge, third runtime repo, or shared contracts
   package is justified yet.
7. **The existing loop is the scientist harness.** Briefs, gates, signed
   artifacts, reviews, and quarantines already encode hypotheses and evidence.
   Add typed diagnostics to that loop only when a concrete task needs them.
8. **Counterexamples are evidence before they are data.** Archive replay may
   block regression, but a failure trace cannot enter training without a
   separate source-bound compiler, mixture, and central-authority decision.

## Capability Ladder For Policy Adaptation

Every training or diagnostic slice must name the lowest unmet gate it
addresses. Failure at a gate localizes the fault class; optimizer budget is
not spent on a higher gate while a lower one is unmet.

| Gate | Proof | A failure localizes to | Status |
| --- | --- | --- | --- |
| A | Exact train/inference parity: dataset statistics, image/state/action normalization, chunk interpretation, joint order, gripper representation, postprocessing, cadence/hold, with round-trip tests on known values | Contract or preprocessing parity | Largely verified: T20.12 round-trip, T20.13 statistics, T20.26 determinism, T20.28-T20.31 sampler/quantile chain |
| B | One-batch memorization: the policy overfits a tiny fixed batch to near-zero action error | Model or trainer plumbing | Passed once by T20.35x under frozen uniform Gate B; T20.36 coverage regressed; T20.36n preserves the uniform pass but passes the consequence amendment on only 3/5 single-batch seeds; T20.36o then fails every forward bridge checkpoint and closes current candidate entry. Diagnostic purpose (plumbing localization) is complete per the 2026-07-16 owner route decision; R1–R3 rungs do not re-prove Gate B |
| C | One-episode closed-loop reproduction: an unassisted rollout reproduces one training episode (seeds 0-5) through strict-v2 | Action-chunk execution semantics or closed-loop compounding | Not executed: the owner-designated X bridge failed all five pre-registered open-loop checkpoints through 2,500 updates, so the adjudicated ACT/SmolVLA/X Gate C route is closed without a rollout. Reopened for R1–R3 standard-recipe candidates with rollout-primary evaluation per the 2026-07-16 owner route decision |
| D | Full training-set success: strict-v2 across all eight constructive episodes | Dataset coverage or adaptation capacity | Open |
| E | Held-out nominal starts: seeds 6-7 and small initial-state variation | Generalization | Open (0/2 at T20.24 and T20.31) |
| F | Robustness grid and forked recovery starts | Robustness | Open |

The historical T20.2 ACT control failed closed loop with near-zero lift, while
T20.35x later proved that the shared training/checkpoint/decode stack can
memorize one batch. That positive plumbing proof must appear in the MVP
scorecard, but it is not an accepted policy. New R1-R3 candidates still require
exact R0 Gate A parity and honest learning curves; a new one-batch or open-loop
threshold may diagnose them but must not block safe closed-loop evaluation.

## Sim-Link Task Queue

Only the first dependency-ready task is active. Later tasks are planned and do
not inherit authority from this document.

Owner route decision (2026-07-16, answers T20.41): dataset expansion by
construction, then standard-recipe training rungs at realistic budgets
(ACT → SmolVLA → conditional π0.5) with rollout-primary evaluation; no
correction-objective work and no Gate B re-proof for the new rungs. Routing,
evaluation doctrine, and stop rules are pre-registered in
[`owner-route-decision-2026-07-16-t20-41.md`](./autonomous-workflow/owner-route-decision-2026-07-16-t20-41.md).
The consumed overnight direction is retained as history in
[`owner-direction-2026-07-16-overnight.md`](./autonomous-workflow/owner-direction-2026-07-16-overnight.md).
Manager Intervention 018 narrows the next-hours delivery order to T20.42 R0,
then T20.43 ACT, immediate closed-loop evaluation and demo capture, then
T20.44 SmolVLA. It also preserves the real Robo Scan/I5 metric twin and a
separately authorized physical-policy canary as non-negotiable full-MVP exits:
[`018-mvp-demo-convergence-directive.md`](./manager-log/018-mvp-demo-convergence-directive.md).

| Order | Task | Required output and gate | Depends on | Explicitly excluded |
| --- | --- | --- | --- | --- |
| 1 | **T20.17 — clean-base dataset-native PI0.5** | One clean `pi05_base` initialized with exact source-dataset statistics; bounded local training; frozen held-out evaluation; unassisted strict-v2 result; all dataset, processor, normalizer, checkpoint, and evaluation identities signed. A non-passing policy is recorded as a negative result, never promoted. | Verified T20.16 diagnosis, source-backed native dataset/processor boundary, current mechanical training authority | Hardware, Brev, external compute, projection/assistance, hybrid postprocessor reuse |
| 2 | **T20.18 — state-fork recovery episodes** | Reuse the verified T18.4 MuJoCo checkpoint/branch primitive to fork selected approach, grasp, hold, and release milestones; generate labelled perturbation, near-failure, recovery, and failure episodes; preserve parent checkpoint and `generation_reason`; prove deterministic replay and no padded/inferred actions. | T20.17 evaluation identifies policy-visited failure states; existing T18.4/T17 contracts | Full-system checkpoint abstraction, hardware reset, arbitrary counterfactual framework |
| 3 | **T20.19 — discrete ensemble cousins v0** | A fixed 10–20-cell manifest over bounded cube pose, friction, command latency/action hold, and gripper mapping; same-seed replay; physically valid bounds; nominal and worst-cell strict-v2 scorecard. | A T20.17 candidate worth stress-testing; T20.18 data decision recorded | BayesSim/ASID posterior inference, broad visual/object/task cousin generation |
| 4 | **T20.20 — observer-role evaluator contract** | Versioned privileged and observable evaluator roles; identical task predicate vocabulary; positive, negative, anti-false-positive, missing-observation, and role-leakage tests; simulator consistency report. | Strict-v2 semantics and declared observable inputs | Camera access, VLM-only success, physical qualification |
| 5 | **T20.21 — thin paired trace runner** | Extend the Brief-088 replay idea: bind common `q0`, proposed/issued/measured actions, timestamps, joint traces, and grasp/contact event times; compare traces without a pixel-matching requirement; route mismatch categories without changing the twin. | T20.20 observable contract; separately supplied immutable traces | Live robot execution, calibration optimizer, full shadow-sim service |
| 6 | **T20.22 — timing/latency certificate v0** | Deterministic schema and verifier for clock sources, frame age/skew, observation assembly, action transport/hold, control period/jitter, inference latency where present, drops, and deadline misses; prove timing mismatch cannot be silently relabelled as dynamics error. | T20.21 trace schema | Contact/dynamics calibration, live probe execution, task-family fidelity certificate |
| 7 | **T20.23 — recovery-augmented dataset preflight** | One actual LeRobotDataset containing the six nominal strict-success episodes and four strict-success policy-visited recovery episodes; near-failures/failures and seeds 6-7 remain outside training/statistics; exact mixture, dataset, statistics, clean model snapshot, and central simulation-only authority identities signed before any optimizer. | Verified T20.17 dataset/result and T20.18 recovery package | Optimizer execution, failure imitation, implicit oversampling, hardware, Robo Scan, external compute, Brev |
| 8 | **T20.24 — recovery-augmented local-MPS campaign** | Exact official-LeRobot 500-update rank-4 campaign from clean base; frozen adapter evaluated once each on held-out seeds 6-7 with no projection/assistance; signed per-seed and aggregate strict-v2 result without policy promotion. | Verified T20.23 dataset/spec and active central simulation-training authority | Additional rungs/sweeps, ensemble, promotion, hardware, Robo Scan, external compute, Brev |
| 9 | **T20.32 — closed-loop divergence localization (verified)** | Six complete signed 244-frame traces; four held-out action hashes reproduce exactly; both seed-0 probes first diverge at frame zero and route Gate B. | Verified T20.31; Brief 163; Reviewer Decision 193 | Any optimizer, dataset/statistics change, promotion, hardware, Robo Scan, external compute, Brev |
| 10 | **T20.33 — Gate B one-batch memorization proof (verified negative)** | One exact batch, 500 finite updates, five fixed-seed decoded chunks; both objective-ratio and action-error gates fail. | Verified T20.32 Gate B route; Brief 164; Reviewer Decision 195 | Gate C cadence/chunk changes, unreviewed sweeps, grid expansion, promotion |
| 11 | **T20.34 — Gate B plumbing localization (verified)** | Exact base/adapter replay proves active nonzero LoRA, exact checkpoint reload, lower mean error and positive target alignment on all five seeds; routes insufficient optimization/capacity. | Verified-negative T20.33; Brief 165; Reviewer Decision 196 | Optimizer continuation/retry, Gate C changes, second batch, promotion |
| 12 | **T20.35 — Gate B rank-capacity discriminator (verified negative)** | The sole rank-16 attempt completed 500 finite updates and improved objective ratio from 0.528248 to 0.155307, but missed the 0.10 objective gate and all five 0.05 rad decoded-action gates. | Verified T20.34 capacity/optimization route; Brief 166; Reviewer Decision 199 | Multiple ranks, continuation, second batch, Gate C changes, promotion |
| 12b | **T20.35.x — conditional Gate B discriminators** | T20.35c's expert-only ceiling passes the objective gate but misses action error; T20.35d-f localize systematic normalized bias without clipping. T20.35g rejects 20/50-step cadence. T20.35h's bias ceilings improve but fail. T20.35i localizes the remaining 96 failures as distributed across all five seeds and four channels; top-two seed/channel and boundary fractions are only 56.25%/67.71%/31.25%, with raw spread up to 0.183018 rad. Route T20.35j to one inference-only initial-noise-scale discriminator before any optimizer correction. | Verified-negative T20.35; T20.35c-i signed evidence; reviewer chain through Decision 212 | Combined-factor changes, unreviewed sweeps, second batch, Gate C changes, promotion |
| 13 | **T20.36 — bounded campaign after Gate B correction (verified negative)** | The sole 500-update campaign passed the standard-objective ratio but regressed all five decoded chunks to 0.1506-0.1870 rad; Gate B failed, so no closed-loop seed was reached. T20.36a verifies weighted-objective/physical-gate non-equivalence; T20.36b is a pure retention contract. | Verified T20.35x Gate B pass | Retry, gate change, promotion, hardware, external compute, Brev |
| 13c | **T20.36c — local ACT/SmolVLA preflight (verified)** | Source/cache/dataset metadata routes an exact ACT Gate B control design first. Cached ACT is not drop-in; SmolVLA requires a two-camera override and MPS runtime proof. No tensor was read and no policy was selected. | T20.36b no-coverage decision | Model load, inference, optimizer, policy selection, gate change, hardware, external compute, Brev |
| 13d | **T20.36d — exact ACT Gate B control design (verified)** | Spec `45c90dc0...` binds the fresh compact ACT, canonical batch/statistics, 2,000-update ceiling, pre-registered checkpoint schedule, deterministic repeats, unchanged Gate B conjunction, stop rules, and one-use boundary. | Verified T20.36c preflight | Model load, optimizer creation/training, run authority, SmolVLA entry, gate change, Gate C, hardware, external compute, Brev |
| 13e | **T20.36e — exact ACT control (verified negative)** | The sole 2,000-update attempt signs result `2ea2c246...`: objective ratio passes at 0.054918 and five hashes agree, but maximum physical error is 0.442487 rad. No retry; no Gate C. | Verified T20.36d design and pre-run | Retry, sweep, policy selection, Gate B amendment, Gate C, hardware, external compute, Brev |
| 13f | **T20.36f — ACT decode/per-joint localization (verified)** | Result `472e5ec5...` reproduces objective/hash and direct/queue equality; 14 exceedances concentrate at t0 and the late endpoint and already exist in normalized output. ACT retry closes. | Verified-negative T20.36e | Optimizer, retry, second training attempt, policy selection, gate change, Gate C, hardware, external compute, Brev |
| 13g | **T20.36g — exact SmolVLA Gate B entry design (verified)** | Spec `fb217f3e...` binds exact offline policy/VLM snapshots, real two-camera configuration, canonical batch/stats, MPS no-fallback smoke, one frozen attempt/schedule, unchanged Gate B, finite evidence, selected-only checkpoint, and conservative routes. | Verified T20.36f localization; Brief 198; Reviewer 249 | Model load, inference, optimizer, policy selection, Gate B amendment, Gate C, hardware, external compute, Brev |
| 13h | **T20.36h — exact SmolVLA Gate B attempt (verified runtime failure)** | Attempt `43c2d0a1...` stopped in AutoProcessor on missing `num2words`; result `3804eff6...` proves zero updates, no policy checkpoint load/inference, and Gate B not evaluated. The permit is consumed. | Verified T20.36g design; Brief 199; Reviewer 251 | Retry, relabel as Gate B failure, policy selection, Gate B amendment, Gate C execution, hardware, external compute, Brev |
| 13i | **T20.36i — SmolVLA dependency-closure audit (verified)** | Audit `0804fd4f...` proves LeRobot/Transformers pass while num2words/Accelerate are missing. Future preflight must validate the recursive closure and construct AutoProcessor offline before a marker. | Verified T20.36h dependency failure; Brief 200; Reviewer 252 | Package install, environment mutation, replacement attempt, model access, Gate C, hardware, external compute, Brev |
| 13j-A | **T20.36j-A — offline cache resolution audit (verified)** | Result `8dec69ae...` resolves 28 packages offline, reuses 24 installed distributions, and binds four cached additions with manifest `6cc7235c...`; no network is needed. | Verified T20.36i; Brief 201; Reviewer 253 | Network/download, package install, environment mutation, attempt marker, model access, Gate C, hardware, external compute, Brev |
| 13j-B | **T20.36j-B — corrected replacement-preflight contract (verified)** | Contract `cb018b69...` independently reconstructs recursive installed closure and makes offline AutoProcessor construction a mandatory pre-marker gate while full policy construction remains counted. | Verified T20.36j-A; Brief 202; Reviewer 254 | Package install, live AutoProcessor/model access, permit, marker, replacement execution, Gate B change, Gate C, hardware, external compute, Brev |
| 13j | **T20.36j — corrected SmolVLA replacement attempt (verified negative)** | Result `08ef923d...` completes 2,000 updates with deterministic seeds and objective ratio 0.022866, but maximum physical error 0.266024 rad fails unchanged Gate B. SmolVLA replacement closes; no retry or Gate C. | Verified T20.36j-B; Brief 203; Reviewer 260 | Second attempt; retry/sweep; relabel as pass; Gate C; hardware; external compute; Brev |
| 13k | **T20.36k — consequence-calibrated Gate B amendment design (verified)** | Result `a3b39178...` binds 252 symmetric model-free perturbation pairs: 202 pass, 50 fail, zero non-monotonic cells. Wrist roll is insensitive through 0.4 rad; shoulder lift and gripper retain task-critical 0.025/0.01-rad phase ceilings. No gate changes here. | Verified-negative T20.36e/T20.36f/T20.36j; Brief 204; Reviewer 261 | Candidate-derived thresholds, ACT/SmolVLA retry, model load/inference, optimizer, Gate C execution, policy selection, hardware, external compute, Brev |
| 13l | **T20.36l — frozen consequence Gate B amendment (verified fail-closed)** | Gate `463477dc...` is frozen before scoring. ACT conclusively fails three retained witnesses; SmolVLA is indeterminate because hashes/aggregates but no decoded tensors were retained. Result `0f8ae393...`; no Gate C route. | Verified T20.36k; Brief 205; Reviewer 262 | Threshold fitting, retry, model load/inference, optimizer, new decode, Gate C execution, policy selection, hardware, external compute, Brev |
| 13m | **T20.36m — SmolVLA tensor-only reproduction (verified negative)** | The sole local-MPS attempt reproduced all five signed hash pairs with bit-identical repeats. Result `4f101f38...` records 162 frozen-gate violations across all five seeds, so SmolVLA fails the amended gate. X must still be scored before the three-candidate comparison is complete. | Verified T20.36l; Brief 206; Reviewer 264; result boundary `a5e7c6a` | Retry, optimizer, training, new seeds/repeats, threshold change, ACT work, Gate C execution, policy selection, hardware, network, external compute, Brev |
| 13n | **T20.36n — T20.35x tensor-only reproduction (verified mixed-negative)** | All five source hashes and repeats reproduce. Result `f8d7866e...` preserves the uniform Gate B pass and passes the frozen amendment on 3/5 seeds; five misses are only grasp-phase gripper cells at t33-36, with 0.000342-0.004420 rad excess. X remains the owner-designated bridge candidate. | Verified-negative T20.36m; Brief 207; Reviewer 266; result boundary `a20f2a4` | Retry, threshold change, direct Gate C execution before bridge acceptance, new candidate, hardware, network, external compute, Brev |
| 13o | **T20.36o — bounded X episode-0 bridge (verified terminal negative)** | Baseline `e6537428...` fails all later starts. The sole bounded correction then completes 2,500 finite updates; result `ec7fb323...` passes every source-objective gate but the final amended gate passes 0/25 with 1,677 violations. Uniform supplement `70e98c06...` also fails. No retry; Gate C was not executed and the current candidate route closes. | Verified T20.36n; owner overnight priority 3; Brief 208; Reviewers 267-277; bundle `f1744a0` | Retry, T20.36p, Gate C rollout, threshold change, new candidate, hardware, external compute, Brev |
| 14 | **T20.37 — observable-evaluator qualification** | Run the T20.20 observable role beside strict-v2 over all nominal, recovery, and grid episodes; signed confusion matrix with a low-false-positive requirement; ambiguous outcomes fail closed; prerequisite for any canary planning. | A strict-v2-passing policy worth transferring | Camera access, VLM-only success, physical qualification |
| 15 | **T20.38 — quantitative strict-v2 receipt contract (verified/hardened)** | Receipt `042bf0be...` binds 33 raw/normalized signed margins, explicit actor/evidence blockers, hard conjunction, source identities, and guard-preempting effective bottleneck. It agrees with analytic source success while withholding policy/MuJoCo/physical claims. | T20.36o terminal negative; Briefs 209/211; Reviewer 280; implementations `f9c3682`/`83d51c5` | Model load/inference, optimizer, gate change, history rewrite, Gate C execution, policy selection, hardware, external compute, Brev |
| 16 | **T20.39 — counterexample archive schema/bootstrap (verified/hardened)** | Receipt `60babc53...` and index `043d45b3...` seed one truthful evidence-only T20.19 source-controller negative; authority is routing-bound, conflicting inactive duplicates fail, and stale sources require invalid/no-replay/no-delete disposition. | T20.19; verified T20.38; Briefs 210/211; Reviewer 280; implementations `80d2992`/`83d51c5` | Scene search, policy blame without expert competence, replay gate activation, training ingestion, hardware, external compute, Brev |
| 17 | **T20.40 — fixed archive replay harness (deferred)** | Replay the complete active manifest on every checkpoint eligible for selection; report open challenges and block regressions of required cases. No scene mutation or training. | Mechanical Gate C pass absent; verified T20.39 | Active adversarial search, optimizer, automatic training ingestion, policy acceptance, hardware, external compute, Brev |
| 18 | **T20.41 — owner capability-route decision (decided 2026-07-16)** | The owner selects dataset expansion plus standard-recipe rungs with rollout-primary evaluation, recorded in [`owner-route-decision-2026-07-16-t20-41.md`](./autonomous-workflow/owner-route-decision-2026-07-16-t20-41.md). A fresh brief must open T20.42/R0; the optimizer alphabet stays closed. | T20.36o terminal negative; verified T20.39; recorded owner decision | Silent resumption of T20.35/T20.36, correction objectives, threshold changes to `463477dc...`, hardware, external compute, Brev |
| 19 | **T20.42 — R0 dataset expansion by construction (verified; Briefs 216-218)** | Sole result `d238379b...` completes 119/119 training and 9/9 fresh-held-out strict-v2 successes. Exact T20.23 base once; 129 training episodes, 31,366 frames, 59,904 windows; held-out rows excluded; mixture `37b30d34...`, statistics `02ba0e70...`, retention `19d19fba...`; independent verifier exit 0. | Recorded T20.41 route; verified scripted expert and randomization contracts; Briefs 216-218; Reviewers 286-290 | Retry, relabel scripted data as learned-policy proof, model/optimizer work inside R0, hardware, external compute, Brev |
| 20 | **T20.43 — R1 ACT standard rung (terminal infrastructure failure; Brief 219/Reviewer 293)** | Sole marker `064e5650...` consumed. Full ACT, optimizer, checkpoint 0, and one chunk-50 rollout completed with zero updates; trace `6133ce58...` failed strict-v2. Mirror child used a venv without MuJoCo and terminated the run. Receipt `b64ec6d0...` preserves the exact partial boundary. No retry; trained ACT capability remains unresolved. | Verified T20.42/Reviewer 290; Brief 219; Reviewer 293 | T20.43 retry/replacement, fabricating a trained ACT result, correction objectives, threshold changes, hardware, external compute, Brev |
| 20b | **T20.43b — R1 ACT replacement rung (implementation verified; Brief 222/Reviewer 299)** | Spec `13c5bb4b...` preserves the original fixed 10,000-update recipe exactly and adds stable T20.44 interpreter/MuJoCo support plus a fresh real renderer smoke binding trace identity and bytes. Model-free materialization opens only after implementation origin confirmation. | Verified T20.44 terminal boundary; owner addendum `8b4a206`; Reviewer 299 | Second replacement, recipe changes, correction objectives, live action before pre-run review, threshold changes, hardware, network, external compute, Brev |
| 21 | **T20.44 — R2 SmolVLA standard rung (verified terminal negative; Brief 220/Reviewer 297)** | Sole result `9d916206...` completes 5,000 finite updates, five checkpoints, and ten dual-semantics rollouts with no strict-v2 pass. Strongest partial result was checkpoint 1,000/receding-10 at 73 contacts and 18.061 mm lift; first-pass selection remains null. | Verified T20.42; T20.43 boundary; Reviewers 294-297 | Retry/replacement, correction objectives, network/download, Gate B/open-loop barrier, threshold changes, hardware, external compute, Brev |
| 22 | **T20.45 — R3 conditional π0.5 standard rung** | Only after R1/R2 evidence: either one bounded local-MPS standard fine-tune from the cached base, or a costed external-compute proposal document (ABEJA-parity reference) for separate fresh owner authorization. No compute consumption beyond local MPS without that grant. | R1/R2 rollout evidence; fresh owner grant for any external compute | External compute or Brev consumption without fresh owner authorization, correction objectives, promotion |

T20.36c's read-only preflight routes ACT as the cheapest diagnostic control,
not as a product-policy selection. T20.36f closes ACT with a reproduced
normalized boundary/endpoint miss. T20.36g now freezes SmolVLA's exact local
entry, and Brief 199 opens only its pre-run implementation/authority boundary.
SmolVLA becomes a policy track only after a separate verified execution result;
PI0.5 remains the compatibility/stress baseline. CUDA, A100, external compute,
and Brev remain closed.

### Support tooling

`scripts/robot_lab/render_rollout_mirror.py` renders any signed
`t20_32_closed_loop_trace.v1` artifact as a side-by-side MP4: re-rendered
policy side/overhead views beside the exact recorded expert top-camera frame
for the same frame index, with phase, strict-contact, and anchor-lift
overlays. Output stays under `outputs/robot_lab/rollout_mirror/` with a hash
manifest. It is kinematic playback of signed evidence — diagnostic
visualization only, never new evidence or authority. Every future closed-loop
evaluation slice should retain its mirror MP4 the way rendered keyframes are
retained today; a later small slice may fold the render into the evaluation
runner and sign the output.

T20.17 is verified negative, T20.18 is verified recovery evidence, T20.19 is
verified as an uncalibrated grid, T20.20 and T20.21 are verified, and T20.22 is
verified. Brief 154 and Reviewer Decision 184 verify T20.23's narrow policy-data preflight; the
MVP exit condition below is not met. Do not
start broad calibration, Robo Scan consumption beyond the verified
reference-only I2/I3 boundary, or canary planning while the learned policy has
not achieved repeatable strict-v2 success in simulation.

**Current progress:** Brief 147 is verified at `b826e3f` by Reviewer Decision
177. One actual LeRobotDataset contains six strict-v2 source episodes (seeds
0-5, 1,464 frames); seeds 6-7 remain frozen outside it and its statistics. The
complete local `lerobot/pi05_base` snapshot and fixed local-MPS campaign are
byte-bound, and central composition grants only `simulation_training_ready`.
Brief 148 is verified through `dce1995` by Reviewer Decision 178. Official
LeRobot completed the exact 250-update clean-base campaign with finite losses,
but the unassisted frozen seed-6 rollout made no strict contact and lifted only
0.000307 mm. The result is signed negative evidence and is not promoted.
Brief 149 is verified through `9b359a5` by Reviewer Decision 179. Exact replay
captured 244 policy-visited states; eight deterministic branches yielded four
recoveries, two near-failures, and two failures. The durable supplement retains
1,290 child frames and 2,580 fresh top/wrist observations with measured,
unpadded actions. Brief 150 is verified through `2436a14` by Reviewer Decision
180: 11/12 fixed cells passed and gripper scale 1.05 was the sole failure. Brief
151 is verified through `50abb80` by Reviewer Decision 181: both roles share
eight strict-v2 predicates, two complete simulator cases agree, and missing,
leaked, spoofed, camera/VLM, malformed, or undeclared evidence fails closed.
Brief 152 is verified through `7f264ab` by Reviewer Decision 182: the matched
synthetic pair has zero joint/action/event-time error and nine fixed diagnostics
route all declared mismatch categories without calibration or twin mutation.
Brief 153 is verified through `98a79a2` by Reviewer Decision 183: one synthetic
certificate passes, eleven one-factor timing failures route exactly, and every
failure blocks dynamics attribution. Brief 154 is verified through `fc54988`
by Reviewer Decision 184 without an optimizer: the six nominal successes plus
four strict-success recovery branches form one 10-episode, 2,330-frame package
dataset while all negative and held-out evidence remains outside training
statistics. Central composition grants only `simulation_training_ready`; a
separate brief must activate the frozen 500-update local-MPS campaign.
Brief 155 now activates exactly that bounded T20.24 campaign and its two frozen
held-out evaluations; it does not predeclare a passing result or policy
acceptance.
T20.24 is verified negative through `3abee49` by Reviewer Decision 185. Run 002
completed 500 finite local-MPS updates, but the frozen adapter made zero strict
contact on both held-out seeds and lifted only 0.000144 mm / 0.000143 mm. The
0/2 candidate is rejected; no accepted-policy pointer changed. The next policy
step is offline failure localization, not another unexamined optimizer rung.
Brief 156 opens that T20.25 diagnostic: compare both frozen adapters' complete
requested-action and visited-state traces with exact held-out source seeds 6-7,
separating frame-zero prediction error from later closed-loop drift. It runs no
optimizer and predeclares no next training hypothesis.
T20.25 is verified through `c234936` by Reviewer Decision 186. Recovery improves
sampled pre-contact action MAE by 0.04735 rad but regresses frame-zero MAE by
0.11137 rad. Because the clean prior action hash is not cross-process
reproducible despite an equal stack identity, training-effect attribution is
blocked. Repeated frozen-inference variability is the next causal proof; no
optimizer rung is justified yet.
Brief 157 opens T20.26 for two independent frame-zero inference batches per
adapter on one identical held-out observation. It separates same-process seeded
sampling from cross-process drift without applying an action or running an
optimizer.
T20.26 is verified through `437215b` by Reviewer Decision 187. Fixed-seed output
is bit-exact within and across processes for both adapters, so the older clean
hash gap is not reproduced in the current runtime. Distinct seeds span 0.18478
rad clean and 0.14797 rad recovery; the next comparison must pair candidates
over the same seed distribution before any optimizer decision.
Brief 158 opens T20.27 to compute that paired five-seed source-action comparison
offline from the verified T20.26 batches. No additional inference, rollout, or
optimizer is authorized.
T20.27 is verified through `e1fc104` by Reviewer Decision 188. Across five
paired seeds, recovery raises frame-zero source-action MAE from 0.50833 to
0.61926 rad and regresses every seed. Only gripper improves marginally. The
next causal proof is exact phase/sample exposure, not another optimizer rung.
Brief 159 opens T20.28 to replay the pinned official sampler and compare exact
clean versus recovery-campaign phase exposure without loading a model or
running an optimizer.
T20.28 is verified through `72a6360` by Reviewer Decision 189. Recovery saw 26
approach and 3 frame-zero samples versus clean's 14 and 0, so low early-phase
exposure does not explain the regression. Quantile/postprocessor shift is next.
Brief 160 opens T20.29 to cross-decode the same normalized five-seed candidate
outputs under clean and recovery action quantiles without model execution or
optimizer authority.
T20.29 is verified through `7473272` by Reviewer Decision 190. Applying the
recovery action quantiles to clean normalized outputs raises source-action MAE
by 0.11301 rad versus the observed 0.11094 rad regression, leaving a -0.00208
rad accounting residual. This is a postprocessor-only counterfactual, not full
training causality. A separately reviewed nominal-quantile-freezing ablation is
next; no optimizer is opened by this result.
Brief 161 opens T20.30 for the tests-first preflight of that ablation. It must
prove every dataset byte except `meta/stats.json` is unchanged, replace only
action q01/q99 with clean nominal values, bind the same sampler seed and
500-update budget, and obtain a fresh central simulation-only training decision
before T20.31 may load a model or optimizer.
T20.30 is verified through `2911e24` by Reviewer Decision 191. The distinct
10-episode / 2,330-frame dataset view preserves all non-statistics bytes and
changes only action q01/q99. Its fresh central decision grants only
`simulation_training_ready`; T20.31 is the separately bounded execution slice.
Brief 162 now activates T20.31 for exactly 500 local-MPS updates with the
T20.30 dataset/specification and frozen unassisted seed-6/7 evaluation. Its
result must be recorded whether positive or negative; policy acceptance stays
false pending a separate promotion decision.
T20.31 is verified through `151c6ee` by Reviewer Decision 192. The checkpoint
contains the intended clean action quantiles and 500 finite updates, but both
244-frame held-out evaluations ended with no strict grasp contact and 0/2
successes. The ablation changes action sequences without rescuing closed-loop
behavior. Further training is not justified before offline trajectory
localization. Brief 163 now opens T20.32 in the fresh owner window:
complete-trace earliest-divergence localization for T20.24 versus T20.31 plus
one bounded training-seed closed-loop reproduction probe per adapter as
capability-ladder Gate C evidence, with no optimizer.
T20.32 is verified through `7bbf7cf` by Reviewer Decision 193. All four
held-out action sequences replay exactly, but both adapters' seed-0 probes
diverge from the source action at frame zero and produce no strict grasp. The
first state error follows at frame one, so cadence, chunk boundaries, and
observation feedback are not the initiating fault. T20.33 is routed narrowly
to Gate B one-batch memorization/model-plumbing proof before further training.
T20.33 is verified negative through `bb3435b` by Reviewer Decision 195. The
one fixed batch received exactly 500 finite local-MPS updates, but the
five-seed objective ratio is 0.528248 and decoded maximum errors remain
0.843707-1.250647 rad against the 0.05 rad gate. No retry is authorized.
T20.34 now localizes base-versus-adapter parameter and inference movement on
that exact batch without an optimizer before any corrective campaign.
T20.34 is verified through `491eb6c` by Reviewer Decision 196. The rank-4
adapter is active, exactly replayable, lowers mean decoded error under every
seed, and moves toward the target under every seed. Dead checkpoint plumbing
and objective-to-inference opposition are rejected. T20.35 is one controlled
same-batch rank-16 capacity discriminator with no sweep or continuation.
The learned policy, real Robo Scan/I5 bundle, and physical canary exit gates
remain unmet; no paired-real/sim, hardware-observation, live-probe,
clock-synchronization, calibration/twin update, physical-qualification,
training-ready, posterior-calibration, or optimizer grant exists.

## Tonight's MVP Demo Composition (owner convergence directive 2026-07-16)

The near-term presentation surface is a verified runbook and evidence bundle,
not a new UI. It adds no authority and keeps scripted, learned-simulation,
metric-twin, and physical proof distinct.

1. **Declare and build.** Use `build_workcell_from_spec.py` to show the compact
   workcell declaration, deterministic MuJoCo compile, stability checks, and
   rendered preview. Label it a simulation fixture, not a real metric twin.
2. **Generate and compile R0.** Show the scripted expert completing unchanged
   strict-v2 grasps, the fixed 119+9 manifest, admission/quarantine results,
   the exact T20.23 base inclusion, training-only statistics, and held-out
   exclusion. Scripted success demonstrates the data path, never policy skill.
3. **Show learning plumbing.** Cite the signed one-batch T20.35x proof and the
   active candidate's exact R0 Gate A round-trip/parity evidence. Keep this
   separate from closed-loop policy behavior.
4. **Train ACT first.** Run the bounded standard-recipe T20.43 rung. Evaluate
   pre-registered checkpoints closed loop without an open-loop entry barrier.
   At the first strict-v2 Gate C pass, preserve the checkpoint, full trace,
   first divergence, margins, mirror MP4, and scorecard immediately.
5. **Continue policy evidence.** If ACT is negative, proceed directly to
   SmolVLA. If ACT is positive, publish the ACT demo before SmolVLA so a second
   model cannot delay delivery. PI0.5 remains conditional and must not block a
   valid ACT or SmolVLA demonstration.
6. **Publish one proof index.** At the first Gate C result or by 18:30 CDT,
   write `docs/autonomous-workflow/mvp-demo-status-2026-07-16.md` and a compact
   tracked manifest binding every artifact that actually exists. Include exact
   run/verification commands and one plain plumbing/policy/dataset/twin/canary
   scorecard. A negative result is publishable evidence, not learned success.

This composition is a **demo-ready simulation-learning MVP** only after a
learned, unassisted nominal strict-v2 Gate C pass. The complete product MVP
still requires the real Robo Scan/I5 metric twin and physical-policy canary
defined below.

## Paused Integration Queue

Robo Scan producer Brief 054 is committed and accepted at
`72eb02efe7e69981a5afab41a2733cd31ec03d4e`. Sim-link I2 and the reference-only
I3 descriptor are verified at `67daad9`, `cb4e5a0`, and `d01416b`. The next
cross-repository task is therefore **I4 in Robo Scan**, after real M1–M4 metric
evidence. The expected USB cable does not alter the sim-link queue or grant a
hardware session.

When I4 eventually lands, sim-link may open I5 as a separate reviewed task. I7
deduplication remains blocked until two real metric handoffs and one end-to-end
compile prove that retirement is safe.

I4/I5 and the physical canary are full-MVP critical-path items, not optional
polish. They proceed independently of R0/R1 until their inputs are ready; an
active irreversible generation/training boundary is allowed to finish, then a
real immutable I4 export makes I5 the next metric-twin compile boundary. No
synthetic fixture, descriptor-only receipt, or scripted motion may fill these
exit slots.

Calibration splits into two stages with different prerequisites. **Instrument
calibration** — camera intrinsics, hand-eye, robot/world frames, clock
alignment, command cadence/latency, joint tracking, and gripper
command-to-width mapping — is a property of the capture and execution stack
and may proceed under fresh owner permits before a learned policy exists.
**Transfer calibration** — the one friction parameter, contact discrepancy,
and task-event alignment — waits for a strict-v2-passing policy and the
compiled metric twin, and fits only what the single-anchor task exercises.

The approved physical calibration intake is the WCW-1 witness: a printed,
fiducialized, cartridge-loaded object with measured as-built dimensions and
masses, an optional removable depth-metrology plate, and known
center-of-mass/inertia configurations from selected precision bearing balls.
Robo Scan owns its CAD/tag geometry, reference print profile, as-built
measurement protocol, and `CalibrationArtifactReceipt`. Sim-link consumes only
that receipt through the already verified
`measured_inertial_intake`/`production_inertial_compiler` path, so MuJoCo
inertials derive from measured masses, never slicer density. Grasp-face
contact bands, gripper-width fit coupons, and push/lift probes later feed
transfer calibration through the paired trace runner; none of this grants a
hardware session by itself.

## MVP Exit Condition

The project may use two cumulative labels.

**Demo-ready simulation-learning MVP** requires all of:

- One signed R0 dataset/statistics/mixture boundary with held-out evidence
  excluded from training and statistics.
- Explicit Gate A and one-batch learning/plumbing evidence, including the
  existing T20.35x positive proof, without relabelling that checkpoint as the
  product policy.
- At least one approved learned policy (ACT, SmolVLA, or PI0.5) performing an
  unassisted nominal strict-v2 MuJoCo grasp in closed loop.
- A full trace, mirror MP4, compact evidence manifest, exact replay/verification
  commands, and a plain proof-state scorecard.

**Full SceneSmith MVP** additionally requires all of:

- The learned policy remains acceptable across the declared discrete ensemble.
- One real Robo Scan capture becomes a metric `WorkcellBundle` with fiducial
  scale, held-out evidence, uncertainty, and lineage.
- Sim-link I5 compiles that exact bundle with pinned SO-ARM100 into a
  deterministic MuJoCo twin candidate.
- One separately authorized, owner-present, low-speed canary is scored by the
  hardware-observable evaluator and produces a paired trace.
- Fork-generated recovery data has been evaluated against a success-only
  baseline on the same gates, and grid training against nominal-only training.
- The observable evaluator carries a signed confusion matrix against strict-v2
  with ambiguous outcomes failing closed, and references no privileged state.
- The canary brief contains one plain four-section scorecard — policy,
  reconstruction, twin/runtime, canary — and the result is promoted or
  quarantined only through the existing evidence process.
- Every claim preserves exact source, task, evaluator, dataset, processor,
  normalizer, policy, twin, and evidence identities.

Until then, use narrower labels: simulator strict success, ensemble robustness,
metric workcell candidate, paired replay, or constrained physical canary. None
alone is full autonomous physical-robot proof, and a demo-ready simulation-
learning MVP is not the full SceneSmith MVP.
