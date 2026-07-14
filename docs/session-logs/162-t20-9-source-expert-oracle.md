# Executor Session 162 - T20.9 Source-Expert Oracle

T20.9 regenerated the immutable seed-2 T17.5b episode byte-identically and fed
all 244 recorded requested actions through the exact T20.7 policy callback,
scene, phase schedule, actuator limits, stepping, strict evaluator, keyframe,
and gate-margin path. A diagnostic observer compared the stored source,
regenerated source, and oracle execution frame by frame.

There is no execution divergence: actions, joint positions, joint velocities,
object positions, phases, and contact-geometry sequences match exactly in all
eleven phases. Projection and assistance are zero. The oracle reproduces 8/8
strict grasp-hold, 24/24 unassisted lift, 12/12 unsupported hold, 64/64 stable
recording hold, 24/24 lower, and a 36.3853 mm lift. Five 256 px keyframes show
the complete grasp/lift/retreat behavior.

The T20.7 evaluator nevertheless rejects the source trajectory solely because
`release_final_contact_clear` measures 0 versus 1. T17.5b declares the same
trajectory strict-success without that gate. At release-settle end, a
fixed-pad collision pair remains but has no force-bearing pad aggregate and no
non-pad contact; final retreat geometry is clear. The result therefore records
an adapter-valid source/acceptance contract mismatch, not policy capability.

The signed output verifies byte-identically with identity `cdb7d924...` and
file hash `bca4e548...`. Seventy-five relevant tests pass. No model was loaded,
no inference or optimizer ran, and no hardware, external compute, or Brev was
used.
