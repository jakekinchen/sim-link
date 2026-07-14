# Executor Session 156 - T20.4 PI0.5 Update Ladder

T20.4 added exact optimizer-update and gradient-accumulation accounting to the
source-bound PI0.5 LoRA runner. The reviewed 250-update rung used 500 finite
microbatches and reduced held-out loss from 130.0066 to 31.4226, but its strict
rollout made zero contacts. Reviewer 152 authorized one independent 500-total-
update rung while withholding 1,000 updates.

The 500-update run recorded exactly 1,000 microbatches, 500 per-update loss
means, 500 pre-clip gradient norms, and 390 unique valid source starts. All were
finite. Train loss changed from 100.84408569335938 to 6.476014852523804 and
held-out loss from 130.006591796875 to 1.8620187640190125.

The saved adapter controlled all 244 held-out seed-2 frames with 49 replans,
zero action projections, and zero assist. It made zero strict-v2 contacts and
lifted only 0.00000030070669393422733 m against the 0.025 m gate. Five 256 px
keyframes and measured gate margins are signed. The first requested action
still differed from the expert by 0.1507563 rad mean, dominated by a 0.6551162
rad gripper-coordinate error.

Thirty-seven focused training, evidence, authority, coordinate, and strict-
grasp tests passed. No hardware, network, external compute, or Brev was used.
T20.4 closes negative; the 1,000-update rung is retired because further loss
optimization no longer has evidence of translating to contact behavior.
