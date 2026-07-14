# Executor Session 166 - T20.13 Dataset-Bound PI0.5 Normalizer

T20.13 fit PI0.5 state and action statistics only from the 488 training frames
after canonical LeRobot conversion. The 244 held-out frames were transformed
for evaluation but contributed no fitted value. State uses the exact first-six
joint-position projection from T20.7; six velocity columns remain excluded.

Train normalized means are within 1.03e-13 of zero and standard deviations
within 2.35e-7 of one versus a 1e-6 tolerance. The smallest fitted standard
deviation is 0.04271 versus the 1e-6 minimum. Maximum inverse errors are
1.137e-9 rad for state and 1.230e-9 rad for action versus 1e-8. No clipping is
used.

With equal six-way loss weights retained, train target mean-square becomes
approximately 1.0 per joint. Wrist roll drops from 412.39 under the checkpoint
normalizer to 1.0, wrist flex from 25.48 to 1.0, and gripper from 2.61 to 1.0.
The frame-zero open gripper changes from 2.792 to 1.411 normalized units.
Held-out values remain finite and invertible but include phase/seed extremes up
to about seven fitted standard deviations, so this is a preprocessing
preflight, not evidence of learned behavior improvement.

The signed artifact identity is `c41977b9...`, file hash is `8fa0d437...`, and
52 relevant tests pass. No model load, inference, optimizer, checkpoint or
dataset mutation, hardware, external compute, or Brev ran.
