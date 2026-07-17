# Third-Party and Artifact Boundary

The exporter copies only tracked SceneSmith-owned code/evidence and the vendored
Menagerie reference already present at the pinned closeout commit. It never
copies the local `external/` checkouts.

| Dependency | Exact pin | License | Role |
| --- | --- | --- | --- |
| LeRobot | `e40b58a8dfa9e7b86918c374791599d070518d11` + patch `efe912e3...` | Apache-2.0 | Unified policy/dataset/processor/training runtime |
| SO-ARM100 | `fda892cba81032c46c40976a48c9ceadbf40a9ca` | Apache-2.0 | Active SO-101 MJCF source |
| leLab | `def3e9e51e99c03e01b214dc8a0d9b7c2dd5f0da` | Apache-2.0 | URDF required by current source proof; optional UI/runtime reference |
| MuJoCo Menagerie | `71f066ad0be9cd271f7ed58c030243ef157af9f4` | Apache-2.0 | Vendored robotstudio_so101 structural reference |
| openpi | `15a9616a00943ada6c20a0f158e3adb39df2ccac` | Apache-2.0 | PI0.5 semantic reference only |
| SceneSmith capsule | exact commit in `SOURCE_MANIFEST.json`; original T20.43c terminal `d848a1a8...`; T20.43c-R2 final `be11a258...`; F0b final `7b7f4f77...` | MIT | Portable simulator/data/evaluator source and non-authorizing evidence history |

## Required byte checks

- LeRobot patch SHA-256:
  `efe912e3cf75c76a3b0a01d2baec8f0856ce2e2a981f4845978f0e9e34155284`.
- SO-ARM100 active MJCF SHA-256:
  `d75253eb568e8a7214db9c631ab7bed4217f608a26f7276ebe9a7636cac82580`.
- leLab URDF SHA-256:
  `443d38d756e01bac7d3455b24430047ddc6427105e0d3454b2003116f5f67236`.
- Unified LeRobot stack identity:
  `c8e903e7f1b75215864719398c902d864d8cbd7f43e01f03ffb22c8de240a7a4`.

## Not redistributed

- LeRobot, SO-ARM100, leLab, or openpi source checkouts.
- Hugging Face model weights or gated checkpoints.
- The 1.15 GB local LeRobot lock/cache environment.
- The full 31,366-frame R0 output, camera observations, policy checkpoints,
  optimizer state, bulk rollout trees, or campaign videos. The included 66 MB
  asset pack is limited to the exact 10-episode base plus three signed
  simulation traces and explicitly transfers no authority.
- Robo Scan source or private scan/calibration observations.

Acquire each dependency from its owner, verify its license and pin, and record
new download/checkpoint hashes. The historical hashes prove what this program
used; they are not a substitute for verifying newly acquired bytes.
