import { useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, frameUrl, mediaUrl, usePoll } from '../api/client'
import type { TimelineFrame } from '../api/types'
import { ErrorState, Hash, KV, Panel, PassFail, Tag } from '../components/ui'
import { phaseColor, sci } from '../lib/format'

function PhaseStrip({ timeline }: { timeline: TimelineFrame[] }) {
  return (
    <div className="flex h-4 w-full overflow-hidden border border-line-2">
      {timeline.map((frame) => (
        <div
          key={frame.frame_index}
          title={`frame ${frame.frame_index} · ${frame.phase ?? frame.task_phase ?? '?'}${
            frame.candidate_strict_contact ? ' · strict contact' : ''
          }`}
          className="h-full flex-1"
          style={{
            background: phaseColor(frame.phase ?? frame.task_phase),
            opacity: frame.candidate_strict_contact ? 1 : 0.55,
          }}
        />
      ))}
    </div>
  )
}

function AnchorSpark({ timeline }: { timeline: TimelineFrame[] }) {
  const points = timeline.filter((f) => typeof f.anchor_z_m === 'number')
  if (points.length < 2) return null
  const zs = points.map((f) => f.anchor_z_m as number)
  const [min, max] = [Math.min(...zs), Math.max(...zs)]
  const span = Math.max(max - min, 1e-9)
  const path = points
    .map((f, i) => {
      const x = (i / (points.length - 1)) * 100
      const y = 28 - (((f.anchor_z_m as number) - min) / span) * 24
      return `${i === 0 ? 'M' : 'L'}${x.toFixed(2)},${y.toFixed(2)}`
    })
    .join(' ')
  return (
    <div>
      <div className="cap mb-1">
        anchor z (m) · min {sci(min)} · max {sci(max)} · Δ {sci(max - min)}
      </div>
      <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-16 w-full border border-line-2 bg-panel-2">
        <path d={path} fill="none" stroke="#56c8d8" strokeWidth="0.6" vectorEffect="non-scaling-stroke" />
      </svg>
    </div>
  )
}

export default function EpisodeDetail() {
  const { kind = '', stem = '' } = useParams()
  const id = `${kind}/${stem}`
  const { data, error } = usePoll((signal) => api.episode(id, signal), null)
  const [frame, setFrame] = useState(0)
  const [view, setView] = useState<'top' | 'wrist'>('top')
  const flatMeta = useMemo(() => {
    if (!data) return []
    return Object.entries(data)
      .filter(([k, v]) => (typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean') && k !== 'id')
      .slice(0, 24)
  }, [data])

  if (error) return <ErrorState error={error} />
  if (!data) return <Panel title={id}>loading…</Panel>
  const frameCount = data.timeline.length

  return (
    <div className="flex flex-col gap-3">
      <Panel
        title={
          <span>
            <Link to="/episodes" className="text-faint hover:text-ink">
              episodes /
            </Link>{' '}
            {stem}
          </span>
        }
        right={<Tag tone={data.source === 'expert' ? 'green' : 'violet'}>{data.source}</Tag>}
      >
        <div className="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-4">
          <KV label="seed">{String(data.seed ?? data.episode_spec?.seed ?? '—')}</KV>
          <KV label="frames">{String(frameCount)}</KV>
          {data.source === 'policy_trace' ? (
            <>
              <KV label="adapter">{String(data.adapter_id ?? '—')}</KV>
              <KV label="strict success">
                <PassFail value={(data.training_seed_reproduction_strict_success as boolean) ?? null} />
              </KV>
              <KV label="trace identity">
                <Hash value={data.identity_sha256 as string} />
              </KV>
              <KV label="checkpoint">
                <Hash value={data.checkpoint_sha256 as string} />
              </KV>
            </>
          ) : (
            <KV label="strict success">
              <PassFail value={data.outcome?.strict_success ?? true} />
            </KV>
          )}
        </div>
      </Panel>

      {data.mirror_video && (
        <Panel title="mirror video · policy re-render vs expert recorded" pad={false}>
          <video controls loop className="max-h-[420px] w-full bg-black" src={mediaUrl(data.mirror_video)} />
        </Panel>
      )}

      {data.source === 'expert' && frameCount > 0 && (
        <Panel
          title={`camera frames · ${view} · frame ${frame}/${frameCount - 1}`}
          right={
            <span className="flex gap-1">
              {(['top', 'wrist'] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setView(v)}
                  className={`border px-1.5 py-px text-3xs uppercase ${
                    view === v ? 'border-cyan/50 text-cyan' : 'border-line-2 text-dim'
                  }`}
                >
                  {v}
                </button>
              ))}
            </span>
          }
        >
          <img src={frameUrl(id, frame, view)} alt={`${view} frame ${frame}`} className="mx-auto max-h-96 border border-line-2" />
          <input
            type="range"
            min={0}
            max={frameCount - 1}
            value={frame}
            onChange={(e) => setFrame(Number(e.target.value))}
            className="mt-2 w-full"
          />
        </Panel>
      )}

      <Panel title="phase timeline">
        <PhaseStrip timeline={data.timeline} />
        <div className="mt-3">
          <AnchorSpark timeline={data.timeline} />
        </div>
      </Panel>

      <Panel title="signed fields">
        <div className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-3">
          {flatMeta.map(([key, value]) => (
            <KV key={key} label={key.replace(/_/g, ' ')}>
              {typeof value === 'string' && /^[0-9a-f]{64}$/.test(value) ? <Hash value={value} /> : String(value)}
            </KV>
          ))}
        </div>
      </Panel>
    </div>
  )
}
