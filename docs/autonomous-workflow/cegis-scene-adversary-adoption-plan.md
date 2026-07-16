# CEGIS Scene Adversary Adoption Plan

**Date:** 2026-07-16

**Decision:** Adopt the architecture and its preparatory contracts. Do not build
or run the active scene-search loop until a policy is competent enough to yield
informative differential failures.

**Assessment:** 9/10 strategic fit; 2/10 value for an active falsifier at the
current Gate B boundary.

This is a roadmap and contract-design artifact, not an authority source. It
does not amend the verified T20.36l result or proposed T20.36m brief, open Gate
C, authorize a model load or optimizer, grant policy acceptance, or permit
hardware, external compute, or Brev.

## Executive Decision

Scene adversarial testing is an unusually good fit for sim-link because the
repository already owns most of the difficult substrate:

- a deterministic, manifest-producing scene randomizer with validity checks;
- a fixed one-factor perturbation grid with exact replay evidence;
- strict-v2 semantic predicates and per-gate measurements;
- a geometry-derived constructive expert that can be rerun from scene state;
- paired-trace, timing, content-address, and quarantine contracts; and
- policy-independent evaluation paths already used across ACT, SmolVLA, and
  PI0.5.

The missing product is not another learned antagonist. It is a bounded verifier
that searches only valid scenes, proves that the constructive expert remains
competent on each scene, compares the expert and candidate under one evaluator,
and archives novel policy failures as immutable regression evidence.

The active search is intentionally deferred. T20.36l closed fail-closed: ACT
fails the frozen consequence gate and SmolVLA is indeterminate because its
decoded tensors were not retained. T20.36m is only a proposed tensor-reproduction
route and has no owner or central inference authority. No learned policy has
passed one training episode in closed loop. Searching today would mostly produce
ordinary policy failures or `both_fail` rows, not a capability frontier. The
immediate work is limited to two reusable contracts:

1. a canonical quantitative strict-v2 evaluation receipt; and
2. a counterexample archive schema with replay and routing semantics.

## What The Literature Contributes

