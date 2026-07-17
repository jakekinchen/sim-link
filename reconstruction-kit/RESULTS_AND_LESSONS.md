# Results and Lessons

## What demonstrably works

### 1. Constructive source behavior beats open-ended search

A geometry-derived grasp source produced the full R0 strict-success set across
the bounded training and held-out construction space. This replaced broad pose
search with explicit pad geometry, contact semantics, phase timing, and one
deterministic controller. Preserve that pattern: solve deterministic structure
constructively, then spend learning capacity on policy behavior.

### 2. Strict consequence evaluation prevents false wins

Contact alone, object displacement, low open-loop error, and visually plausible
motion all produced tempting partials. Strict-v2 requires the conjunction:
antipodal pad contact, no forbidden assistance, the declared phase gates,
25 mm lift, stable hold duration, and truthful release semantics. The evaluator
must remain unchanged while comparing policies.

### 3. Native package execution is more trustworthy than reimplementation

The useful stack is pinned LeRobot plus a thin governance shell. Actual package
processors, datasets, policies, and postprocessors are executed and observed.
SceneSmith owns the coordinate bridge, identities, gates, and bounded runners.
This eliminated several classes of “almost equivalent” preprocessing errors.

### 4. Content-addressed boundaries make long autonomous runs auditable

Canonical JSON, SHA-256 identities, exact source commits, output absence checks,
one-use markers, first-pass selection, signed mirrors, and independent verifier
passes prevented retries and documentation drift from silently changing the
meaning of results.

### 5. Dual cadence exposes closed-loop behavior

Chunk-50 and receding-10 often produce materially different interaction. Both
must be retained, along with queue reset, chunk-start states, executed tail
lengths, and MP4/trace identities. A post-hoc render is useful evidence; a
render integrated into every evaluation is better.

## Clean negative findings

### SmolVLA

SmolVLA trained stably for 5,000 updates but did not pass Gate C. Its strongest
partial reached 18.061 mm lift with 73 contact frames at checkpoint 1,000 under
receding-10. That is meaningful interaction, but still a negative under the
unchanged 25 mm and phase-duration conjunction. More of the same run is not
licensed by this evidence.

### PI0.5

The long Gate B ladder was diagnostically useful but should not be replayed.
Key findings:

- Warmup was not the silent killer in the one-batch runner; it used constant-LR
  AdamW.
- Early LoRA updates moved in the target direction but covered only a small
  fraction of the target distance.
- Exact decode analysis found active-dimension interference beginning during
  denoising, with shoulder lift and wrist roll dominating physical error.
- Uniform loss in normalized space underweighted large-standard-deviation
  joints relative to the physical-radian gate.
- Std-derived joint weighting improved the candidate, but the retained X result
  passed the amended gate on only three of five seeds; remaining violations
  clustered around gripper/grasp timesteps.
- Repeated same-shape failures justified interrogating fixed objectives and
  gates, not adding endless optimizer rungs.

Treat PI0.5 as a compatibility/stress baseline. SmolVLA supplies one clean
model negative. ACT is also now a clean model negative: after two
evidence-path failures and the original T20.43c interruption, T20.43c-R2
completed the unchanged 10,000-update campaign and fourteen rollouts without a
Gate C pass or infrastructure failure.

### ACT

The terminal ACT result is structured, not featureless. Chunk-50 checkpoints
at updates 2,500, 5,000, 7,500, and 10,000 completed strict grasp, unassisted
lift, unsupported/stable hold, and lower, with 37–45.674 mm lift. The final
chunk-50 rollout lifted 37.655304 mm and failed only
`release_final_contact_clear`; final receding-10 lost grasp hold and lifted
0.502 mm. This points the fork toward consequence-aware release completion,
short-horizon state-based control, and evaluator-owned task predicates—not a
third attempt at the same ACT recipe or a weakened Gate C.

## Infrastructure failures that are not model results

- The first ACT standard attempt completed checkpoint-0 inference but its
  renderer child lacked MuJoCo. That consumed the original marker without
  resolving trained ACT capability.
