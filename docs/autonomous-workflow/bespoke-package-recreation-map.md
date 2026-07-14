# Bespoke-versus-Package Recreation Map

**Status:** T20.17 first-slice contract (2026-07-14)

SceneSmith should own its evidence, grasp truthfulness, SO-101 bridge, and
authority rules. It should not duplicate a package's dataset storage,
normalization, or processor behavior merely to make those results auditable.
The pinned LeRobot checkout remains the executable ML, dataset, motor, teleop,
and processor implementation; SO-ARM100 supplies the source MJCF; leLab is a
UI/runtime shell. This map is a migration constraint, not a reinterpretation of
historical artifacts.

## Retain as bespoke IP

| Surface | Reason | Rule |
| --- | --- | --- |
| `artifact_contract.py` | Canonical JSON content identities and fail-closed references bind all evidence. | Keep small and dependency-free. |
| `strict_grasp.py` and contact semantics | Antipodal witness, assistance, phase, and release truthfulness are the capability oracle. | Never substitute terminal placement for strict success. |
| Geometry-derived grasp and scripted episode generator | The constructive midpoint/aperture primitive creates the valid unassisted source experience. | Retain geometry derivation; do not revive blind search. |
| `so101_processor.py` | Explicit calibrated-degree/percent to radians bridge with golden round trips. | Keep requested/executed semantics separate. |
| Authority composer and `lerobot_stack.py` | Training and hardware fail-closed decisions plus pinned package identity. | Keep enforcement thin and central. |

## Collapse behind package boundaries

| Current seam | Replacement | Required proof |
| --- | --- | --- |
| Compiler-owned frames, segments, and windows used as a second training store | A signed eligibility/provenance manifest over a single `LeRobotDataset` (`lerobot_native_episode_manifest.py`). | Episode bytes, eligibility/quarantine, split, metadata, and dataset statistics hash; no Parquet translation before training. |
| `pi05_fixture_preprocessing.py` plus `pi05_preprocessing_contract.py` mirroring | Run the pinned LeRobot processor pipeline and hash its actual input/output tensors and serialized pipeline identity. | Same dataset metadata/stat hash, finite tensor hashes, and deterministic repeated output; no hand-derived normalization substitute. |
| Live physical-twin observation stack | A smaller future adapter over LeRobot camera/robot APIs with owner permit, read-only session, and content-addressed frame invariants. | Do not change the present historical live evidence in T20.17. |

## Retire after dependency proof

The following first-slice modules have no production import or configuration
consumer and are deleted with their dedicated tests:

- `static_pose_session_review.py`
- `evidence_image_store.py`
- `so101_physical_coordinates.py`

The retired T19.0 wrappers and the large search body are not deleted by this
slice because current geometry episode code still imports their primitive
helpers. A later isolated migration must first move the retained primitive to a
named geometry module, preserve the existing T19 evidence as immutable, and
then delete the dead wrappers. The enduring lesson is: a 12-sample Halton
scheme with bases above its sample count is not meaningful search; place the
grasp at mid-height and derive aperture from geometry.
