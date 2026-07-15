# Session Log 221 - T20.35m Factorial Interaction Audit

## Evidence

- Implementation/report commit: `2ba6d8ece3daedbdc2cd371b981b249977af7b61`.
- Audit identity: `83105424d6faf668d8a41a70999e25a82338bb2537c802f5a4a60803df3cedb0`.
- File SHA-256: `5628cbf808484baf31943c5361d8de98b38981460b736a3b77764928ff754684`.
- Fifty-two relevant tests and 24 subtests pass.
- Exact verification passes under Python 3.11 and 3.12.

## Result

Active noise is harmful at both padded settings for worst error, mean error,
and spread. Padded noise changes sign for worst/mean by active context. The best
condition is active-zero/padded-normal, which remains Gate-B-negative.

Reviewer 218 routes T20.35n to a separately reviewed active-scale 0.25/0.5
evaluation with padded noise normal. No model, inference, optimizer, Gate C,
hardware, external compute, or Brev action occurred.
