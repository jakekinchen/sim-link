# Slice Brief 043 - Disconnect Proof, Alias Holder, And Torque Evidence

**Date:** 2026-07-11

## Objective

Close the owner-review P0 state-transition gaps before any new T16.5b live
access. Produce an independently verified, machine-readable disconnect proof;
make the one-call permit mechanically consumed; check every signed path for the
follower serial identity; and add per-servo `Torque_Enable` to the no-write
census. Implement and test offline. Keep `live_gate` closed throughout.

## Canonical state contract

- Remove self-staling `current_head_commit` and `last_reviewed_commit` fields.
  Use `verified_through_commit` and `last_reviewed_implementation_commit`; derive
  actual branch HEAD from Git at runtime.
- The disconnect plan records `maximum_call_count=1`, `observed_call_count=1`,
  `permit_consumed=true`, and `additional_calls_allowed=0`.
- Canonical state, generated status prose, proof artifacts, verifier outcome,
  reviewer decision, Git history, and remote branch must agree before a separate
  live-gate transition.

## Virtual disconnect proof

- Define `scenesmith.virtual_follower_disconnect_proof.v1` plus a private raw
  evidence schema. Bind authority/permit identity, exact POST method/path/body,
  one observed call, timestamps, response status/body hash, pre/post hardware,
  safety/routing/jobs, all-path holder evidence, forbidden effects, zero motion
  commands, and consumed-permit state.
- Preserve exact raw reconstructed observations only under ignored private
  output, explicitly labeled as reconstructed from the executor operation
  transcript and canonical hashes rather than a contemporaneous capture file.
- Track a redacted content-addressed proof that includes private file hash/size/
  identity references but no raw USB serial, device paths, or private payloads.
- Independently reject wrong method/path/body/role, call count other than one,
  unconsumed or reusable permit, non-200/disconnected response, leader loss,
  safety/routing mutation, any running job, any holder, any forbidden effect,
  motion-commanded state, missing raw references, tampering, alias gaps, or
  evidence substitution.

## All-alias serial ownership

- Replace canonical-path-only checks with
  `enumerate_serial_identity_holders(canonical_path, observed_aliases)`.
- The signed follower identity must include the paired `/dev/tty.*` alias. Run
  lsof separately over canonical and every signed alias, retain per-path
  records/counts, and deduplicate by PID/file descriptor/type while retaining
  all paths.
- Reject missing/extra/duplicate/unsafe paths, malformed lsof output, command
  errors, an alias appearing/disappearing across pre/post discovery, any holder
  on any path, or contradictory per-path/deduplicated counts.

## Per-servo torque evidence

- Add source-bound `Torque_Enable` to the allowlisted scalar census for all six
  servos, with exact width/semantics from the pinned Feetech runtime.
- Record the raw per-servo value and require the observed disconnected proof to
  report torque disabled for all six before any later motion permit. Do not
  infer disabled state from Studio aggregate status alone.
- Update exact operation counts, trace/result schema version where required,
  recorded fixtures, malformed/missing/wrong-value tests, and source binding.
- Do not add any write, handshake, scan, torque transition, or motion method.

## Validation

- Adversarial disconnect-proof matrix including every rejection above.
- Holder tests: canonical free/TTY held; same process on both paths; different
  processes per path; alias set drift between pre/post; malformed and failed
  lsof; exact zero-holder success.
- Census tests: six `Torque_Enable=0` values; missing register; one enabled
  servo; wrong width/type; retry/cleanup paths; exact operation counts; zero
  register/configuration/torque writes; `physical_follower_commanded=false`.
- Existing camera diagnostics, live observation, authority, qualification,
  inertial, twin, dependency, LeRobot, static forbidden-call, `py_compile`,
  offline verifier, formatter, and broad regression gates.
- Fresh same-agent adversarial review, explicit-path commits, push only to the
  named branch, and remote confirmation. Live-gate reopening is a separate
  reviewed commit after all artifacts agree.

## Authority

Offline implementation and OS metadata/holder inspection only. No serial or
camera open, Studio POST, process signal, reconnect, register write, torque
change, motion, live proof label, policy actuation, physical qualification,
training, transfer, promotion, or global authority. `training_lock` remains
closed.
