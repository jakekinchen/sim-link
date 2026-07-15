import { api, usePoll } from '../api/client'
import type { ResultGate } from '../api/types'
import { EmptyState, ErrorState, Hash, Panel, PassFail, Tag } from '../components/ui'
import { gateLabel, sci } from '../lib/format'

const GATE_B_OBJECTIVE_THRESHOLD = 0.1

function decisionTone(decision: string | undefined): string {
  if (!decision) return 'dim'
  if (/fail|negative|reject/i.test(decision)) return 'red'
  if (/pass|accept|verified/i.test(decision)) return 'green'
  return 'amber'
}

function taskId(gate: ResultGate): string {
  return /t20_[0-9]+[a-z]?/.exec(gate.schema_version)?.[0] ?? gateLabel(gate.schema_version)
}

function taskOrder(gate: ResultGate): number {
  const match = /t20_([0-9]+)([a-z]?)/.exec(gate.schema_version)
  if (!match) return Number.MAX_SAFE_INTEGER
  const suffix = match[2] ? match[2].charCodeAt(0) - 96 : 0
  return Number(match[1]) * 100 + suffix
}

function ObjectiveTrend({ gates }: { gates: ResultGate[] }) {
  const measured = [...gates]
    .filter(
      (gate): gate is ResultGate & { final_to_baseline_objective_ratio: number } =>
        typeof gate.final_to_baseline_objective_ratio === 'number' &&
        Number.isFinite(gate.final_to_baseline_objective_ratio) &&
        gate.final_to_baseline_objective_ratio >= 0,
    )
    .sort((left, right) => taskOrder(left) - taskOrder(right))
  if (measured.length === 0) {
    return (
      <Panel title="final / baseline objective trend">
        <EmptyState>no signed objective ratios found</EmptyState>
      </Panel>
    )
  }

  const width = 900
  const height = 278
  const margin = { top: 28, right: 28, bottom: 64, left: 62 }
  const plotWidth = width - margin.left - margin.right
  const plotHeight = height - margin.top - margin.bottom
  const ratios = measured.map((gate) => gate.final_to_baseline_objective_ratio)
  const maxRatio = Math.max(...ratios, GATE_B_OBJECTIVE_THRESHOLD)
  const domainMax = Math.max(0.2, Math.ceil(maxRatio * 10) / 10)
  const xAt = (index: number) =>
    margin.left + (measured.length === 1 ? plotWidth / 2 : (index / (measured.length - 1)) * plotWidth)
  const yAt = (ratio: number) => margin.top + (1 - ratio / domainMax) * plotHeight
  const points = measured.map((gate, index) => `${xAt(index)},${yAt(gate.final_to_baseline_objective_ratio)}`)
  const ticks = Array.from({ length: 5 }, (_, index) => (domainMax / 4) * index)

  return (
    <Panel
      title="final / baseline objective trend"
      right={
        <span className="flex items-center gap-2">
          <Tag tone="cyan">{measured.length} measured</Tag>
          <Tag tone="dim">{gates.length - measured.length} unreported</Tag>
        </span>
      }
    >
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-1">
        <span className="cap flex items-center gap-1.5">
          <span className="inline-block h-px w-5 bg-cyan" /> signed ratio
        </span>
        <span className="cap flex items-center gap-1.5 text-green">
          <span className="inline-block w-5 border-t border-dashed border-green" />
          Gate B objective threshold ≤ 0.10
        </span>
        <span className="cap ml-auto text-faint">missing ratios are omitted, never inferred</span>
      </div>
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="block h-auto w-full overflow-visible"
        role="img"
        aria-labelledby="objective-trend-title objective-trend-description"
      >
        <title id="objective-trend-title">Final to baseline objective ratio by signed task gate</title>
        <desc id="objective-trend-description">
          Ratios are shown in task order with a Gate B objective threshold at 0.10. Gates without
          signed ratios are omitted.
        </desc>
        <defs>
          <linearGradient id="objective-trend-stroke" x1="0" x2="1">
            <stop offset="0" stopColor="#ffb454" />
            <stop offset="1" stopColor="#56c8d8" />
          </linearGradient>
        </defs>
        {ticks.map((tick) => {
          const y = yAt(tick)
          return (
            <g key={tick}>
              <line
                x1={margin.left}
                x2={width - margin.right}
                y1={y}
                y2={y}
                stroke="#1d242f"
                vectorEffect="non-scaling-stroke"
              />
              <text
                x={margin.left - 10}
                y={y + 4}
                textAnchor="end"
                fill="#7a8aa0"
                fontFamily="IBM Plex Mono"
                fontSize="10"
              >
                {tick.toFixed(2)}
              </text>
            </g>
          )
        })}
        <line
          x1={margin.left}
          x2={width - margin.right}
          y1={yAt(GATE_B_OBJECTIVE_THRESHOLD)}
          y2={yAt(GATE_B_OBJECTIVE_THRESHOLD)}
          stroke="#58d9a2"
          strokeDasharray="6 5"
          strokeWidth="1.5"
          vectorEffect="non-scaling-stroke"
        />
        <text
          x={width - margin.right}
          y={yAt(GATE_B_OBJECTIVE_THRESHOLD) - 7}
          textAnchor="end"
          fill="#58d9a2"
          fontFamily="IBM Plex Mono"
          fontSize="10"
          letterSpacing="1"
        >
          0.10 GATE B
        </text>
        <polyline
          points={points.join(' ')}
          fill="none"
          stroke="url(#objective-trend-stroke)"
          strokeWidth="2"
          vectorEffect="non-scaling-stroke"
        />
        {measured.map((gate, index) => {
          const x = xAt(index)
          const y = yAt(gate.final_to_baseline_objective_ratio)
          return (
            <g key={gate.artifact}>
              <circle
                cx={x}
                cy={y}
                r="5"
                fill="#0b0e13"
                stroke="#56c8d8"
                strokeWidth="2"
                vectorEffect="non-scaling-stroke"
              >
                <title>
                  {taskId(gate)} · {gate.final_to_baseline_objective_ratio.toPrecision(5)}
                </title>
              </circle>
              <text
                x={x}
                y={Math.max(margin.top + 10, y - 11)}
                textAnchor="middle"
                fill="#cdd8e6"
                fontFamily="IBM Plex Mono"
                fontSize="10"
              >
                {sci(gate.final_to_baseline_objective_ratio)}
              </text>
              <text
                x={x}
                y={height - margin.bottom + 24}
                textAnchor="middle"
                fill="#7a8aa0"
                fontFamily="IBM Plex Mono"
                fontSize="10"
                letterSpacing="0.5"
              >
                {taskId(gate)}
              </text>
            </g>
          )
        })}
        <line
          x1={margin.left}
          x2={width - margin.right}
          y1={height - margin.bottom}
          y2={height - margin.bottom}
          stroke="#47546a"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </Panel>
  )
}

