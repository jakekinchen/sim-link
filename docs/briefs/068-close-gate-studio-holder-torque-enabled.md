# Slice Brief 068 - Close Gate On Studio Holder And Torque Enabled

**Date:** 2026-07-12

## Objective

Preserve the owner-present preflight failure and close Reviewer 093's gate
before any candidate session or device open.

## Observed failure

- Fresh discovery resolved the exact follower and both signed aliases.
- The all-alias holder gate found one independent holder; snapshot identity
  `b86802c166f94845a39d5cbe04480126061373cb87b00c29199338ca64b519ef`.
- The holder is the separate SO-101 Studio server.
- A read-only Studio status request reports follower connected and torque true.
- The preflight stopped before lease construction, candidate issuance, private
  artifact, serial/camera open, servo read, or session start.

Close at `2026-07-12T17:51:13-05:00` with sessions-started zero. The consumed
disconnect permit is not reused. A future gate requires the follower released
from Studio, torque observed off, zero holders across both aliases, fresh owner
presence/lease, and fresh discovery.
