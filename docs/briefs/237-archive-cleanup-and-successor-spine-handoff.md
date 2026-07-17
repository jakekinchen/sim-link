# Brief 237 — Archive Cleanup Reconciliation and Successor Spine Handoff

## Objective

Close the final archival contradiction without reopening project work:

1. verify whether the recorded tier-1 and tier-2 output cleanup is still
   pending;
2. preserve every explicitly protected source, proof, and receipt path;
3. amend the closure note and living state to the verified filesystem truth;
4. leave the source branch unmerged and direct all future work to `sim2claw`;
5. give the successor a portable, authority-safe spine export contract.

## Frozen boundaries

- Source branch: `codex/pi05-autolearn-loop` at owner-instruction baseline
  `4674e2bd630edd5ad4ee1696f924d88ccb6a17cc`.
- Tier 1 and tier 2 mean only the paths recorded in
  `docs/autonomous-workflow/sim-link-closure-2026-07-17.md` under the actual
  `outputs/robot_lab/` root.
- Tier 3 `t20_35x_physical_gate_joint_weighted_run_001` is retained.
- The R0 generator, R2/F0c source checkpoint, append-only raw store, SmolVLA
  mirrors and rollouts, `weights/`, tracked receipts, F1 in-repo archive, and
  external F1 selected artifact are retained.
- Existing `.codex/config.toml`, `external/`, `tmp/`, and Claude worktree dirt
  is unrelated and must not be staged or modified.

## Implementation

- Reconcile the closure note against current disk inventory and the earlier
  signed cleanup evidence. If tier 1 and tier 2 are already absent, do not
  reinterpret the owner's instruction as permission to delete different
  surviving paths.
- Record the exact reclaimed amount and current preservation audit.
- Mark the cleanup decision resolved and the source repository archived in
  `project_state.json`, without importing successor authority.
- Add a small closeout session log and same-agent reviewer decision.
- In `sim2claw`, create a canonical spine manifest/export helper that copies
  living doctrine without copying historical permits or live authority.

## Verification

- Exact target presence/absence and `du` inventory.
- `git ls-files` check for the retained `autolearn` receipt.
- Preserved-asset existence and external F1 artifact check.
- Strict JSON parse, Markdown relative-link audit, shell syntax check, export
  rehearsal into an empty scratch directory, and `git diff --check`.
- Branch, HEAD, upstream, explicit dirty paths, scoped commit, push, and remote
  equality for each repository.

## Authority not granted

No training, model action, retry, hardware, camera, serial, motion, external
compute, Brev provisioning, promotion, merge, rebase, branch deletion, or
deletion outside the already authorized tier-1/tier-2 cleanup set.
