# Reviewer Decision 188 - Verify T20.27 Paired Source-Action Comparison

`ACCEPT_VERIFIED_FRAME_ZERO_DISTRIBUTION_REGRESSION`

Reviewed Brief 158 through artifact commit `e1fc104` and gate identity
`37c7fb8fb2899e3c368cc5c25a2e3f0a0b8526a43477b979632edc850fd9eabe`.

The two independent T20.26 batches reproduce every scheduled action exactly
for each candidate. The duplicate-free view pairs clean and recovery actions
over the same five inference seeds and compares each with the immutable held-
out seed-6 source action. All five seeds and all six joints are accounted for.

Clean mean source-action MAE is 0.50833 rad. Recovery mean source-action MAE is
0.61926 rad, a 0.11094 rad regression. Recovery regresses on 5/5 paired seeds.
At the joint level, recovery improves only gripper by 0.00120 rad; shoulder pan,
shoulder lift, elbow flex, wrist flex, and wrist roll regress by 0.00195,
0.18749, 0.07576, 0.17851, and 0.22311 rad respectively.

This verifies a frame-zero requested-action distribution regression under the
five declared inference seeds. It is not a statistical-significance claim and
does not establish later closed-loop behavior, contact, strict success, or the
value of another optimizer rung.

Same-agent adversarial review checked source substitution, duplicate-process
equality, candidate/sample/seed/joint ordering, finite actions, paired-seed
alignment, requested-action representation, signed mutation, authority
escalation, and cleanup side effects. Eighty-one relevant tests pass, and the
gate recomposes from the four live T20.26 batches and source episode.

T20.27 grants only a verified offline frame-zero distribution result. It does
not authorize model inference, an optimizer, action application, policy
acceptance, transfer, promotion, hardware, external compute, or Brev. The next
safe diagnostic is source/recovery phase-sampling exposure under the exact
training seed before considering any further training.
