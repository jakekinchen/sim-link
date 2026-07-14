# Executor Session 163 - T20.10 Release Semantics

T20.10 reconciled the policy rollout release gate with T20.6's active
fingertip-contact semantics while preserving the independent final-retreat
geometry requirement. A named legacy geometry-pair mode keeps historical
T20.7 and T20.9 outputs reproducible. A new force-bearing mode requires no
positive pad aggregate and no non-pad contact at release-settle end, then still
requires complete geometric contact-pair clearance at retreat end.

The corrected seed-2 source oracle remains exactly aligned across all 244
actions, robot states, velocities, object positions, phases, and contact
sequences. It records five 256 px keyframes, zero projection and assistance,
36.3853 mm lift, release active-contact clear 1/1, retreat geometry clear 1/1,
and no failed gates. Release-settle geometric overlap remains explicitly false
rather than being discarded.

The legacy T20.9 artifact verifies byte-identically, and the new T20.10 output
verifies deterministically with identity `dad3133a...` and file hash
`25af7721...`. Seventy-nine relevant tests pass. No model was loaded, no
inference or optimizer ran, and no hardware, external compute, or Brev was
used. The result is an evaluator baseline, not learned-policy acceptance.
