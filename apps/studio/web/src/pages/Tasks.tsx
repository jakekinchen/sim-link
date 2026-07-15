import { api, usePoll } from '../api/client'
import { EmptyState, ErrorState, Hash, Panel, PassFail, Tag } from '../components/ui'
import { gateLabel, sci } from '../lib/format'

function decisionTone(decision: string | undefined): string {
  if (!decision) return 'dim'
  if (/fail|negative|reject/i.test(decision)) return 'red'
  if (/pass|accept|verified/i.test(decision)) return 'green'
  return 'amber'
}

export default function Tasks() {
  const { data, error } = usePoll((signal) => api.tasks(signal), 15000)
  if (error && !data) return <ErrorState error={error} />
  const gates = data?.result_gates ?? []
  return (
    <Panel title={`signed result gates · ${gates.length}`} pad={false}>
      {gates.length === 0 ? (
        <EmptyState>no result gates found</EmptyState>
      ) : (
        <table className="w-full text-left font-mono text-2xs">
          <thead>
            <tr className="border-b border-line-2 text-faint">
              {['gate', 'decision', 'gate b', 'obj ratio', 'strict', 'updates', 'artifact'].map((h) => (
                <th key={h} className="cap px-3 py-2 font-normal">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gates.map((gate) => (
              <tr key={gate.artifact} className="border-b border-line-2/50 hover:bg-panel-2/60">
                <td className="px-3 py-1.5 text-ink">{gateLabel(gate.schema_version)}</td>
                <td className="px-3 py-1.5">
                  {gate.decision ? <Tag tone={decisionTone(gate.decision)}>{gate.decision}</Tag> : '—'}
                </td>
                <td className="px-3 py-1.5">
                  <PassFail value={gate.gate_b_one_batch_memorization_passed} />
                </td>
                <td className="px-3 py-1.5">{sci(gate.final_to_baseline_objective_ratio)}</td>
                <td className="px-3 py-1.5">
                  {gate.strict_success_count !== undefined
                    ? `${gate.strict_success_count}/${gate.held_out_seed_count ?? '?'}`
                    : '—'}
                </td>
                <td className="px-3 py-1.5">{gate.optimizer_update_count ?? '—'}</td>
                <td className="px-3 py-1.5 text-dim" title={gate.artifact}>
                  <Hash value={gate.artifact.split('/').pop() ?? ''} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
