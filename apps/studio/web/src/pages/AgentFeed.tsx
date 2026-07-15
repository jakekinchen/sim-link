import { useEffect, useState } from 'react'
import { api } from '../api/client'
import type { StudioDocument, StudioDocumentKind } from '../api/types'
import MarkdownDocument from '../components/MarkdownDocument'
import { EmptyState, ErrorState, Led, Panel, Tag } from '../components/ui'
import { parseDocName } from '../lib/format'
import { useStatus } from '../state/StatusContext'

function DocumentFeed({
  names,
  kind,
  tone,
  role,
}: {
  names: string[]
  kind: StudioDocumentKind
  tone: string
  role: string
}) {
  const namesKey = names.join('\u0000')
  const [documents, setDocuments] = useState<StudioDocument[]>([])
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    const requestedNames = namesKey ? namesKey.split('\u0000') : []
    if (requestedNames.length === 0) {
      setDocuments([])
      setError(null)
      setLoading(false)
      return () => controller.abort()
    }
    setLoading(true)
    void Promise.all(requestedNames.map((name) => api.document(kind, name, controller.signal)))
      .then((payloads) => {
        setDocuments(payloads)
        setError(null)
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setError(requestError instanceof Error ? requestError : new Error(String(requestError)))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [kind, namesKey])

  if (names.length === 0) return <EmptyState>none yet</EmptyState>
  if (error) return <ErrorState error={error} />
  if (loading && documents.length === 0) {
    return (
      <div className="flex items-center gap-2 p-3">
        <Led tone="cyan" pulse />
        <span className="cap">loading signed document text</span>
      </div>
    )
  }

  return (
    <div>
      {documents.map((document, index) => {
        const { id, title } = parseDocName(document.filename)
        return (
          <details key={document.filename} className="group border-b border-line" open={index === 0}>
            <summary className="flex cursor-pointer list-none items-center gap-2 px-3 py-2 hover:bg-panel-2 focus-visible:outline-1 focus-visible:outline-cyan">
              <span className="text-faint transition-transform group-open:rotate-90">▸</span>
              <Tag tone={tone}>
                {role} {id}
              </Tag>
              <span className="min-w-0 truncate font-mono text-2xs text-ink">{title}</span>
            </summary>
            <div className="border-t border-line-2/60 bg-inset px-4 py-4">
              <MarkdownDocument content={document.content} />
              <p className="cap mt-5 border-t border-line-2 pt-2 text-faint">
                source · {document.filename}
              </p>
            </div>
          </details>
        )
      })}
    </div>
  )
}

export default function AgentFeed() {
  const { data, error } = useStatus()
  if (error && !data) return <ErrorState error={error} />
  return (
    <div className="grid gap-3 xl:grid-cols-2">
      <Panel title="latest briefs · executor" pad={false}>
        <DocumentFeed
          names={data?.recent_briefs ?? []}
          kind="briefs"
          tone="cyan"
          role="brief"
        />
      </Panel>
      <Panel title="latest reviewer decisions" pad={false}>
        <DocumentFeed
          names={data?.recent_reviewer_decisions ?? []}
          kind="reviewer-messages"
          tone="violet"
          role="review"
        />
      </Panel>
      <Panel title="latest session logs" pad={false}>
        <DocumentFeed
          names={data?.recent_session_logs ?? []}
          kind="session-logs"
          tone="green"
          role="session"
        />
      </Panel>
      <Panel title="latest manager interventions" pad={false}>
        <DocumentFeed
          names={data?.recent_manager_interventions ?? []}
          kind="manager-log"
          tone="amber"
          role="manager"
        />
      </Panel>
      <Panel title="run state" className="xl:col-span-2">
        <p className="font-mono text-2xs leading-relaxed text-dim">{data?.ledger.run_state ?? '—'}</p>
        <p className="cap mt-2">next step</p>
        <p className="font-mono text-2xs leading-relaxed text-ink">{data?.ledger.next_step ?? '—'}</p>
      </Panel>
    </div>
  )
}
