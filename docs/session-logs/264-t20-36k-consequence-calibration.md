# Session Log 264 - T20.36k Consequence Calibration

## Evidence

- Result: `a3b391784eaca8fef2cb9ff6abe45cc21346cada8f9483be60692dac0faf1f66`.
- File SHA-256: `714b50ed820866fb99ebb186847bff38d2ef33eac23ac70eac622d99e9381391`.
- Implementation: `fbdb0aad4f268268ae567836fc69866c97e528b1`, confirmed on origin.
- Canonical source: seed 0, 244 frames, episode file `586a3e67...`, raw
  rollout identity `9e186088...`.
- Matrix: six joints, seven exhaustive phase groups, six fixed magnitudes,
  two signs; 252 pairs, 202 pass, 50 fail, zero non-monotonic cells.
- Minimum phase ceilings: shoulder pan 0.1, shoulder lift 0.025, elbow flex
  0.05, wrist flex 0.1, wrist roll 0.4, gripper 0.01 rad.
- Verification: two exact complete physics passes with identical semantic
  matrix; signed artifact verifier; 13 focused tests; 80/82 broader T20.36
  tests pass. The two remaining tests encode the pre-install expectation that
  Accelerate/num2words are absent and are invalid after the authorized
  T20.36j offline install.

## Result

Reviewer 261 verifies the model-free calibration and opens Brief 205 to freeze
the amendment and score retained evidence. No gate changed in T20.36k; strict
uniform error remains report-only, and no model, optimizer, Gate C, hardware,
external compute, or Brev action occurred.
