# Reviewer Decision 169 - Verify T20.17 Actual LeRobot Processor Observation

`CONTINUE`

Reviewed implementation commit
`cf1d05d9625887f3180ffca63da4a649a1888a41` under Brief 139.

The same-agent adversarial review found no hand-derived preprocessing, second
dataset writer, model or optimizer call, simulator step, hardware path,
external-compute path, or authority escalation. The observation re-verifies
the source manifest before selecting a frame, rejects out-of-range frames and
ambiguous episode mapping, invokes the actual pinned
`DataProcessorPipeline`, and signs only finite descriptors of package-returned
values. Serialized processor and tokenizer files are content-addressed; the
local tokenizer override changes only the offline lookup location. The socket
guard fails closed on any connection attempt. Output recording omits the local
cache path, preventing a host-path alias from becoming signed evidence.

The pinned leLab runtime passed the focused observation test and the 90-test
combined gate. The MuJoCo runtime skips the three package-dependent tests
because it intentionally lacks the LeRobot training dependency; static compile
and import checks still pass there. The incidental AVFoundation duplicate-class
warnings came from the pre-existing leLab runtime and did not affect results.

Continue only with a source-backed projection into the single native
`LeRobotDataset` boundary. Do not turn the fixture into training evidence,
restore a parallel frame/segment/window format, start an optimizer, or alter
the historical physical-observation record.
