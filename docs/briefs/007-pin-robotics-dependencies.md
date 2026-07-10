# Slice Brief 007 - Pin Robotics Dependencies

## Objective

Complete T16.1 by recording the exact policy/runtime and SO-101 structural inputs
that future twin/compiler/training artifacts must reference.

## Required Identities

- The LeRobot environment actually used for collection, export, training, and inference.
- Any separate local LeRobot checkout and its uncommitted patch identity.
- OpenPI as the PI0.5 transform/normalization semantic reference.
- The Robot Studio SO-101 model currently used by SceneSmith.
- Menagerie `robotstudio_so101` as the proposed next structural lineage.

## Invariants

- Record repository URL, revision, dirty state, relevant path, license, and hashes.
- Never claim that a dirty checkout is reproducible from its commit alone; hash
  its tracked diff and relevant source tree.
- Do not silently switch the runtime model or processor in this slice.
- Do not commit nested dependency trees, weights, datasets, credentials, or caches.
- Do not open hardware or start training.

## Acceptance

- One tracked lock manifest captures all required identities and intended roles.
- A validator rejects missing files, revision/hash/license drift, and a dirty
  dependency whose patch identity was omitted.
- The manifest explicitly records the current split LeRobot state as unresolved
  rather than pretending it is already unified.
- Tests and a live validation report pass.
