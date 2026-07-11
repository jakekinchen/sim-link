# SO-Frame Adoption Decision

**Date:** 2026-07-11

**Decision:** Adopt the disclosed reward-hacking failure as an adversarial
evaluation requirement. Do not import the repository, model, checkpoint, RL
runtime, or physical frame into the active workflow.

## Source pin

- Repository: <https://github.com/livekit-examples/so-frame>
- Inspected commit:
  [`aa5d6da0834de7a08a971caf1540f825c3ea0349`](https://github.com/livekit-examples/so-frame/tree/aa5d6da0834de7a08a971caf1540f825c3ea0349)
- Relevant disclosure:
  [`README.md` lines 122-134](https://github.com/livekit-examples/so-frame/blob/aa5d6da0834de7a08a971caf1540f825c3ea0349/README.md#L122-L134)
- Relevant evaluation semantics:
  [`rl/README.md` lines 147-185](https://github.com/livekit-examples/so-frame/blob/aa5d6da0834de7a08a971caf1540f825c3ea0349/rl/README.md#L147-L185)
- Relevant actuator caveat:
  [`so101_constants.py` lines 84-113](https://github.com/livekit-examples/so-frame/blob/aa5d6da0834de7a08a971caf1540f825c3ea0349/rl/src/soframe_rl/so101_constants.py#L84-L113)

At the inspected commit, the tracked repository tree contains no top-level
`LICENSE` or `COPYING` file. Public visibility and the README's use of the word
"open" do not grant a copying license. No code or asset may be vendored unless a
compatible explicit license and all upstream asset licenses are recorded.

## Component disposition

| Component | Disposition | Reason |
|---|---|---|
| Golf-putt reward-hacking case | Adopt as an adversarial evaluation requirement | It proves that terminal object placement alone is not strict pick-and-place competence. |
| PPO checkpoint | Reject | It is a disclosed reward-hacking policy with a different observation and action contract. |
| MjLab / MuJoCo-Warp runtime | Reject for the active stack | It would introduce a second CUDA-oriented training runtime while the pinned LeRobot identity and training lock remain authoritative. |
| URDF, MJCF, USD, and STS3215 files | Comparison-only after licensing | The frame has a seventh slider axis, different cameras and extrinsics, and unqualified actuator choices; it is not the current six-joint physical twin. |
| BOM, CAD, and LeSlider frame | Defer to a separately authorized hardware-v2 decision | Building it would change the physical robot, workspace, cameras, calibration, and qualification evidence rather than extend the current rig in place. |
| LiveKit transport | No adoption from this repository | The inspected repository provides a frame, simulation, and RL example, not a transport integration for the current policy loop. |

## Semantic task-success invariant

The M20 proof contract must expose terminal outcome and strict task success as
different fields. A cube entering the correct target may set an outcome fact such
as `terminal_target_outcome=true`; it must not by itself set
`strict_pick_place_success=true`.

The exact numeric thresholds are pinned by T20.1, but the contract must require
all of the following before strict success can be granted:

1. A complete, monotonically ordered trace bound to the task, object, target,
   structural twin, evaluator, and seed identities.
2. An ordered semantic witness for approach, contact, grasp, lift, transport,
   release, stable placement, and retreat. Later-stage evidence cannot repair a
   missing earlier stage.
3. A source-bound grasp witness and an object lift that clears the work surface
   and target rim before the scored lateral transport.
4. Bounded object-to-gripper displacement during transport, followed by release
   inside the target and a stable post-release dwell.
5. Source-bound joint, end-effector, object-speed, and contact/impact bounds that
   reject ballistic, high-impulse, or otherwise unsafe target entry.
6. No teleport, scripted object motion, contact-gated weld, controller assistance,
   or privileged action source in a strict pure-policy result.
7. Evaluator-only simulator state may compute labels but may never enter deployed
   actor observations, training actor inputs, or policy actions.

Missing, stale, contradictory, or incomplete evidence fails closed. A rollout
that pushes, slides, putts, throws, or otherwise knocks the cube into the target
may retain the terminal outcome fact, but its strict-success field remains false
and its failure reason must identify the violated semantic or dynamics gate.

## Required M20 adversarial cases

T20.6 must include deterministic negative traces in which the cube reaches the
correct target through each of these mechanisms:

- putt or high-impulse strike without grasp;
- planar push or slide without lift;
- ballistic throw after only momentary contact;
- target occupancy credited as success without a verified in-target release and
  stable post-release dwell;
- teleport, scripted object motion, or contact-gated weld;
- valid semantic phases produced by controller assistance but relabeled as pure
  policy;
- final placement with a missing, reordered, stale, or contradictory stage
  witness;
- strict-looking evaluator evidence leaked into actor inputs.

Every case must preserve any truthful terminal outcome while rejecting strict
success. A positive fixture must pass the same evaluator with the complete ordered
witness and all bounds satisfied.

## Authority and timing

This decision changes only future M20 acceptance criteria. It does not change the
active T16.5c task, open the training or live-hardware gates, authorize MuJoCo or
policy execution in the current slice, grant physical-transfer authority, or add
the external repository to the dependency lock.

When T20.1 becomes dependency-ready, its immutable proof contract must convert
this invariant into a signed machine-readable schema. T20.6 then implements the
evaluator and adversarial fixtures before T20.7 model comparison or T20.8 policy
acceptance.
