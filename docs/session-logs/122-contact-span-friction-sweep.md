# Session 122 - Contact Span And Friction Sweep

**Date:** 2026-07-13

Brief 092 derives a simulation-only metric contact span from MuJoCo contact
points at the fixed Brief 091 pose. Nineteen simultaneous fixed/moving-jaw
frames span 32.86691 mm at first closure and collapse to 4.907838 mm during the
hold. This is not a physical aperture calibration. More importantly, it shows
the two named jaw bodies contact one local region rather than opposing object
faces; the existing contact-count proxy is not sufficient force-closure proof.

A 12-setting training grid changed only the object/jaw sliding friction and
contact time constant. Object mass, geometry, pose, trajectory, close target,
seed, and lift threshold remained fixed. No setting retained any two-jaw
contact during the 12-frame lift hold or maintained 0.35 m clearance, so no
candidate was selected. The friction 4.0 / 0.01 s holdout was excluded from
selection until afterward and also failed, ending at z 0.322867 m.

Artifact `89c04062...` binds Brief 091 and the pinned model, the exact contact-
span profile, all training summaries, selection result, and holdout. Three
focused tests pass. No weld, assistance, hardware, physical motion, inference,
optimizer, training, Brev, paid compute, or network was used.
