# Session Log 274 - T20.36o Baseline Capture Result

## Execution

- Source commit: `a40573a7821fe3cb1e6e41b4c90e05120f8c502f`.
- Attempt: `f89d3c040c5dbd4d1fe21c6b793618a225038a67eb7b571c4a9e6e1973c8f67d`.
- Tensor artifact: `40bf3b018c388cc6b755e566fdd66ee09895346597171daca4b26d764330fe3a`.
- Trajectory artifact: `202ace386bdb05a8888d887a31b83e6335c836e30da145a0d444a813365b680b`.
- Result: `e653742885cc086219cb08a36b84606dbc066941b8751fcc890bf8897c0b2e97`.
- Retention receipt: `1154d5244fbe65f90d30c6e2ad0e39b677f2010dd7051157579fa7bfd93765e7`.

## Evidence

- Start-zero hashes: 5/5 exact; decoded repeats and denoise-path repeats: all
  bit-identical.
- Captured: 50 complete 50x6 decoded tensors and 500 complete 50x32 state plus
  velocity denoise records.
- Frozen bridge pass: false. Uniform report-only pass: false. Source objective
  ratio pass: true.
- Per-start probe passes: start 0 = 3/5; starts 50/100/150/200 = 0/5 each.
- Per-start violation counts: 5, 649, 543, 513, 505; total 2,215.
- No optimizer, retry, Gate C, threshold change, hardware, network, external
  compute, or Brev.
- Live verifier and tracked-only verifier both reconstruct result `e6537428...`.

## Result

Reviewer 271 verifies the baseline negative. Preserve this boundary remotely,
then compose separate bounded optimizer authority from the retained paths.
