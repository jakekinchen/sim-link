# Reviewer Decision 152 - Continue T20.4 After 250 Updates

`CONTINUE_WITH_500_TOTAL_UPDATES`

Reviewed implementation boundary `35c22fd0bdde2ec9fc6f9f930fd2f81055ad4e72`
and the immutable 250-update training and held-out evaluation artifacts.

The accounting is exact and fail-closed: 250 optimizer updates, two
microbatches per update, 500 recorded microbatch losses and starts, 250 update
means and pre-clip gradient norms, and 390 unique valid starts. All values are
finite. The run remains bound to the exact T20.1 source, model, processing,
coordinate, seed, and local-MPS contracts.

The result is behaviorally negative. The action sequence changed and held-out
loss fell from 130.0066 to 31.4226, but the policy made zero strict contacts and
lifted 0.0003007 mm against the 25 mm threshold. Five keyframes, all failed gate
margins, zero assist, and zero projection are preserved. No promotion claim is
made.

The large finite loss reduction justifies one independent 500-total-update
rung to test whether further fitting changes semantic behavior. Extend the
evaluator's exact-count gate first. Do not run 1,000 updates unless the
500-update evidence receives another explicit review decision.
