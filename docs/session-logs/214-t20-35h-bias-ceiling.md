# Session Log 214 - T20.35h Bias Ceiling

## Evidence

- Implementation: `68b71153c769492e5eeedf2b7336cbba85f1a722`.
- Artifact identity:
  `63e1181b2f825de108a85525e38e0ae728cae2288a16b7d3763851e8109a6593`.
- Artifact file SHA-256:
  `8792ce2b2d9310e71404ef9fb4278665469d40e59d3ef6139b9f6cfa8b6057b8`.
- Six focused and 76 relevant tests pass.
- Writer verification passes under Python 3.11 and 3.12.

## Result

| Correction ceiling | Worst held-out maximum (rad) | Aggregate mean (rad) | Exceedances | Pass |
| --- | ---: | ---: | ---: | --- |
| Global channel | 0.113302 | 0.019781 | 159 | no |
| Time conditioned | 0.136460 | 0.017710 | 96 | no |

Reviewer 211 routes T20.35i to model-free residual-variance localization.
Gate B and Gate C remain closed. No model, checkpoint, inference, optimizer,
training, mutation, hardware, external compute, or Brev action occurred.
