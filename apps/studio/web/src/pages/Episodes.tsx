import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, usePoll } from '../api/client'
import type { EpisodeSummary } from '../api/types'
import { EmptyState, ErrorState, Panel, PassFail, Tag } from '../components/ui'
import { sci } from '../lib/format'

type SourceFilter = 'all' | 'expert' | 'policy_trace'

function strictOf(episode: EpisodeSummary): boolean | null {
  if (episode.source === 'expert') return episode.outcome?.strict_success ?? true
  return episode.strict_success ?? null
}

export default function Episodes() {
  const { data, error } = usePoll((signal) => api.episodes(signal), 10000)
  const [source, setSource] = useState<SourceFilter>('all')
  const episodes = useMemo(() => {
    const items = data?.episodes ?? []
    return source === 'all' ? items : items.filter((e) => e.source === source)
  }, [data, source])

  if (error && !data) return <ErrorState error={error} />
  return (
    <Panel
      title={`episodes · ${episodes.length}`}
      right={
        <span className="flex items-center gap-2">
          <Link to="/episodes/compare" className="btn btn-quiet">
            compare mirrors
          </Link>
          <select
            value={source}
            onChange={(e) => setSource(e.target.value as SourceFilter)}
            className="border border-line-2 bg-panel-2 px-1.5 py-0.5 font-mono text-2xs text-ink"
          >
            <option value="all">all sources</option>
            <option value="expert">expert</option>
            <option value="policy_trace">policy trace</option>
          </select>
        </span>
      }
      pad={false}
    >
      {episodes.length === 0 ? (
        <EmptyState>no episodes indexed</EmptyState>
      ) : (
        <table className="w-full text-left font-mono text-2xs">
          <thead>
            <tr className="border-b border-line-2 text-faint">
              {['episode', 'source', 'adapter', 'seed', 'role', 'frames', 'strict', 'max lift (m)', 'video'].map(
                (h) => (
                  <th key={h} className="cap px-3 py-2 font-normal">
                    {h}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {episodes.map((episode) => (
              <tr key={episode.id} className="border-b border-line-2/50 hover:bg-panel-2/60">
                <td className="px-3 py-1.5">
                  <Link to={`/episodes/${episode.id}`} className="text-cyan hover:underline">
                    {episode.id.split('/')[1].slice(0, 34)}
                  </Link>
                </td>
                <td className="px-3 py-1.5">
                  <Tag tone={episode.source === 'expert' ? 'green' : 'violet'}>
                    {episode.source === 'expert' ? 'expert' : 'policy'}
                  </Tag>
                </td>
                <td className="px-3 py-1.5 text-dim">{episode.adapter_id ?? '—'}</td>
                <td className="px-3 py-1.5">{episode.seed ?? '—'}</td>
                <td className="px-3 py-1.5 text-dim">{episode.seed_role ?? '—'}</td>
                <td className="px-3 py-1.5">{episode.frame_count ?? '—'}</td>
                <td className="px-3 py-1.5">
                  <PassFail value={strictOf(episode)} />
                </td>
                <td className="px-3 py-1.5 text-dim">{sci(episode.maximum_anchor_lift_m)}</td>
                <td className="px-3 py-1.5">
                  {episode.mirror_video ? <Tag tone="cyan">mp4</Tag> : <span className="text-faint">—</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Panel>
  )
}
