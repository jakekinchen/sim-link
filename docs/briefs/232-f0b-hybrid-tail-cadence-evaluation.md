# Slice Brief 232 - F0b Hybrid Tail-Cadence Evaluation

**Date:** 2026-07-17

## Objective

Test F0a's cadence/gate mechanism once, without training, by evaluating the
retained T20.43c-R2 update-10,000 ACT checkpoint on the exact seed-0 episode.
Keep chunk-50 execution through frame 175, discard the remaining queued tail
once at frame 176, and then re-decode every ten executed actions. Preserve a
replayable full trace and a signed mirror whether strict-v2 Gate C passes or
fails.

This brief activates implementation and deterministic tests only. Checkpoint
reads, policy construction, inference, simulator execution, and rendering stay
closed until the implementation, model-free authority bundle, and separate
pre-run acceptance are each reviewed, committed, pushed, and exact on origin.

## Frozen source boundary

- F0a closeout commit:
  `951c5254950b734677a6d185c227c56724182b58`.
- F0a result:
  `278e8bc772dc879622a226abe22665d320421925045ad9b3cb1f88b1c31153a4`,
  file SHA-256
  `2ef689c7f51784a799db20cba5dec5f35c51422608b5a78ff4bd94346da06fa6`.
- T20.43c-R2 marker `dfe3ff05...`, run `82a06083...`, result
  `bf2c8b46...`, scorecard `6f848570...`, retention `e565e17a...`, and final
  receipt `be11a258...` remain immutable.
- Exact checkpoint path:
  `outputs/robot_lab/t20_43c_r2_act_replacement_run_001/checkpoints/step_10000`;
  tree identity
  `c77ee36250f921dbdfc7b19802ab8705c9795b298fa14d4a2b1825acf68451ab`.
  It contains `config.json` at 1,714 bytes / SHA-256
  `1b2ba89880e421180962a0c862b37bfc854d16e5f8811e82210a64ecf6d09aaf`
  and `model.safetensors` at 206,494,928 bytes / SHA-256
  `673c87a5c411997e5a0e146702df95a0e301ba8585ec1cba64dca25b6d55170c`.
- Frozen comparator trace:
  `77bf82ce917c2a30cc3bfc915b887f0e6af98c8c8a397f022b633ccf23c7d19c`
  (`step_10000_chunk_50.json`). Its 37.655304 mm final lift fails only
  `release_final_contact_clear`; its maximum lift is not relabeled as final
  success.
- Source episode file SHA-256
  `586a3e67034a577bf046381837aebe68d3d5febdce6b1c51dbcb6f0be4968b54`,
  raw rollout identity
  `9e186088c9ca82fa9c58cb6e3870f322a9c2a84405d5ea23152b822fb9d4abdb`,
  simulation seed 0. R0 statistics remain `02ba0e70...`.

The implementation must hash-check these sources before any model action,
reject symlinks and path aliases, and bind the exact LeRobot checkout/runtime,
policy source, MuJoCo scene/assets, coordinate conversion, source phase plan,
strict-v2 evaluator, and renderer entrypoint without deserializing tensors.

## Frozen execution semantics

- Initialize Python, NumPy, and torch RNGs with original ACT training seed
  `20260801` immediately before one `ACTPolicy.from_pretrained` construction.
- Load the checkpoint once. Do not create an optimizer, scheduler, sampler, or
  dataset loader. `training_lock` remains closed throughout.
- Run exactly one seed-0, 244-frame policy-owned MuJoCo episode against the
  same source initial state and strict-v2 evaluator. No scripted action,
  projection, assistance, intervention, phase token, wall-clock trigger, or
  source-action fallback is allowed.
- Start with an empty action queue. Decode starts are exactly
  `[0, 50, 100, 150, 176, 186, 196, 206, 216, 226, 236]`; executed lengths are
  `[50, 50, 50, 26, 10, 10, 10, 10, 10, 10, 8]`, summing to 244.
