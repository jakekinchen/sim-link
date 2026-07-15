# Sim-Link MVP Execution Plan

## Decision

The program will optimize for the next causal proof, not for architectural
completeness. The immediate sim-link long pole is T20.17: initialize a clean
`pi05_base` policy with source-dataset statistics, train with a realistic but
bounded local update budget, and test unassisted strict-v2 grasp behavior in
MuJoCo. Robo Scan proceeds independently toward its first real metric capture.

This plan is a task-ordering source, not an authority source. Live authority,
training readiness, and proof labels remain mechanically owned by
[`project_state.json`](./autonomous-workflow/project_state.json) and the central
authority composer.

## Product Cut

### Build in the current sim-link lane

- T20.17 clean-base, dataset-native PI0.5 fine-tuning and fixed strict-v2
  evaluation.
- Recovery and perturbation episode expansion from the already verified MuJoCo
  state-branching primitive.
- A small discrete uncertainty ensemble over cube pose, friction, command
  latency, and gripper mapping using the existing randomization path.
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

### Defer until the first verified sim-to-hardware task success

- Posterior inference and posterior-driven calibration.
- A generalized cousin algebra or full taxonomy.
- Fidelity certificate v1 beyond a plain task scorecard.
- Event-triggered flight recorder, drift monitor, live scene deltas, and
  renderer qualification.
- A dependency-light shared contracts package, unless two real schema versions
  first demonstrate repeated semantic drift.

### Cut until evidence creates a need

- RL and a reward/curriculum compiler.
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

## Sim-Link Task Queue

Only the first dependency-ready task is active. Later tasks are planned and do
not inherit authority from this document.

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
localization, and the current run cutoff prevents opening that next slice now.
The learned policy, real Robo Scan/I5 bundle, and physical canary exit gates
remain unmet; no paired-real/sim, hardware-observation, live-probe,
clock-synchronization, calibration/twin update, physical-qualification,
training-ready, posterior-calibration, or optimizer grant exists.

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

## MVP Exit Condition

The program is in a good MVP state only when all of the following are true:

- A PI0.5 adapter performs an unassisted strict-v2 grasp in nominal MuJoCo and
  remains acceptable across the declared discrete ensemble.
- One real Robo Scan capture becomes a metric `WorkcellBundle` with fiducial
  scale, held-out evidence, uncertainty, and lineage.
- Sim-link I5 compiles that exact bundle with pinned SO-ARM100 into a
  deterministic MuJoCo twin candidate.
- One separately authorized, owner-present, low-speed canary is scored by the
  hardware-observable evaluator and produces a paired trace.
- Every claim preserves exact source, task, evaluator, dataset, processor,
  normalizer, policy, twin, and evidence identities.

Until then, use narrower labels: simulator strict success, ensemble robustness,
metric workcell candidate, paired replay, or constrained physical canary. None
alone is full autonomous physical-robot proof.
