# Slice Brief 093 - Antipodal Contact Gate

**Date:** 2026-07-13

## Objective

Correct the experiment-proven weakness in the strict grasp contact proxy by
adding a separately versioned antipodal two-jaw geometry gate.

## Contract

- Preserve the complete v1 evaluator fixture and identity byte-for-byte.
- Bind the correction to Brief 092's contact-span collapse evidence.
- Require two distinct jaw identities, finite metric contact points, minimum
  span, opposing unit normals, and alignment of those normals with the contact
  axis at grasp confirmation and stable hold.
- Call this an antipodal two-jaw contact proxy, not a full 6D wrench-closure
  proof or physical calibration.
- Reject missing, same-jaw, same-side, too-short-span, non-opposing,
  misaligned, non-finite, and malformed witnesses.
- Run positive and adversarial analytic fixtures through the same v2 evaluator.

This slice may prove the v2 contact-geometry gate. It may not prove an actual
MuJoCo or physical grasp, force closure, policy success, training readiness,
physical qualification, or motion authority.

## Verified Outcome

- The v1 fixture remains exact at identity `4f0bad3c...`.
- V2 requires distinct jaw IDs, at least 0.02 m contact span, normal dot at most
  -0.8, and at least 0.8 alignment with the contact axis.
- One analytic antipodal positive passes semantic expert success and remains
  non-policy. All 17 adversarial negatives fail for their expected reason.
- The adversarial set includes Brief 092's exact 0.004907838 m collapsed span,
  missing/malformed/non-finite witnesses, same-jaw identity, same-side normals,
  and opposing but axis-misaligned normals.
- Artifact identity: `950e7568025f4fe09b9e51633da71b3ee90212ee5ea9c86be8194863cea2e640`.
- File SHA-256: `5ac9c96e7efb1b9980cbc2159d58dda28b033e47e5d063e944367d5a42472e45`.
