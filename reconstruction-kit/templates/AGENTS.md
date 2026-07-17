# SO-101 Fork Operating Rules

- Treat `docs/reconstruction/CURRENT_STATE.json` as inherited, immutable
  history. Copied grants, permits, markers, and reviewer artifacts are never
  live authority in this repository.
- Preserve fixture, synthetic, simulation, replay, learned-policy, physical
  read-only, and physical task evidence as separate proof classes.
- Use `external/lerobot/.venv/bin/python` as the sole interpreter. Keep rollout
  and rendering in-process; do not recreate the source repo's subprocess
  runtime dispatch.
- Freeze held-out scenes and seeds before training. Evaluation code and frozen
  verdict fixtures are owned separately from training code.
- State-RL uses joint state plus simulator object pose, light parquet, and
  60-frame success-terminated episodes. Cameras and audiovisual datasets are
  VLA/demo-tier inputs only.
- ACT and state-based RL are the primary tracks until an end-to-end demo works.
  SmolVLA and PI0.5 are stretch work.
- Training may be accelerator-nondeterministic. Run selection evaluation on
  CPU/fp32 and require bit-identical verdicts across supported hosts.
- Every run emits `RUN_RECEIPT.json` with commit, config hash, dataset identity,
  seed, wall clock, and metrics, plus replayable signed claim artifacts.
- Keep one frozen workcell XML. Add tasks through registry data, never by
  casually editing the base XML.
- The reviewed gateway is the only future robot path for teleop, tests, and
  demos. Never infer hardware access from a receipt or shell permission.
- Keep generated datasets, checkpoints, credentials, caches, private
  observations, `outputs/`, and human-named `runs/` out of Git. Do not create a
  task alphabet.
