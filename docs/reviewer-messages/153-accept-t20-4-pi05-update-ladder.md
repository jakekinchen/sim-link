# Reviewer Decision 153 - Accept T20.4 PI0.5 Update Ladder

`CONTINUE`

Reviewed implementation boundaries `35c22fd0bdde2ec9fc6f9f930fd2f81055ad4e72`
and `7e82001e6ab34269dcdbdb2354f5c280dd539b57`, plus the immutable
250- and 500-update training and strict held-out artifacts.

Update, microbatch, sample-start, loss, and gradient accounting is exact and
finite. The source, checkpoint, processor, coordinate, seed, local-MPS, and
authority bindings remain intact. Both evaluated adapters own every control
frame and preserve five keyframes, measured gate margins, zero assist, and zero
projection.

The 500-update rung drove held-out loss to 1.8620 but still made zero strict
contacts. Its first held-out command retains 0.6551 rad gripper error and the
anchor lift remains 0.0003007 mm versus 25 mm. This disconnect falsifies the
current “more updates alone” hypothesis. Do not spend the 1,000-update rung.

Close T20.4 as verified negative evidence without promotion. Advance to T20.5
to isolate the declared 5/10/15 execution-horizon assumption using the same
500-update weights and inference seed.
