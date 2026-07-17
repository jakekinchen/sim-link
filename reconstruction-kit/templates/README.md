# SO-101 Simulation Learning Lab

This repository was seeded from the SceneSmith reconstruction capsule pinned to
portable source commit `605e4d3624a87593a1b5da9a97cd263f6bade78a` and
evidence snapshot `6c53d9309f7f41f0d3ac351c049436ddda20e50f`.

Current inherited evidence proves the simulation/data/evaluation substrate and
records a SmolVLA terminal negative. It does **not** include a successful learned
policy, physical qualification, model weights, datasets, external checkouts, or
runtime authority.

Start here:

1. `RECONSTRUCTION_RECEIPT.json`
2. `docs/reconstruction/CURRENT_STATE.md`
3. `docs/reconstruction/ARCHITECTURE.md`
4. `docs/reconstruction/QUICKSTART.md`
5. `docs/reconstruction/FORWARD_PLAN.md`

Verify the pristine exported bytes before adding dependencies or initializing
new generated state:

```bash
python3 tools/reconstruction_kit.py verify-export .
```

This check is intentionally strict: any later unreceipted file, including a
runtime cache, makes it fail. Keep the original receipt as the immutable import
record; use the new repository's own Git/evidence process for subsequent work.

The next capability task is the still-unconsumed fixed ACT replacement, but it
must receive a fresh local authority epoch and a complete uninterrupted run
window. Never reuse the copied historical owner grants or permits.
