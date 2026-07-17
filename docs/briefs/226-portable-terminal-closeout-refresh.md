# Slice Brief 226 - Portable Terminal Closeout Refresh

**Date:** 2026-07-16
**Support task:** K2
**Policy boundary preserved:** T20.43b verified terminal runtime failure

## Objective

Refresh the portable reconstruction capsule to the verified T20.43b closeout
and harden the diagnostic mirror so a new repository does not repeat the
known unsupported-T20.43b-schema integration failure. This is support tooling
and documentation only; the consumed policy attempt remains immutable.

## Ground-truth inputs

- Closeout commit `4d8f951fc5e0f16d3f47dc44965e3221fe0c3778` is exact on
  `origin/codex/pi05-autolearn-loop`.
- Attempt marker `d67cf38e...` and terminal receipt `89b6dbff...` prove one
  checkpoint-0 rollout, zero optimizer updates, no Gate C pass, and no retry.
- Reviewer 306 localizes the failure to missing dispatch for schema
  `scenesmith.t20_43b_r1_act_closed_loop_trace.v1`; the retained T20.43 smoke
  could not exercise that distinct schema.

## Allowed work

- Add T20.43b trace verification/dispatch to the existing model-free mirror
  renderer and a deterministic regression test.
- Exercise the retained signed trace only through temporary diagnostic output;
  never write into the immutable T20.43b run tree.
- Re-pin the portable implementation manifest to the reviewed renderer-fix
  commit and refresh current-state, lessons, quickstart, forward-plan, and
  export receipts.
- Run model-free focused, manifest, clean-export, and documentation checks.

## Authority withheld

No policy retry, continuation, second replacement, marker rewrite, model or
checkpoint loading, model inference, optimizer action, policy rollout, Gate C
execution, recipe/gate/data change, T20.45 activation, hardware/camera/serial
access, physical motion, network/package installation, external compute,
Brev, transfer, promotion, authority transfer, bulk/private copying, or
destructive operation is authorized.

## Acceptance criteria

- The original retained trace reproduces the unsupported-schema error before
  the fix and a temporary one-frame MP4 plus signed manifest after the fix.
- Focused renderer/runner tests and the terminal verifier pass without model
  construction or optimizer action.
- The capsule reports ACT as a verified terminal infrastructure failure with
  capability unresolved, never as unconsumed or as a trained negative.
- The regenerated manifest and clean export are content-addressed, remotely
  preserved, and continue to carry no live authority.
