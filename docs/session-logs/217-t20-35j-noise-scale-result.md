# Session Log 217 - T20.35j Noise-Scale Result

## Evidence

- Result commit: `06b3a0af419ecd802fc949cc344a453c3a925410`.
- Attempt identity: `61eca0ab9eef8945d6b17ada065c5b7be05c14d2c2909c788bac236b131dc9c0`.
- Result identity: `e9bbff84864a838f64e67c72a4996fd4eefe13739294becc43a371268f3da75a`.
- Result file SHA-256: `e3c3948fb00cefcd9118445eb8bf6a6a1a402bda5c11c10db050f00f6497019c`.
- Python 3.12 signed verifier passes; 38 relevant tests and 6 subtests pass.

## Result

- Scale 1.0: worst `0.150321`, mean `0.030990`, spread `0.046392` rad.
- Scale 0.5: worst `0.084120`, mean `0.024630`, spread `0.018129` rad.
- Scale 0.0: worst `0.073360`, mean `0.024130`, spread `0.0` rad.
- Classification: initial-noise effect positive, Gate B failed.
- Route: model-free sampler/noise-distribution audit under Brief 177.

Reviewer 214 verifies the directional effect without accepting zero noise as a
policy sampler. Gate B and Gate C remain closed. No optimizer, training,
mutation, rollout, hardware, external compute, or Brev action occurred.
