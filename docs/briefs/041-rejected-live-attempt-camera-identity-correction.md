# Slice Brief 041 - Rejected Live Attempt Camera Identity Correction

**Date:** 2026-07-11

## Objective

Contain rejected T16.5b attempt 001 and replace ephemeral AVFoundation numeric
camera indexes with a stable name/unique-ID-bound finite capture path. Perform
all implementation, fake capture, parsing, cleanup, evidence, and privacy work
offline. Do not reopen a serial port or camera in this slice.

## Trigger and containment

- Contract `2102227cedc18e0b21152863424817781eff9bba139c986c8496e898bf2c22e9`
  reached post-close discovery, where the same two camera names were associated
  with swapped numeric indexes.
- The system-camera record set and AVFoundation camera-name set were unchanged;
  only order and index association churned. Numeric index identity is therefore
  invalid as an authority field.
- No private evidence bundle or tracked manifest was written and no live proof
  label survived.
- A pre-existing `studio_server` process started on 2026-07-08 still holds the
  follower serial device. Preserve it untouched. Do not infer exclusive bus
  ownership or perform another live open until the owner explicitly resolves
  that independent holder.

## Stable camera contract

- Bind each selected camera to one exact AVFoundation name and one exact
  `system_profiler` unique ID/model identity. Reject duplicate names, missing or
  multiple system matches, duplicate unique IDs, or changed stable name/unique-
  ID sets.
- Treat numeric discovery indexes as ephemeral observation metadata only. They
  may select a camera during the initial private planning step but must not be
  used by the production capture backend or post-close stability decision.
- Open the camera by its exact unique name through a reviewed finite ffmpeg
  AVFoundation subprocess. Do not use OpenCV index capture.

## Finite subprocess and frame contract

- Request exactly the contract frame count, output PNG bytes only, and parse
  exactly that many complete PNG files from the pipe. Reject truncation, extra
  frames, invalid signatures/chunks, dimensions, nonzero exit, stderr failure,
  timeout, or any trailing unparsed bytes.
- Apply finite startup/read/total watchdogs. On success, failure, timeout,
  cancellation, or parser error, close pipes and terminate/wait/kill only the
  capture subprocess as required; preserve primary and cleanup failures.
- Record construct/start/read/release/terminate/wait counts. Continuous
  recording remains zero. No capture-property setter is permitted.

## Discovery stability

- Serial candidates must remain exact.
- Stable AVFoundation camera-name and system-camera identity sets must remain
  exact and duplicate-free, independent of list order or numeric index churn.
- The selected name-to-system-identity mapping must remain exact before and
  after capture. Any stable identity drift still fails closed.

## Evidence and privacy

- Retain exact private camera names/unique IDs and frame bytes only in ignored
  local-private evidence.
- Keep tracked output limited to hashes, operation counts, timestamps,
  dimensions, content addresses, and permitted proof labels.
- Attempt 001 remains rejected history and must never be relabeled from a later
  correction or replay.

## Validation

- Deterministic fake ffmpeg process/pipe tests for exact two-frame success,
  swapped discovery indexes, duplicate names, truncation, extra PNG, timeout,
  nonzero exit, primary plus cleanup failure, and content/hash drift.
- Existing live harness, T16.5a census, authority, qualification, twin,
  dependency-lock, LeRobot, static forbidden-call, formatter, `py_compile`, and
  `git diff --check` gates.
- Fresh same-agent review, scoped commits, push only to the named branch, and
  remote confirmation before any live reconsideration.

## Authority

This brief is offline-only. It grants no serial/camera open, stop/termination of
the pre-existing Studio server, write, torque change, motion, live proof label,
physical qualification, policy actuation, training, transfer, promotion, or
global authority. `training_lock` remains closed.
