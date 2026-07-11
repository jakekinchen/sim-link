# Session 087 - Brief 057 PI0.5 Reviewed-Input Issuance Gate

**Date:** 2026-07-11

Brief 057 began offline at `2026-07-11T16:18:18-05:00` from remotely matched
HEAD `cae8184a3f456480c4e0f70e0fb8d73b72d7cc0f`; start boundary
`f0e346f009df60451ccd2c625844ecce72cc8b39` recorded the exact scope.
Implementation `44dd871745efcc3490321a3ada92b4ddf138ba6c` is present on
`origin/codex/pi05-autolearn-loop`. The live gate and training lock remained
closed.

The gate first runs the complete Brief 056 verifier against the pinned local
source, checkpoint-processor, tokenizer, calibration, and coordinate evidence.
It then validates any supplied review inputs from exact non-aliased robot-lab
configuration paths. Every input has an exact schema and field set, fixed local
scope, allowlisted issuer, reviewer decision ID, source-contract and session
identity, signed semantic-subject hash, tracked reviewer-record hash and marker
block, issuance time, and at-most-24-hour validity interval.

A future acceptance must reference the exact signed Brief 055 manifest and its
candidate-pending-review classification. A future role binding must reference
that same manifest, cover exactly the two stable camera identities, and map
top to the base model key and wrist to the left-wrist model key. It rejects raw
camera identity inclusion, numeric indexes, duplicate roles or identities, and
missing private-review evidence hashes. A future task must already match the
executable cleaner: nonblank, bounded UTF-8, NFC, trimmed, single-line,
underscore-free, control-free, and single-spaced, with exact task/template/
prefix hashes.

The composer validates present partial inputs but cannot promote them. A full
fixture bundle produces only `fixture_inputs_conformant`; a mixed bundle is
rejected. A full production-class bundle can produce only the local reviewed-
bundle capability and still records no accepted policy input or execution. The
checked artifact supplies no input paths and no evaluation time, so it is
deterministically `blocked_missing_reviewed_inputs` with three absent slots.

Same-agent adversarial review added exact field sets, dynamic fixture versus
production evidence modes and scopes, stable rereads around input, manifest,
and review-record evidence, NFC task enforcement, and explicit rejection of
extra authority fields. Tests cover source, issuer, subject, scope, session,
time, evidence-class, manifest, camera, task, record, path, partial-bundle, and
re-signed gate substitutions.

One hundred twenty-three focused tests pass in both `.mujoco_venv` and the
pinned LeLab runtime. The Brief 056 source writer and Brief 057 gate writer both
verify in both runtimes. Compilation, whitespace, privacy, path-safety, and diff
checks pass. The 322-test offline authority/twin gate passes in 69.292 seconds.

No real live-session acceptance, stable-camera role binding, or task prompt was
created. No tokenizer, processor, model, policy input, or model weight was
loaded or constructed. No hardware was enumerated, instantiated, or opened; no
serial, camera, Studio, reconnect, register write, torque change, motion,
preprocessing, inference, policy shadow, MuJoCo replay, optimizer, training,
paid compute, destructive action, or unrelated dirty path was touched. Grant
only `pi05_reviewed_input_issuance_gate_conformant`.
