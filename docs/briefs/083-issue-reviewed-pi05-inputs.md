# Slice Brief 083 - Issue Reviewed PI0.5 Inputs

**Date:** 2026-07-13

## Objective

Issue the three production review artifacts required by the existing PI0.5
reviewed-input gate for the accepted static-pose bracket.

## Contract

- Bind acceptance to manifest `75d8aae3...` and Reviewer 108's bracket-only
  decision.
- Bind camera roles by exact stable identity using Reviewer 089's physical
  content review: `69d55167...` wrist/left-wrist model input and `9931d030...`
  external overview/base model input.
- Bind the exact sorting-checkpoint task prompt already reviewed by Reviewer
  089.
- Use one finite production validity interval and one same-agent review record
  with exact subject markers for all three artifacts.
- Build and verify the production reviewed-input gate without running
  preprocessing, loading a model, or using hardware.

This slice may grant `production_input_issuance_allowed` and
`pi05_reviewed_input_bundle_valid` at the reviewed semantic boundary. It must
continue to report `accepted_live_policy_input=false` and withhold
`policy_shadow_input_valid`, real preprocessing, model loading, inference,
shadow, replay, motion, and training because the current session retained frame
hashes but not pixel bytes.
