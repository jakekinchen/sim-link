# SO-101 Simulation Learning Lab

This repository was seeded from the source commit and exact file manifest in
`docs/reconstruction/SOURCE_MANIFEST.json`.

Current inherited evidence proves the simulation/data/evaluation substrate and
records terminal negatives for both SmolVLA and the full T20.43c-R2 ACT
campaign. It does **not** include a successful learned policy, physical
qualification, model weights, full R0 output, external checkouts, or runtime
authority. It does include the signed minimal 10-episode/2,330-frame R0 base
and three simulation-only trace fixtures.

Start here:

1. `RECONSTRUCTION_RECEIPT.json`
2. `docs/reconstruction/CURRENT_STATE.md`
3. `docs/reconstruction/ARCHITECTURE.md`
4. `docs/reconstruction/QUICKSTART.md`
5. `docs/reconstruction/FORWARD_PLAN.md`
6. `docs/reconstruction/HARDWARE_READINESS_RGB_CAMERAS.md`

Verify the pristine exported bytes before adding dependencies or initializing
new generated state:

```bash
python3 tools/reconstruction_kit.py verify-export .
python3 tools/bootstrap.py \
  --local-source-root /absolute/path/to/sim-link \
  --offline
```

This check is intentionally strict: any later unreceipted file, including a
runtime cache, makes it fail. Keep the original receipt as the immutable import
record; use the new repository's own Git/evidence process for subsequent work.

The bootstrap proves the transplanted source stack and emits a signed receipt;
it grants no training or hardware authority. Original T20.43c is retained as
exact ACT zero-update equivalence followed by an inconclusive owner-directive
interruption at update 728. T20.43c-R2 is retained separately as the later full
10,000-update terminal negative. Every source-repo marker and permit is
consumed and inert here.

After bootstrap, `external/lerobot/.venv/bin/python tools/regenerate_r0.py run`
recreates the legacy R0 compatibility dataset and `verify` checks it
independently. The source reference receipts are W1 `392fcc8b...` and W2
`86739578...`; neither receipt is live authority or learned-policy proof.

Fork defaults:

- one pinned LeRobot venv and in-process rendering;
- ACT plus state-based RL as the two primary tracks;
- camera-free joint-state/object-pose RL with light parquet and 60-frame
  success-terminated tasks;
- audiovisual LeRobotDataset only for VLA/demo work;
- accelerator-nondeterministic training but CPU/fp32 bit-identical evaluation;
- one frozen workcell XML plus a data-only task registry;
- one robot gateway for all future teleop/tests/demo traffic;
- outputs ignored from commit one, human run names, and one auto-emitted
  `RUN_RECEIPT.json` per run.

Never simplify away the frozen held-out set, replayable signed claims, or
evaluation ownership separate from training. Copied permits and reviewer
artifacts are history, not live authority.