export default function Tasks() {
  const { data, error } = usePoll((signal) => api.tasks(signal), 15000)
  if (error && !data) return <ErrorState error={error} />
  const gates = data?.result_gates ?? []
  return (
    <div className="flex flex-col gap-3">
      <ObjectiveTrend gates={gates} />
      <Panel title={`signed result gates · ${gates.length}`} pad={false}>
        {gates.length === 0 ? (
          <EmptyState>no result gates found</EmptyState>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left font-mono text-2xs">
              <thead>
                <tr className="border-b border-line-2 text-faint">
                  {['gate', 'decision', 'gate b', 'obj ratio', 'strict', 'updates', 'artifact'].map(
                    (heading) => (
                      <th key={heading} className="cap px-3 py-2 font-normal">
                        {heading}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {gates.map((gate) => (
                  <tr key={gate.artifact} className="border-b border-line-2/50 hover:bg-panel-2/60">
                    <td className="px-3 py-1.5 text-ink">{gateLabel(gate.schema_version)}</td>
                    <td className="px-3 py-1.5">
                      {gate.decision ? (
                        <Tag tone={decisionTone(gate.decision)}>{gate.decision}</Tag>
                      ) : (
                        '—'
                      )}
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
          </div>
        )}
      </Panel>
    </div>
  )
}
