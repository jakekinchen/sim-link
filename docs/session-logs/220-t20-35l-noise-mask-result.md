# Session Log 220 - T20.35l Noise-Mask Result

## Evidence

- Result commit: `1040478f19deb134fee5c6e8a0c9d84aedddbe60`.
- Attempt identity: `adf33ca1c56e84a78c69a07d94c4dd7b476f30a74b7e9dc88541b002827c71ed`.
- Result identity: `b4fc6060c56431ab2bf52dd74d8efa58b1808a10a827521db076f9d10234dbea`.
- File SHA-256: `7d5436fdd003ca86f750c3a96882a4c996455ea3948452f89640aa75b82f481f`.
- Python 3.12 signed verifier and focused tests pass.

## Result

- All normal worst error: `0.150321` rad.
- Active normal / padded zero: `0.114173` rad.
- Active zero / padded normal: `0.066398` rad.
- All zero: `0.073360` rad.
- Classification: joint active and padded noise sensitivity; Gate B failed.

Reviewer 217 routes the model-free T20.35m factorial interaction audit. No
optimizer, training, mutation, rollout, Gate C, hardware, external compute, or
Brev action occurred.
