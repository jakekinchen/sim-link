# Session Log 243 - T20.36 Gate B Regression

## Evidence

- Result commit: `3e1f2bd`.
- Attempt identity: `6513bfd2f6012567c5ca4df98a8d58fd16c5421f07a4a41add89d688ff257d2a`.
- Run identity: `88daae0d8239239d064227b9e9561a01b7bf634d849dc4e61237b1713462410e`.
- Run file SHA-256: `19010302db1e7f41cc6a089914fa7260030eaa57498bea76737a03fb9862e830`.
- Run size: 89,258 bytes.
- Checkpoint identity: `c5e36cca9b61379a24dd72bcb89aa582ab3b2de70a48bb64202a4484f0ac8488`.
- Checkpoint model SHA-256: `acba5798ddf5b3562196e3f38ab15b28e9b72c0c09576548436ba7f25f5d23b0`.
- Checkpoint model size: 2,773,721,000 bytes.
- Result identity: `02b543be829220f89e0bfe2d16b042507127f488f73a9de0149442e89bc3a638`.
- Result file SHA-256: `7927aaafa7d7a403487ac228b8cfe7e058b3414ac0a2a6a56993d77b17ba8ee8`.
- Result size: 1,191 bytes.

## Result

The one-use attempt completed all 500 updates. The standard-objective ratio
passes at `0.0305642`, but every decoded chunk fails 0.05 rad; the observed
maximum-error range is `0.150601` to `0.187035` rad. The weighted correction
objective improves while the raw correction objective worsens. Gate B is not
retained, so the runner reaches no rollout seed or mirror. Exact result
verification passes. Reviewer 240 verifies the negative boundary and opens
only the optimizer-free T20.36a audit. No hardware, external compute, or Brev
action occurred.
