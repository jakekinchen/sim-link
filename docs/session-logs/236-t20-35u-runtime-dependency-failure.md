# Session Log 236 - T20.35u Runtime Dependency Failure

## Evidence

- Attempt identity: `179092b97c91b37d69d4578f9f1c81a0a5f73c309c7e684df0454d6ce709ef81`.
- Attempt file SHA-256: `513ae085f4cfcdfb43d8cb135219a66a47037d2b22c50af51885deffaae94843`.
- Attempt size: 830 bytes.
- Signed failure identity: `0abd9650caa36206e6b2b8a1dc4c89d773107ada1c062677520089beadc0d208`.
- Failure file SHA-256: `50c35635cc39cce6c0a8678917cb7097b9ebed0a0feba64543273656f3a2adc7`.
- Failure size: 1,694 bytes; artifact commit `5700fb0`.

## Result

The one permitted attempt failed before checkpoint access or model construction
because the Python 3.12 runtime lacked LeRobot's `datasets` dependency. No
trajectory result was emitted and the checkpoint tree remains exact. Reviewer
233 forbids retry and routes distinct T20.35v behind a full runtime preflight.
Gate B and Gate C remain closed.

No optimizer, rollout, hardware, external compute, or Brev action occurred.
