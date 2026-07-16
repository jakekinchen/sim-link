# Reviewer Decision 251 - Verify T20.36h Consumed Runtime Dependency Failure

**Decision:** `VERIFY_CONSUMED_ATTEMPT_DEPENDENCY_FAILURE_NO_RETRY`

## Reviewed Boundary

Brief 199; implementation `29b9525`; remote authorization boundary `41d1540`;
attempt `43c2d0a1...`; signed failure `56415b28...`; tracked result
`3804eff6...`; exact verifier output; pinned dependency metadata; and complete
scoped diff through `d680eca`.

## Adversarial Findings

- The immutable attempt marker preceded model import. The exact local VLM
  checkpoint began construction with no network or CPU fallback.
- AutoProcessor stopped on missing `num2words`. No policy checkpoint loaded, no
  action was decoded, no optimizer was created, and zero updates ran. Gate B
  was not evaluated and must not be reported as a policy failure.
- The failure is a preflight-contract defect. Pinned LeRobot declares
  `num2words>=0.5.14,<0.6.0` directly in its `smolvla` extra and also delegates
  to `accelerate>=1.14.0,<2.0.0`; the consumed venv has neither distribution.
  The old preflight enumerated Transformers but not the optional-extra closure.
- Failure result `3804eff6...` binds the exact permit, attempt, failure class,
  zero-update state, and no-retry/no-Gate-C/no-policy-selection claims.
- The one-use permit is consumed. Installing the dependency or correcting the
  preflight cannot silently revive it.

## Disposition

Verify T20.36h as a consumed-attempt runtime dependency failure, not a Gate B
result. Open Brief 200 for a read-only exact SmolVLA dependency-closure audit
and correction design. A replacement attempt requires a new owner-signed
decision after that audit is verified on origin.

## Withheld Authority

No package installation, environment mutation, replacement attempt, model,
inference, optimizer, policy selection, Gate B change, Gate C, rollout,
hardware, external compute, or Brev.