- The separately authorized ACT replacement reached fresh model/optimizer
  construction, checkpoint 0, and one untrained chunk-50 rollout, then the
  mirror rejected the distinct T20.43b trace schema. Zero optimizer updates
  occurred. The pre-run smoke had replayed a valid T20.43 trace, proving the
  interpreter and MuJoCo path but not the future schema dispatch.
- Smoke tests must exercise the exact future artifact schema and entrypoint,
  not merely a nearby retained trace. The immutable-safe
  `render_rollout_mirror_v2.py` compatibility entrypoint fixes future dispatch
  without changing the legacy renderer bytes bound by signed history.
- Across the sequence, three scarce experiment slots were lost to evidence-path
  integration—a venv import, a renderer entrypoint, and a mirror schema—not to
  policy science. Fork rule: every one-use attempt gets a pre-marker smoke that
  executes the exact output-artifact schemas end to end. Infrastructure
  failures receive explicit replacement semantics in the new design rather
  than being misreported as model negatives; this does not silently authorize a
  current-repo retry.
- Ephemeral `uv --with` environments are unsuitable evidence identities. The
  corrected path binds one stable interpreter plus the exact cached MuJoCo
  support-tree identity.
- T20.43c then proved the correction: actual-schema mirrors passed, checkpoint
  tensors were bit-exact, AdamW state was empty, the sampler was unadvanced,
  and training reached update 728 with checkpoint-500 evidence. A sibling agent
  applied an older scheduling instruction and sent SIGINT. Preserve that as an
  inconclusive owner-directive interruption—not a model negative, not an
  infrastructure failure, and not automatic retry authority.
- The separately reviewed T20.43c-R2 replacement then ran the complete fixed
  recipe. It is the model result the earlier infrastructure failures could not
  supply: verified terminal negative, no Gate C pass, no infrastructure
  failure, no retry. Preserve the original interruption and the later result as
  separate immutable boundaries.
- Retaining only tensor hashes is insufficient when future model-free rescoring
  is required. Preserve the signed tensor payload itself in a tracked evidence
  path, or explicitly record that reproduction will require a model load.
- A path is not an immutable source identity. When the T20.41 route document
  later received an authorized addendum, the historical R0 hash guard correctly
  rejected the mutable path. Portable code now reads an exact tracked snapshot
  of the original commit while preserving the original path/commit reference.

## Things to keep out of the new core

- The T20.35 alphabet of one-off optimizer corrections.
- A second training datastore beside native `LeRobotDataset`.
- A general reward compiler, skill graph, scientist service, learned dynamics
  model, or alternative simulator before a concrete failure demands one.
- Raw asset expansion as a response to a behavioral bottleneck.
- CUDA/A100 rental merely to reproduce a structured local failure.
- Automatic ingestion of Robo Scan artifacts or automatic physical-twin
  qualification.
- Hardware control inside the high-level agent loop.
- Parent/child Python dispatch after the W1 transfer proof; the fork uses one
  pinned LeRobot interpreter and in-process rendering.
- Cameras or audiovisual datasets in the fast state-RL loop.
- A second robot path beside the gateway.
- Per-task XML edits, task alphabets, and committed output trees.

## Strategic pattern to carry forward

Use two primary tracks against one separately owned evaluator:

1. ACT as the deterministic imitation baseline.
2. State-based RL on joint state plus object pose, light parquet, 60-frame
   success-terminated tasks, and T20.38 direction-correct margins.

SmolVLA and PI0.5 are day-three stretch tracks, not parallel blockers. Training
may be nondeterministic across MPS/CUDA; CPU/fp32 evaluation verdicts must be
bit-identical across Macs and Linux. Freeze one workcell XML and add tasks as
registry data. Emit one `RUN_RECEIPT.json` per run and keep outputs ignored from
the first fork commit.

Once one learned policy passes Gate C, add counterexample-guided,
posterior-constrained domain randomization: search only plausible scene/twin
parameters, retain minimal failures, retrain on evidence-bearing counterexamples,
and keep a fixed challenge archive. Do not launch that loop before a baseline
policy can solve the nominal task.

The simplification deliberately keeps three hard rules: frozen held-out
scenes/seeds, a replayable signed artifact for every claim, and evaluation
ownership separate from training. Copied permits and reviewer artifacts remain
inert history.
