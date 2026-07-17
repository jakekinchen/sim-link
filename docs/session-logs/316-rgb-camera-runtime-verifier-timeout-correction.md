# Session 316 - RGB Camera Runtime Verifier Timeout Correction

**Date:** 2026-07-16
**Support task:** K3 / Brief 228

The first K3 preflight failed before artifact creation or hardware access because
the exact `codex doctor` command took 33.51 seconds while the formal runtime
verifier allowed only 30 seconds. Direct execution returned the expected JSON
report and the verifier already accepts doctor exit codes 0 or 1.

Raised only the bounded doctor subprocess timeout from 30 to 60 seconds, added a
regression assertion for that value, and bound the hardware-profile source and
test into K3's origin-clean source set. Both pinned robot runtimes pass the 25
hardware-profile-plus-camera tests. No authority semantic, camera scope, depth,
serial, motion, or evidence rule changed; no hardware was enumerated or opened.
