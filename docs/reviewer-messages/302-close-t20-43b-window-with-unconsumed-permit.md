# Reviewer Decision 302 - Close T20.43b Window With Unconsumed Permit

**Date:** 2026-07-16

## Decision

`STOP_BEFORE_T20_43B_MARKER_INSUFFICIENT_HARD_CLOSE_BUDGET`

Pre-run acceptance commit `5f2abf3d188fb1e3109f7911e15e939a837606bd`
is exact on `origin/codex/pi05-autolearn-loop`. Acceptance `525de8dc...`,
permit `c7e8e1ca...`, and all seven authority artifacts reconstruct. The attempt
marker, run root, result, and terminal-failure receipt remain absent.

## Time-budget finding

At `2026-07-16T18:50:03-05:00`, 6,353 seconds remained before the fixed hard
close at `20:35:56`. The closest completed standardized campaign, T20.44, ran
from marker time `15:58:23` to signed run summary time `18:03:29`: 7,506
seconds for 5,000 updates and 10 rollouts. T20.43b requires 10,000 updates and
14 rollouts. ACT is a different, smaller policy, so the T20.44 duration is not
an ACT runtime prediction; it is decisive only that no measured evidence proves
the complete noninterruptible T20.43b attempt fits the remaining 6,353 seconds.

The marker is one-use, retry is forbidden, and the campaign has no authorized
pause/resume route. Consuming it without a safe completion budget would turn a
time-window interruption into the sole terminal result. Fail closed instead.

## Preserved proof state

- No marker, backbone tensor read, model construction/load/inference, optimizer,
  checkpoint, rollout, Gate C evaluation, or terminal result occurred.
- T20.43b remains `in_progress` and capability-unresolved; this is not a
  learned-policy negative and does not activate T20.45.
- Owner addendum `8b4a206` still describes one ACT replacement; because no
  marker exists, that replacement remains unconsumed.
- The current owner grant/permit remains immutable and expires at `20:35:56`.
  A future run therefore requires a fresh owner window and a separately reviewed
  administrative authority epoch that proves the old marker is absent. Such an
  epoch refresh is not a second replacement, but it is not granted here.

## Authority withheld

No marker or model action in this closing window; no stale-permit reuse after
expiry; no second replacement, retry, sweep, recipe/schedule/threshold change,
correction objective, T20.45 activation, hardware/camera/serial access, network,
external compute, Brev, transfer, promotion, or destructive operation.
