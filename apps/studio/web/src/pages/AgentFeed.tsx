import { useStatus } from '../state/StatusContext'
import { EmptyState, ErrorState, Panel, Tag } from '../components/ui'
import { parseDocName } from '../lib/format'

function FeedList({ names, tone, kind }: { names: string[]; tone: string; kind: string }) {
  if (names.length === 0) return <EmptyState>none yet</EmptyState>
  return (
    <ul className="flex flex-col">
      {names.map((name) => {
        const { id, title } = parseDocName(name)
        return (
          <li key={name} className="flex items-baseline gap-2 border-b border-line-2/50 px-1 py-2">
            <Tag tone={tone}>
              {kind} {id}
            </Tag>
            <span className="font-mono text-2xs text-ink">{title}</span>
          </li>
        )
      })}
    </ul>
  )
}

export default function AgentFeed() {
  const { data, error } = useStatus()
  if (error && !data) return <ErrorState error={error} />
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <Panel title="latest briefs · executor" pad={false}>
        <FeedList names={data?.recent_briefs ?? []} tone="cyan" kind="brief" />
      </Panel>
      <Panel title="latest reviewer decisions" pad={false}>
        <FeedList names={data?.recent_reviewer_decisions ?? []} tone="violet" kind="rev" />
      </Panel>
      <Panel title="run state" className="md:col-span-2">
        <p className="font-mono text-2xs leading-relaxed text-dim">{data?.ledger.run_state ?? '—'}</p>
        <p className="cap mt-2">next step</p>
        <p className="font-mono text-2xs leading-relaxed text-ink">{data?.ledger.next_step ?? '—'}</p>
      </Panel>
    </div>
  )
}
