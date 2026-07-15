import { api, usePoll } from '../api/client'
import type {
  RobotArtifactSource,
  RobotCalibrationJoint,
  RobotServoEvidence,
} from '../api/types'
import { ErrorState, Hash, KV, Led, Panel, Tag } from '../components/ui'

function ArtifactIdentity({ source }: { source: RobotArtifactSource }) {
  return (
    <div className="grid gap-2 border-t border-line-2 pt-2 sm:grid-cols-3">
      <KV label="artifact">{source.artifact.split('/').pop()}</KV>
      <KV label="file sha256">
        <Hash value={source.artifact_sha256} />
      </KV>
      <KV label="identity sha256">
        <Hash value={source.identity_sha256} />
      </KV>
    </div>
  )
}

function ServoTable({ servos }: { servos: RobotServoEvidence[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left font-mono text-2xs">
        <thead>
          <tr className="border-b border-line-2 text-faint">
            {['id', 'joint', 'model', 'model no.', 'firmware'].map((heading) => (
              <th key={heading} className="cap px-3 py-2 font-normal">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {servos.map((servo) => (
            <tr
              key={`${servo.servo_id}-${servo.joint_name}`}
              className="border-b border-line-2/50 hover:bg-panel-2/60"
            >
              <td className="px-3 py-1.5 text-cyan">{servo.servo_id ?? '—'}</td>
              <td className="px-3 py-1.5 text-ink">{servo.joint_name ?? '—'}</td>
              <td className="px-3 py-1.5">{servo.model ?? '—'}</td>
              <td className="px-3 py-1.5">{servo.model_number ?? '—'}</td>
              <td className="px-3 py-1.5">{servo.firmware_version ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function CalibrationTable({ joints }: { joints: RobotCalibrationJoint[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left font-mono text-2xs">
        <thead>
          <tr className="border-b border-line-2 text-faint">
            {['id', 'joint', 'raw range', 'home offset', 'drive', 'normalization'].map((heading) => (
              <th key={heading} className="cap px-3 py-2 font-normal">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {joints.map((joint) => (
            <tr
              key={`${joint.servo_id}-${joint.joint_name}`}
              className="border-b border-line-2/50 hover:bg-panel-2/60"
            >
              <td className="px-3 py-1.5 text-cyan">{joint.servo_id ?? '—'}</td>
              <td className="px-3 py-1.5 text-ink">{joint.joint_name ?? '—'}</td>
              <td className="px-3 py-1.5 tabular">
                {joint.range_min ?? '—'} → {joint.range_max ?? '—'}
              </td>
              <td className="px-3 py-1.5 tabular">{joint.homing_offset ?? '—'}</td>
              <td className="px-3 py-1.5">{joint.drive_mode ?? '—'}</td>
              <td className="px-3 py-1.5">
                <Tag tone={joint.normalization_mode === 'degrees' ? 'cyan' : 'violet'}>
                  {joint.normalization_mode ?? 'unknown'}
                </Tag>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function Robot() {
  const { data, error } = usePoll((signal) => api.robot(signal), 15000)
  if (error && !data) return <ErrorState error={error} />
  if (!data) {
    return (
      <Panel title="robot evidence registry">
        <div className="flex items-center gap-2 py-8">
          <Led tone="amber" pulse />
          <span className="cap">reading fixed signed artifacts</span>
        </div>
      </Panel>
    )
  }

  const { discovery, census, calibration } = data
  const writes = census.operation_counts.motor_register_writes ?? 0
  const motion = census.operation_counts.motion_commands ?? 0
  const torqueChanges = census.operation_counts.torque_changes ?? 0
  const unexpected = census.operation_counts.unexpected_operations ?? 0
  const privacyClaims = Object.values(discovery.privacy)
  const privacySafe = privacyClaims.length > 0 && privacyClaims.every((value) => value === false)

  return (
    <div className="flex flex-col gap-3">
      <Panel
        title="SO-101 evidence registry · signed artifacts only"
        right={
          <span className="flex items-center gap-2">
            <Tag tone="cyan">read only</Tag>
            <Tag tone="amber">no live discovery</Tag>
          </span>
        }
      >
        <div className="grid gap-3 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <div className="flex items-center gap-2">
              <Led tone="green" />
              <span className="font-display text-lg font-semibold text-ink">Follower arm // 6-axis</span>
            </div>
            <p className="mt-1 max-w-3xl text-xs leading-relaxed text-dim">
              This panel projects tracked, privacy-redacted repository evidence. Opening it never
              scans a bus, camera, serial port, or robot.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-px border border-line bg-line">
            <div className="bg-inset px-3 py-2 text-center">
              <span className="cap block">servos</span>
              <span className="font-mono text-xl text-cyan">{census.servos.length}</span>
            </div>
            <div className="bg-inset px-3 py-2 text-center">
              <span className="cap block">cameras</span>
              <span className="font-mono text-xl text-violet">{discovery.cameras.length}</span>
            </div>
            <div className="bg-inset px-3 py-2 text-center">
              <span className="cap block">joints</span>
              <span className="font-mono text-xl text-amber">{calibration.joint_count ?? '—'}</span>
            </div>
          </div>
        </div>
      </Panel>

      <div className="grid gap-3 xl:grid-cols-2">
        <Panel
          title="discovery receipt"
          right={<Tag tone="green">{discovery.qualification_scope ?? 'unscoped'}</Tag>}
        >
          <div className="grid gap-3 sm:grid-cols-2">
            <KV label="session">{discovery.session_id ?? '—'}</KV>
            <KV label="evidence mode">{discovery.evidence_mode ?? '—'}</KV>
            <KV label="identity stable" mono={false}>
              <Tag tone={discovery.discovery_stability ? 'green' : 'red'}>
                {discovery.discovery_stability ? 'reported' : 'missing'}
              </Tag>
            </KV>
            <KV label="privacy projection" mono={false}>
              <Tag tone={privacySafe ? 'green' : 'red'}>{privacySafe ? 'raw ids excluded' : 'review'}</Tag>
            </KV>
          </div>
          <p className="mt-3 border-l-2 border-cyan/50 pl-2 font-mono text-2xs leading-relaxed text-dim">
            {discovery.discovery_stability ?? 'No discovery stability claim in the signed artifact.'}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <Tag tone={discovery.hardware_opened ? 'amber' : 'dim'}>
              receipt hardware opened · {discovery.hardware_opened ? 'yes' : 'no'}
            </Tag>
            <Tag tone={discovery.physical_follower_commanded ? 'red' : 'green'}>
              follower commanded · {discovery.physical_follower_commanded ? 'yes' : 'no'}
            </Tag>
            <Tag tone={discovery.camera_operation_counts?.capture_property_writes ? 'red' : 'green'}>
              capture writes · {discovery.camera_operation_counts?.capture_property_writes ?? '—'}
            </Tag>
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {discovery.cameras.map((camera, index) => (
              <div key={camera.stable_identity_sha256 ?? index} className="border border-line-2 bg-inset p-2">
                <div className="mb-2 flex items-center gap-2">
                  <Led tone="cyan" />
                  <span className="cap text-ink">camera identity {index + 1}</span>
                  <Tag tone="dim">{camera.frame_count} frames</Tag>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <KV label="mode">
                    {camera.input_mode.width ?? '—'}×{camera.input_mode.height ?? '—'} @{' '}
                    {camera.input_mode.framerate_fps ?? '—'}
                  </KV>
                  <KV label="stable hash">
                    <Hash value={camera.stable_identity_sha256} />
                  </KV>
                </div>
              </div>
            ))}
          </div>
          <div className="mt-3">
            <ArtifactIdentity source={discovery} />
          </div>
        </Panel>

        <Panel
          title="read-only census receipt"
          right={
            <Tag tone={writes + motion + torqueChanges + unexpected === 0 ? 'green' : 'red'}>
              zero writes
            </Tag>
          }
        >
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
            <KV label="reads">{census.operation_counts.read_successes ?? '—'}</KV>
            <KV label="retries">{census.operation_counts.read_retries ?? '—'}</KV>
            <KV label="register writes">{writes}</KV>
            <KV label="motion commands">{motion}</KV>
          </div>
          <div className="mt-3 border border-line-2 bg-inset p-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="cap text-ink">declared census contract</span>
              <Tag tone="violet">fixture evidence</Tag>
              <span className="ml-auto cap">{census.contract.expected_servo_count} expected</span>
            </div>
            <p className="mt-1 font-mono text-2xs text-dim">{census.contract.contract_name}</p>
            <p className="mt-1 cap">
              contract identity <Hash value={census.contract.identity_sha256} />
            </p>
            <p className="mt-1 text-3xs leading-relaxed text-faint">
              Fixture contract is displayed as a constraint artifact; it is not relabelled as the
              physical census receipt above.
            </p>
          </div>
          <div className="mt-3">
            <ArtifactIdentity source={census} />
          </div>
        </Panel>
      </div>

      <Panel title={`observed servo census · ${census.servos.length}`} pad={false}>
        <ServoTable servos={census.servos} />
      </Panel>

      <Panel
        title={`calibration semantics · ${calibration.profile_name ?? 'unnamed'}`}
        right={<Tag tone="violet">{calibration.qualification_scope ?? 'unscoped'}</Tag>}
        pad={false}
      >
        <div className="grid gap-px border-b border-line bg-line sm:grid-cols-4">
          {[
            ['hardware accessed', calibration.hardware_accessed],
            ['follower commanded', calibration.physical_follower_commanded],
            ['motion authority', calibration.motion_authority_granted],
            ['training authority', calibration.training_authority_granted],
          ].map(([label, value]) => (
            <div key={String(label)} className="flex items-center justify-between bg-inset px-3 py-2">
              <span className="cap">{String(label)}</span>
              <Tag tone={value === false ? 'green' : value === true ? 'red' : 'dim'}>
                {value === false ? 'no' : value === true ? 'yes' : 'n/a'}
              </Tag>
            </div>
          ))}
        </div>
        <CalibrationTable joints={calibration.joints} />
        <div className="m-3">
          <ArtifactIdentity source={calibration} />
        </div>
      </Panel>

      <Panel title="robot registration · authority boundary" className="border-amber/30">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <button type="button" className="btn btn-quiet cursor-not-allowed opacity-45" disabled>
            register robot
          </button>
          <div>
            <p className="cap text-amber">registration unavailable</p>
            <p className="mt-1 text-xs text-dim">{data.registration.reason}</p>
          </div>
          <span className="ml-auto hidden font-mono text-4xl text-faint/30 sm:block" aria-hidden>
            ⊘
          </span>
        </div>
      </Panel>
    </div>
  )
}