- The frame-150 decode predicts 50 actions. Execute offsets 0-25 at frames
  150-175, then at frame 176 discard exactly 24 queued actions and record their
  values and SHA-256 before the one manual tail-transition reset. Subsequent
  10-step queues empty naturally; the final decode executes eight actions and
  retains its two unexecuted predictions as terminal tail evidence.
- Every decode row retains the full 50x6 physical-radian chunk, its hash, the
  executed prefix length, and any discarded/unexecuted suffix. Every frame
  retains observation, requested policy action, source comparison, phase,
  chunk index/offset, contact/gate inputs, and actor ownership needed for
  independent strict-v2 replay.
- Preserve the original chunk-50 trace unchanged as comparator. Do not rerun a
  baseline and do not evaluate another checkpoint or seed.

## Authority and one-use boundary

Implementation must define canonical signed task-local owner, central-request,
central-decision, runtime-preflight, permit, pre-run-acceptance, attempt-marker,
trace, result, scorecard, retention, mirror-manifest, and final-receipt
contracts. Use disjoint `F0b` paths and run root
`outputs/robot_lab/f0b_hybrid_tail_cadence_run_001`.

The existing central composer may grant its prerequisite
`simulation_training_ready` decision only after all inputs agree, but the F0b
permit must narrow that prerequisite to one policy evaluation and explicitly
deny optimizer creation/training. A central prerequisite is not a training-lock
transition. The one-use marker must be absent and every output path absent and
unaliasable at preflight, then be written before the first checkpoint tensor is
read. Any post-marker exception writes a terminal receipt, consumes the attempt,
and authorizes no retry.

Before marker creation, require:

1. implementation and same-agent reviewer decision exact on origin;
2. a no-tensor checkpoint-tree/hash preflight;
3. exact runtime/package/source/scene/evaluator/renderer bindings;
4. a fresh renderer smoke using retained replayable trace schema and the exact
   future interpreter, without checkpoint or model access;
5. enough local disk and at least 30 minutes before the authority expiry;
6. a separately signed pre-run acceptance exact on origin.

Network, package installation, Brev/external compute, camera, serial, robot
hardware, physical motion, physical transfer, promotion, destructive
operations, and the freeze tag remain false.

## Decision rule

- **Pass:** only if the new rollout's unchanged
  `simulation_semantic_strict_success` is true and every strict-v2 predicate is
  independently reconstructed from the full trace. Preserve the pass as a
  learned-policy simulation Gate C result, then route to a separate kit-fold/F2
  decision. This does not grant physical transfer, hardware, promotion, or
  autonomous robot authority.
- **Fail:** preserve the exact failed predicates, margins, phase milestones,
  action/decode evidence, trace, and mirror as a terminal deterministic F0b
  negative. Do not retry, train, change thresholds, select another checkpoint,
  or automatically open F1/Brev.
- **Infrastructure failure after marker:** preserve terminal stage, exception,
  marker, partial-tree identity, and retry false. Do not relabel it as a policy
  negative or grant a replacement.

In every branch, report the original chunk-50 and receding-10 R2 results
unchanged. The one owner-authorized corrective ACT training rung remains
unselected and unconsumed unless a later, separate brief explicitly selects it.

## Deliverables and acceptance

- One frozen signed spec and deterministic implementation covering source
  binding, authority composition, preflight, marker-first execution, hybrid
  queue semantics, full trace, strict-v2 replay, mirror, terminal outcomes, and
  no-retry rules.
- Unit tests must reject schedule drift, a missing/extra reset, a 23/25-action
  discard, hidden phase/source actions, optimizer creation, source/checkpoint
  drift, output aliases, non-finite values, forged Gate C, result/trace
  coexistence with terminal failure, and authority escalation.
- Focused tests, relevant ACT/strict-v2/authority/renderer regressions, live
  model-free spec/preflight verification, JSON/lint/whitespace checks, and a
  fresh same-agent adversarial review.
- Implementation/reviewer, materialized authority, and pre-run acceptance are
  separate scoped commits. Each must be pushed and origin-confirmed before the
  next boundary. No checkpoint or model action may occur in this activation
  commit.
