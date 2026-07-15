# Reviewer Decision 202 - Authorize One T20.35c Expert-Only Run

**Decision:** `CONTINUE_ONE_T20_35C_EXPERT_ONLY_RUN`

## Reviewed Boundary

Brief 169, implementation `82614ec`, corrected audit `446a0686...`, signed
specification, owner-scope grant, central composition, runner, tests, canonical
state, and complete scoped diff were reviewed together after remote
preservation.

## Adversarial Findings

- The T20.35c specification is mechanically derived from the frozen T20.33
  artifact. Source batch, processors, base revision, task, constant `2.5e-5`
  learning rate, 500 updates, training seed, five inference seeds, and both
  gates remain unchanged.
- The only model adaptation change is from rank-4 LoRA to no PEFT with
  `train_expert_only=true`: all PaliGemma parameters must be frozen and the
  complete Gemma expert plus action in/out and real `time_mlp_in/out`
  projections must be trainable.
- Runtime checks reject PEFT/LoRA parameters, any trainable PaliGemma weight,
  missing required prefixes, extra trainable parameters, non-float32 trainable
  tensors, and name/shape/dtype/element-count drift.
- The decision grants only `simulation_training_ready` through the current
  hard closeout. It grants no retry, continuation, learning-rate or update
  change, second batch, Gate C work, campaign, hardware, external compute,
  Brev, transfer, or promotion.
- The signed immutable attempt marker is written before model construction;
  any model-load, optimizer, memory, training, inference, or checkpoint failure
  consumes the one-run permit and cannot silently retry.
- Every objective and gradient must be finite. The trainable-only safetensors
  checkpoint, exact tensor manifest, five decoded chunks, authority identity,
  source/dataset hashes, and forbidden result fields fail closed on drift.
- Existing user-owned config changes and external checkouts are excluded.

## Disposition

After this decision is committed, pushed, and confirmed on
`origin/codex/pi05-autolearn-loop`, execute exactly one local-MPS expert-only
run. Then compose and verify one signed Gate B result. Do not retry or continue
regardless of outcome. Route a pass to the separately reviewed T20.36 campaign
and a failure to the optimizer-free objective-floor attainability audit.
