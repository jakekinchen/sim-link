# Slice Brief 004 - Balanced PI0.5 Replay

## Objective

Implement T11.1: deterministic training exposure that balances trusted base
behavior with correction data and reports actual source/phase sample counts.

## Inputs

- M10-validated base and correction dataset contracts
- `configurations/robot_lab/pi05_autolearn.example.json`
- local LeRobot training entrypoint used by the cycle runner

## Acceptance

- The ratio is explicit, validated, deterministic by seed, and content-addressed.
- A dry-run predicts source/phase counts for the configured step budget.
- A bounded training smoke records realized counts matching the schedule.
- No external package mutation is required unless it is tracked and pinned.

## Non-goals

- No checkpoint promotion in this slice.
- No physical robot operation.
- No claim that balanced exposure alone proves policy improvement.
