# Brief 201 - T20.36j-A Offline Cache Resolution Audit

## Objective

Determine, without network access or environment mutation, whether the exact
missing SmolVLA runtime closure can be resolved from the existing local uv
cache for the consumed-attempt Python 3.12 environment. Sign the exact package
versions and cache-content identities so the remaining owner decision is
bounded to an offline install plus at most one replacement attempt.

## Frozen Inputs

- Verified T20.36i closure audit `0804fd4f...` and environment manifest
  `8fbb324c...`.
- Existing `external/lerobot/.venv` Python 3.12 environment, pinned LeRobot
  source, and the current local uv cache.
- The two declared missing requirements:
  `num2words>=0.5.14,<0.6.0` and `accelerate>=1.14.0,<2.0.0`.
- Reviewer 252's owner blocker. This audit grants no installation or attempt
  authority.

## Required Work

1. Run an explicitly offline, dry-run resolution against the exact existing
   venv and reject any result that proposes packages outside the recursively
   required runtime closure.
2. Bind every proposed distribution to its exact version, compatible cached
   content, metadata, and deterministic content-tree identity.
3. Prove whether network acquisition is required and record the minimal exact
   offline install set.
4. Emit a signed, deterministic result and exact verifier with focused tests.
5. Keep dependency installation, environment mutation, AutoProcessor/model
   construction, attempt-marker creation, and replacement execution false.

## Acceptance

- The result is source/environment/cache bound, deterministic, test covered,
  and remotely preserved.
- Offline resolution succeeds for Python 3.12 or fails closed with no partial
  authority.
- The owner request narrows to exact cached distributions and retains the
  unchanged Gate B and one-replacement-attempt ceiling.

## Prohibited Actions

Network/download, package installation, lockfile or venv mutation,
AutoProcessor/model/checkpoint access, attempt marker, inference, optimizer,
Gate B change, Gate C, rollout, hardware, external compute, or Brev.
