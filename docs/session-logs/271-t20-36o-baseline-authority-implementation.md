# Session Log 271 - T20.36o Baseline Authority Implementation

## Evidence

- Source design: corrected `8294c63b...`, remotely preserved at `e6eede1`;
  minimum-envelope artifact `b44bd55b...` is superseded and cannot authorize
  materialization.
- Implemented central owner/request/decision composition, live preflight,
  finite one-use permit, pre-tensor marker, and deterministic materializer.
- Probe cardinality: five starts, five seeds, two repeats, 50 decoded chunks,
  500 denoise-step records.
- Verification: seven authority/permit tests, six bridge-design tests, twelve
  pointer tests, compile check, and diff check pass.
- All baseline owner/request/decision/preflight/permit, attempt, tensor,
  trajectory, result, and failure-result paths are absent.

## Result

Reviewer 268 verifies implementation only. After this boundary is on origin,
the materializer may hash exact checkpoint/base bytes and write the central
authority, preflight, and one-use permit. No model or optimizer action is part
of materialization; a separate pre-run review remains mandatory.
