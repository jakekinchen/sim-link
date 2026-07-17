# Session 317 - RGB Camera Census Terminal Failure

**Date:** 2026-07-16
**Support task:** K3 / Brief 228

Formal runtime `a7d61d0e...` proved the active thread at full access with
approval `never`. Central decision `7990e413...` granted one RGB-only permit
`6341a190...` against origin boundary `105bc4e...`, valid through 22:55:44 CDT.

The one-use session reached the first target, D405 UVC RGB. Named AVFoundation
returned a decoded PNG, but the existing helper rejected its dimensions as
different from the signed selected input mode. The source released and the
session stopped before C922 open. The private failure identity is `0093685a...`;
tracked terminal manifest `5c0edf59...` consumes the permit with zero accepted
frames and no proof labels.

The bounded offline audit found an evidence-contract gap: discovery/modes and
the actual decoded dimensions were not persisted before the frame validator
raised. The hardware-readiness note therefore records no stream configs or
latency and routes any future separately authorized replacement through a
discovery-first, requested-versus-decoded-dimensions diagnostic. Depth, serial,
register operations, torque, motion, audio, inference, training, and follower
commands remained zero; no ffmpeg capture process remained.
