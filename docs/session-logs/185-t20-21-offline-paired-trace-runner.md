# Session Log 185 - T20.21 Offline Paired Trace Runner

## Scope

Brief 152 implemented a thin offline comparator for two independently signed,
role-separated joint/action/event traces. Both checked traces are synthetic
fixtures. No hardware, camera, model, optimizer, external compute, or Brev was
used, and no calibration or twin parameter was changed.

## Implementation And Result

- Each trace binds role, evidence source, clock source, exact six-joint `q0`,
  strictly increasing nanosecond timestamps, joint positions, proposed actions,
  issued/safety-modified actions, measured/applied actions, and task events.
- The runner requires each trace's first joint sample to equal its declared
  `q0`, distinct safe trace identifiers, exact cross-trace `q0`, equal length,
  and an exact proposed-command sequence before downstream comparison.
- Joint, issued-action, measured-action, event-presence, and elapsed-event-time
  diagnostics remain separate. Event-time comparison is withheld when clock
  identities differ. Pixels and privileged observable-trace fields are
  rejected.
- The matched fixture has zero joint/action error and zero event-time delta.
  Nine fixed one-factor cases route all declared mismatch categories; the
  length case also reports proposed-sequence mismatch because the sequences no
  longer have equal length.

## Evidence

- Source observer fixture identity:
  `560480c705a3b3ec9e98fc1a74bb0d1112b7f973fc8877b272b08597d2abb4e1`.
- Runner contract identity:
  `aaa53d2d555c2eaf6190276415812a2400bd9154199874e67a14b11d44c81644`.
- Simulator trace identity:
  `ad3cd4c8622a4d9e2b9d2dabd042596b3ca3cd3dcf16410bee44db1ede637721`.
- Observable-schema trace identity:
  `b5aa3c0ce0a0b1c35d7c1cfcd26c2daec9b816d47c5f662573ce870d81a14884`.
- Matched result identity:
  `13e04a15b0b929a115ab2dc8d1596effa2fe781bb980a1fcbe416b47a2844108`.
- Tracked fixture identity:
  `483fbe671f1ec9d75477c0109af9e23981b371b4987e9ec7e40ced5b78c687af`.
- Implementation commit: `7f264ab`.

## Validation And Review

Seventeen focused paired-trace/observer/registry tests passed. The relevant
broad gate passed 105 tests covering both new contracts, strict-v2 semantics,
experience records and compilation, authority composition, documentation, and
canonical state pointers. The checked artifact reverified exactly.

Same-agent adversarial review covered false `q0` declarations, trace aliasing,
action-variant relabeling, missing fields, signed mutation, non-finite and
wrong-width vectors, boolean/duplicate indices, non-monotonic time, duplicate
events, pixel and privileged leakage, unsynchronized clocks, downstream
comparison before alignment, contract re-signing, authority escalation,
input mutation, and cleanup side effects.

## Result

Reviewer Decision 182 verifies only synthetic offline paired-trace runner
conformance. It does not establish hardware observation, paired real/sim
evidence, clock synchronization, calibration, twin fidelity, physical success,
or physical qualification. T20.22 is next.