| Source idea | Useful principle | sim-link adaptation |
|---|---|---|
| [CEGIS](https://people.csail.mit.edu/asolar/papers/thesis.pdf) | Alternate candidate construction with a verifier that returns counterexamples; future candidates must account for accumulated examples. | A checkpoint is the candidate, bounded scene search is the verifier, and the content-addressed archive is the accumulated counterexample set. The loop never claims formal completeness over a continuous scene domain. |
| [PAIRED](https://proceedings.neurips.cc/paper/2020/hash/985e9a46e10005356bbaf194249f6856-Abstract.html) | Regret focuses environment design on scenes where a stronger solver succeeds and the protagonist does not, avoiding unsolvable worst cases. | The constructive expert can replace the learned antagonist only when it independently passes the same scene. Expert success is therefore a hard regret precondition, not an assumption. |
| [ACCEL](https://proceedings.mlr.press/v162/parker-holder22a.html) | Incrementally edit archived levels and retain environments near the agent's capability frontier. | Start from deterministic one-factor edits of valid archived manifests. Add bounded two-factor or evolutionary edits only after one-factor search has useful yield and acceptable duplicate/invalid rates. |
| [Prioritized Level Replay](https://proceedings.mlr.press/v139/jiang21b.html) | Revisit levels according to learning potential instead of sampling every level uniformly. | Keep a mandatory regression tier and a separate challenge tier. Prioritization may schedule development replays, but a promotion decision still runs the complete required tier. |
| [Quantitative temporal-logic robustness](https://www.georgejpappas.org/wp-content/uploads/2024/04/RV06.pdf) | Preserve signed distance from satisfaction or violation instead of collapsing every trace to one Boolean. | Retain strict-v2 Boolean truth as authoritative while emitting candidate-independent signed margins and a bottleneck robustness score for search and diagnosis. |
| [VerifAI](https://people.eecs.berkeley.edu/~sseshia/pubs/b2hd-verifai-cav19.html) and [adaptive stress testing](https://arxiv.org/abs/1811.02188) | Simulation-guided falsification supports systematic fuzzing, counterexample analysis, dataset augmentation, and differential regression testing. | Keep falsification, diagnosis, regression, and optional training ingestion as separate authority steps. Search for likely/meaningful failures, not merely any invalid or impossible failure. |

The result is CEGIS-inspired rather than formal CEGIS: MuJoCo sampling cannot
prove universal correctness, and the learned policy is updated by separately
authorized training rather than symbolic synthesis.

## Repository Evidence And Gaps

| Existing surface | What is already proven | Gap before adversarial search |
|---|---|---|
| `scenesmith/robot_lab/domain_randomization.py` | Deterministic seeds, physical scene validation, explicit randomized/fixed fields, and a manifest. | Latency, action hold, gripper mapping, and posterior membership need one canonical perturbation-envelope contract. |
| T20.19 discrete recovery ensemble | Twelve one-factor cells replayed exactly; 11/12 passed; gripper scale 1.05 was the sole strict-v2 failure. | It tested a source-bound recovery suffix, not a learned policy versus a freshly re-derived expert. |
| `act_grasp_closed_loop.py` | Current rollouts already expose measured value, threshold, comparison, signed margin, and failed-gate rows. | The margin schema is not yet a policy-independent, versioned receipt shared by every evaluator. Raw values have mixed units and cannot be averaged safely. |
| T20.36e/f/k/l | Mean error can conceal sparse consequence-relevant failures; T20.36k derives candidate-independent phase/joint thresholds. | Gate B action-error evidence and strict-v2 rollout robustness must remain distinct while sharing the same receipt conventions. |
| T19.0l constructive grasp | A deterministic geometry-derived expert achieved a complete unassisted strict-v2 cycle on its verified scene. | Expert competence must be rerun and proven per adversarial scene. One historical success does not certify the expert over a new perturbation. |
| T20.21/T20.22 | Paired trace and timing schemas already separate actions, state tracking, events, clock source, latency, and hold. | The counterexample receipt must bind these identities instead of copying or weakening them. |
| Artifact contract and compiler quarantine | Canonical finite JSON, signed identities, content-addressed references, and reasoned quarantine are established patterns. | A dedicated archive lifecycle and duplicate key are still needed. |

## Quantitative Receipt Contract

The immediate receipt task should derive a new artifact from immutable evidence;
it must not rewrite historical ACT, SmolVLA, PI0.5, T20.19, or strict-v2
artifacts.

Each predicate row should contain:

- predicate and phase identifiers;
- measured value, threshold, comparison, and unit;
- raw signed margin, where positive means passing and negative means failing;
- a candidate-independent normalization scale declared by the evaluator spec;
- normalized signed margin;
- availability and evidence-source identity; and
- Boolean pass/fail plus any discrete guard classification.

Exact provenance and actor-integrity predicates such as zero projection, zero
assistance, correct actor role, and complete source binding remain hard guards.
They should not acquire a misleading continuous score. Missing, non-finite, or
guard-failing evidence invalidates the receipt and fails closed.

For continuous and ordered-count predicates, define the trace robustness as the
minimum normalized signed margin across mandatory predicates. This mirrors the
bottleneck semantics of a conjunction: a strong mean cannot hide one failed
shoulder, gripper, contact, release, or timing requirement. Always retain the
full vector, raw values, minimum, median, and maximum for diagnosis. Do not use a
weighted mean to grant strict success.

Consequence classes from T20.36k may provide candidate-independent tie-breaking
and triage metadata, but they must not be fitted to candidate errors and must not
change strict-v2 Boolean semantics.

## Regret And Search Objective

For valid scene manifest `theta`, candidate policy `pi`, and freshly rerun
constructive expert `E`:

```text
regret(theta, pi) = robustness(E, theta) - robustness(pi, theta)
```

This value is admissible only when:

1. the scene and perturbation manifest are valid, finite, in scope, and exactly
   replayable;
2. the expert independently completes the same strict-v2 task on that scene;
3. expert and policy receipts bind the same scene, parent state, evaluator,
   simulator, timing, and perturbation identities; and
4. all actor-integrity and evidence guards pass.

Search ranking is lexicographic, not a single reward that can erase semantics:

1. expert succeeds and policy fails;
2. larger positive regret / more negative policy bottleneck margin;
3. physically plausible and, when available, higher posterior support;
4. novel failure signature and parameter vector; then
5. lower simulation cost.

Use predeclared inference seeds and exact paired repeats for stochastic policy
paths. Report worst, median, and per-seed margins. The search objective may use
the predeclared worst-seed score, but it may not select a favorable seed after
observing results.

Falsification priority and curriculum priority are different. Deep failures are
valuable for evaluation; near-frontier failures or demonstrated learning
progress may be better for later training. A search receipt must never decide
training eligibility by itself.

## Expert-Competence Routing

`both_fail` is not a sufficient cause code. A constructive expert failure does
not prove that a scene is impossible.

| Expert | Policy | Route | Archive / authority effect |
|---|---|---|---|
| pass | fail | `actionable_policy_counterexample` | Add to the open challenge tier; replay on every selectable checkpoint. It becomes a required no-regression case only after a reference checkpoint passes it. |
| pass | pass | `solved_scene` | Retain as coverage or holdout evidence; do not inflate the counterexample count. |
| fail | pass | `expert_gap_policy_success` | Quarantine from regret scoring and investigate expert brittleness; preserve the truthful policy success. |
| fail | fail | `unresolved_competence_or_feasibility` | Quarantine from policy blame and training. Run a separately specified expert/scene-feasibility diagnosis. Do not label it impossible without independent proof. |
| invalid/error | any | `scene_or_infrastructure_invalid` | Reject or quarantine; never count as a policy counterexample. |

The expert competence check must bind a fresh constructive solve and rollout,
strict-v2 receipt, deterministic repeat, solver/request identities, simulator
identity, and zero assist/projection facts. If the expert implementation cannot
represent a perturbation such as latency or gripper mapping, the result is an
expert-scope gap rather than policy regret.

## Counterexample Receipt And Archive Lifecycle

The first schema should include these immutable groups:

```text
scene
  base scene, parent state, manifest, parameter vector, seed
  structural twin, simulator, perturbation-envelope, posterior-support status
expert
  constructive request/solver identities, trace receipt, competence result
policy
  family, config, checkpoint, processor, inference seeds, trace receipt
evaluation
  strict-v2 spec/evaluator identities, predicate margins, bottleneck scores
  expert-policy regret, failure signature, paired-trace/timing references
routing
  route code, archive tier, replay requirement, duplicate/predecessor links
provenance
  creator/search version, source references, canonical identity, file hash
authority
  evidence-only flags; training, acceptance, transfer, promotion all false
```

Canonical duplicate identity should bind the scene manifest, perturbation
vector, parent state, simulator/evaluator versions, and failure signature. The
policy checkpoint is a replay result identity, not part of the scene's stable
archive identity, so multiple policies can be compared on the same case.

Archive lifecycle states:

- `open_challenge`: expert passes and at least one policy fails;
- `regression_required`: a named reference checkpoint passed the case;
- `resolved_but_retained`: the current candidate passes, but history remains;
- `expert_gap` or `feasibility_unknown`: excluded from policy gating;
- `invalid_or_out_of_envelope`: rejected from active replay;
- `duplicate`: linked to a canonical entry; and
- `stale_requires_revalidation`: a bound simulator, evaluator, twin, or
  perturbation contract changed.

Every checkpoint eligible for selection after Gate C must execute the complete
active replay manifest. It need not already pass every `open_challenge`, but it
must report every result and may not regress any `regression_required` case.
Promotion runs the complete required tier regardless of development-time replay
prioritization. Archive pruning may change scheduling, never erase historical
receipts or silently remove a required regression.

Counterexamples are evaluation evidence, not training records. Importing an
expert trace into a dataset requires a separate compiler slice that rechecks raw
frame/action provenance, actor inputs, phase boundaries, eligibility,
quarantine, statistics, mixture, and central training authority.

## Gripper-1.05 Bootstrap Entry

The T20.19 `gripper_scale_high` cell should be archive seed 0001, but its honest
initial class is `source_controller_boundary_negative`, not
`actionable_policy_counterexample`:

- the cell applied a deterministic 1.05 command transform to the same
  source-bound recovery suffix;
- it achieved 31.849 mm lift but only 21/64 stable-hold and 9/24 lower strict-v2
  frames;
- no learned policy was evaluated; and
- the constructive expert was not freshly re-derived and rerun under the new
  scene/actuator contract.

The migrated entry should bind the existing T20.19 identities without rewriting
them. Before it can enter policy regret or regression gating, a future slice
must decide whether a freshly re-derived expert is competent under the exact
gripper-mapping perturbation.

## Roadmap Integration

### Phase 0 - Current comparison boundary

- Preserve T20.36l and T20.36m's verified fail-closed results and historical
  negative labels.
- T20.36m reproduced all five retained SmolVLA hash pairs and failed the frozen
  amended Gate B on every seed. T20.35x remains to be scored under that same
  gate before the three-candidate comparison is complete.
- Do not change Gate B from this plan or add another candidate architecture.
- Preserve this document as a non-authorizing roadmap.

### Phase 1 - Short-term, policy-agnostic preparation

**T20.38 - Quantitative strict-v2 receipt contract**

- Implement one shared derived schema/verifier for existing and future policy
  evaluations.
- Prove raw/normalized margin derivation, hard guards, mixed-unit handling,
  bottleneck semantics, source identity, determinism, and no history rewrite.
- Backfill only derived receipts from selected immutable positive/negative
  artifacts; no model load, rollout, or training.

**T20.39 - Counterexample archive schema and bootstrap**

- Implement the receipt, manifest, lifecycle, duplicate, stale-reference, and
  routing verifiers.
- Migrate gripper-1.05 as seed 0001 with the boundary-negative classification
  above.
- Add synthetic/fixture tests for all routing rows, but do not build search or
  make the archive a policy gate yet.

These tasks are useful before policies work because they improve every future
evaluation receipt and prevent later evidence migration from becoming an ad hoc
rewrite. T20.38 and T20.39 remain filler roadmap entries until the active
T20.35x comparison and any resulting Gate C priority work are dispositioned.

### Phase 2 - Gate C archive replay, no adversarial search

**T20.40 - Fixed archive replay harness**

- Entry: Gate C mechanically passes for at least one unassisted checkpoint.
- Replay the immutable active archive against a supplied checkpoint using fixed
  scenes and seeds; do not mutate scenes or train.
- Require complete replay for checkpoint selection, enforce the tier semantics
  above, and emit policy-family-neutral results.
- Run the gripper-1.05 expert-competence check before treating it as a policy
  challenge.

If Gate C is still uniformly negative, T20.40 remains pending. Replaying or
searching a failure-only policy adds no useful localization.

### Phase 3 - Gate F one-factor falsification

Replace T21.6's generic one-factor curriculum with a
competence-gated CEGIS scene adversary and archive replay task.

Hard entry is a Gate D pass: one policy must succeed on the complete constructive
training set. Operational entry should also require at least one Gate E nominal
held-out success. If Gate E is uniformly negative, fix generalization before
searching the robustness envelope.

The first active search must:

- use only bounded one-factor edits over declared cube pose, friction, command
  latency/hold, and gripper mapping axes;
- re-derive and rerun the expert for every scene;
- keep uncalibrated simulation-envelope evidence distinct from a later
  T19.5-qualified-posterior search;
- use fixed budget, seeds, mutation schedule, novelty rule, and untouched
  realism holdout;
- archive only valid, expert-competent differential failures; and
- grant no training, policy acceptance, transfer, or promotion authority.

### Phase 4 - Long-term compound search and optional learning loop

Only after Phase 3 has useful actionable yield:

1. add bounded two-factor edits seeded from near-boundary archive entries;
2. consider ACCEL-style evolutionary mutation with explicit validity,
   plausibility, novelty, and cost terms;
3. run a separate posterior-supported mode after T19.5 without relabelling the
   earlier structural-simulation archive;
4. optionally compile expert-success/policy-failure traces into an imitation
   dataset under a new compiler and central training-authority decision; and
5. train a new candidate, replay the complete archive, then evaluate the
   untouched holdout before any acceptance decision.

A learned scene adversary, residual-RL coupling, generalized reward compiler,
or automatic counterexample-to-training path remains cut until the bounded
deterministic loop proves that it cannot supply adequate coverage.

## Success Metrics And Stop Rules

Track at least:

- valid-scene and expert-competence rates;
- actionable counterexamples per simulator call;
- duplicate and stale-entry rates;
- replay determinism and runtime;
- open-challenge closure and regression counts;
- failure-signature and parameter-space coverage; and
- untouched-holdout strict success and bottleneck margins.

Stop or route away from active search when:

- Gate D is not passed or Gate E is uniformly negative;
- most generated scenes are invalid, out of envelope, or expert-incompetent;
- `both_fail` dominates actionable differential failures;
- duplicate yield is high enough that the mutation strategy adds no coverage;
- simulator/evaluator/twin drift makes archive entries stale; or
- a proposed training step lacks separate dataset and central authority.

No finite search budget proves global robustness. The truthful outcome is a
versioned archive, bounded coverage report, and explicit remaining envelope.

## Explicit Non-Goals

- no hardware or camera access;
- no physical perturbation execution;
- no Brev or external compute;
- no optimizer or model execution from this plan;
- no second learned antagonist in the MVP;
- no reward replacement for strict-v2;
- no automatic training on failures;
- no claim that expert failure proves scene impossibility;
- no posterior or sim-to-real claim from the T20.19 grid; and
- no policy acceptance, physical transfer, or promotion from archive results
  alone.
