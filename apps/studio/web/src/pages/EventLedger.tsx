import { useEffect, useMemo, useState } from 'react'
import { api, usePoll } from '../api/client'
import type { StudioDocument, StudioDocumentKind, StudioEvent } from '../api/types'
import MarkdownDocument from '../components/MarkdownDocument'
import NativeDiagnostics from '../components/NativeDiagnostics'
import { EmptyState, ErrorState, Hash, Led, Panel, PassFail, Tag } from '../components/ui'

const KIND_META: Record<
  StudioDocumentKind,
  { label: string; shortLabel: string; tone: string; pip: string }
> = {
  briefs: { label: 'Briefs', shortLabel: 'brief', tone: 'cyan', pip: 'event-pip-cyan' },
  'reviewer-messages': {
    label: 'Reviews',
    shortLabel: 'review',
    tone: 'violet',
    pip: 'event-pip-violet',
  },
  'session-logs': {
    label: 'Sessions',
    shortLabel: 'session',
    tone: 'green',
    pip: 'event-pip-green',
  },
  'manager-log': {
    label: 'Manager',
    shortLabel: 'manager',
    tone: 'amber',
    pip: 'event-pip-amber',
  },
}

const FILTERS = ['all', 'briefs', 'reviewer-messages', 'session-logs', 'manager-log'] as const
const EMPTY_EVENTS: StudioEvent[] = []
type EventFilter = (typeof FILTERS)[number]
type InspectorView = 'rendered' | 'raw'

function formatObserved(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'unknown'
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}

function formatBytes(value: number): string {
  if (value < 1024) return `${value} B`
  return `${(value / 1024).toFixed(1)} KiB`
}

function EventRow({
  event,
  selected,
  onSelect,
}: {
  event: StudioEvent
  selected: boolean
  onSelect: () => void
}) {
  const meta = KIND_META[event.kind]
  return (
    <button
      type="button"
      className="event-row group w-full text-left"
      data-selected={selected}
      onClick={onSelect}
      aria-pressed={selected}
    >
      <span className={`event-pip ${meta.pip}`} aria-hidden />
      <span className="min-w-0 border-b border-line-2/60 py-3 pr-3">
        <span className="flex items-center gap-2">
          <Tag tone={meta.tone}>{meta.shortLabel}</Tag>
          <span className="cap tabular text-faint">#{String(event.sequence).padStart(3, '0')}</span>
          <span className="ml-auto font-mono text-3xs tabular text-faint">
            {formatObserved(event.observed_at)}
          </span>
        </span>
        <span className="mt-1.5 block font-display text-sm leading-snug font-semibold text-ink group-hover:text-cyan">
          {event.title}
        </span>
        {event.decision && (
          <span className="mt-1.5 block truncate font-mono text-3xs text-dim">
            decision · {event.decision}
          </span>
        )}
      </span>
    </button>
  )
}

export default function EventLedger() {
  const { data, error, syncedAt, refresh } = usePoll(
    (signal) => api.events(1000, signal),
    5000,
  )
  const [filter, setFilter] = useState<EventFilter>('all')
  const [query, setQuery] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [view, setView] = useState<InspectorView>('rendered')
  const [document, setDocument] = useState<StudioDocument | null>(null)
  const [documentError, setDocumentError] = useState<Error | null>(null)
  const [documentLoading, setDocumentLoading] = useState(false)

  const events = data?.events ?? EMPTY_EVENTS
  const counts = useMemo(() => {
    const byKind: Record<StudioDocumentKind, number> = {
      briefs: 0,
      'reviewer-messages': 0,
      'session-logs': 0,
      'manager-log': 0,
    }
    for (const event of events) byKind[event.kind] += 1
    return byKind
  }, [events])

  const visibleEvents = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return events.filter((event) => {
      if (filter !== 'all' && event.kind !== filter) return false
      if (!needle) return true
      return [event.title, event.filename, event.source, event.decision ?? ''].some((value) =>
        value.toLowerCase().includes(needle),
      )
    })
  }, [events, filter, query])

  const selectedEvent =
    visibleEvents.find((event) => event.id === selectedId) ?? visibleEvents[0] ?? null
  const selectedKind = selectedEvent?.kind
  const selectedFilename = selectedEvent?.filename
  const selectedSha256 = selectedEvent?.sha256

  useEffect(() => {
    const controller = new AbortController()
    if (!selectedKind || !selectedFilename) {
      setDocument(null)
      setDocumentError(null)
      setDocumentLoading(false)
      return () => controller.abort()
    }
    setDocument(null)
    setDocumentError(null)
    setDocumentLoading(true)
    void api
      .document(selectedKind, selectedFilename, controller.signal)
      .then((payload) => {
        setDocument(payload)
        setDocumentError(null)
      })
      .catch((requestError: unknown) => {
        if (requestError instanceof DOMException && requestError.name === 'AbortError') return
        setDocumentError(
          requestError instanceof Error ? requestError : new Error(String(requestError)),
        )
      })
      .finally(() => {
        if (!controller.signal.aborted) setDocumentLoading(false)
    })
    return () => controller.abort()
  }, [selectedFilename, selectedKind, selectedSha256])

  if (error && !data) return <ErrorState error={error} />

  const hashMatches = document && selectedEvent ? document.sha256 === selectedEvent.sha256 : null

  return (
    <div className="space-y-3">
      <header className="flex flex-col gap-3 border-b border-line pb-3 xl:flex-row xl:items-end">
        <div>
          <p className="cap text-amber">canonical workflow documents</p>
          <h1 className="mt-1 font-display text-3xl font-bold tracking-tight text-ink">
            Event ledger <span className="text-faint">/</span> inspector
          </h1>
          <p className="mt-1 max-w-3xl text-2xs leading-relaxed text-dim">
            Observed chronology only. Source text and hashes are preserved; this view grants no
            authority and does not reinterpret evidence.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2 xl:ml-auto">
          <Tag tone="amber">{data?.total ?? 0} indexed</Tag>
          <Tag tone="cyan">{data?.count ?? 0} loaded</Tag>
          <span className="flex items-center gap-2 border border-line-2 bg-inset px-2 py-1">
            <Led tone={error ? 'red' : 'green'} pulse={!error} />
            <span className="cap">
              {syncedAt ? `observed ${formatObserved(new Date(syncedAt).toISOString())}` : 'acquiring'}
            </span>
          </span>
          <button type="button" className="btn btn-quiet" onClick={refresh}>
            refresh
          </button>
        </div>
      </header>

      {error && <ErrorState error={error} />}
      <NativeDiagnostics />

      <div className="grid gap-3 xl:grid-cols-[minmax(21rem,0.9fr)_minmax(0,1.5fr)]">
        <Panel
          title="evidence rail"
          right={<span className="cap text-faint">{visibleEvents.length} visible</span>}
          pad={false}
        >
          <div className="space-y-2 border-b border-line p-2.5">
            <label className="block">
              <span className="sr-only">Search workflow events</span>
              <input
                className="field"
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="search title, decision, source…"
              />
            </label>
            <div className="flex flex-wrap gap-1" aria-label="Event kind filters">
              {FILTERS.map((kind) => {
                const active = filter === kind
                const label = kind === 'all' ? 'All' : KIND_META[kind].label
                const count = kind === 'all' ? events.length : counts[kind]
                return (
                  <button
                    key={kind}
                    type="button"
                    className={`btn ${active ? 'btn-primary' : 'btn-quiet'}`}
                    onClick={() => setFilter(kind)}
                    aria-pressed={active}
                  >
                    {label} <span className="ml-1 opacity-60">{count}</span>
                  </button>
                )
              })}
            </div>
          </div>
          <div className="event-rail max-h-[calc(100vh-19rem)] min-h-[30rem] overflow-y-auto">
            {visibleEvents.length === 0 ? (
              <EmptyState>no events match this view</EmptyState>
            ) : (
              visibleEvents.map((event) => (
                <EventRow
                  key={event.id}
                  event={event}
                  selected={event.id === selectedEvent?.id}
                  onSelect={() => setSelectedId(event.id)}
                />
              ))
            )}
          </div>
        </Panel>

        <Panel
          title="source inspector"
          right={
            <span className="flex items-center gap-1">
              {(['rendered', 'raw'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  className={`btn ${view === mode ? 'btn-primary' : 'btn-quiet'}`}
                  onClick={() => setView(mode)}
                  aria-pressed={view === mode}
                >
                  {mode}
                </button>
              ))}
            </span>
          }
          pad={false}
        >
          {!selectedEvent ? (
            <EmptyState>select an event to inspect its source</EmptyState>
          ) : (
            <div>
              <div className="border-b border-line bg-inset p-3">
                <div className="flex flex-wrap items-start gap-2">
                  <Tag tone={KIND_META[selectedEvent.kind].tone}>
                    {KIND_META[selectedEvent.kind].shortLabel} {selectedEvent.sequence}
                  </Tag>
                  {selectedEvent.recorded_date && (
                    <Tag tone="dim">recorded {selectedEvent.recorded_date}</Tag>
                  )}
                  {selectedEvent.decision && <Tag tone="amber">{selectedEvent.decision}</Tag>}
                </div>
                <h2 className="mt-2 font-display text-xl leading-tight font-semibold text-ink">
                  {selectedEvent.title}
                </h2>
                <div className="mt-3 grid gap-3 border-t border-line-2 pt-3 sm:grid-cols-2 2xl:grid-cols-4">
                  <div className="min-w-0">
                    <p className="cap">canonical source</p>
                    <p className="mt-1 truncate font-mono text-2xs text-cyan" title={selectedEvent.source}>
                      {selectedEvent.source}
                    </p>
                  </div>
                  <div>
                    <p className="cap">sha256</p>
                    <p className="mt-1"><Hash value={selectedEvent.sha256} /></p>
                  </div>
                  <div>
                    <p className="cap">index → open</p>
                    <p className="mt-1"><PassFail value={hashMatches} /></p>
                  </div>
                  <div>
                    <p className="cap">observed / size</p>
                    <p className="mt-1 font-mono text-2xs text-dim">
                      {formatObserved(selectedEvent.observed_at)} · {formatBytes(selectedEvent.bytes)}
                    </p>
                  </div>
                </div>
              </div>

              <div className="max-h-[calc(100vh-22rem)] min-h-[27rem] overflow-auto p-5">
                {documentError ? (
                  <ErrorState error={documentError} />
                ) : documentLoading || !document ? (
                  <div className="flex items-center justify-center gap-2 py-16">
                    <Led tone="cyan" pulse />
                    <span className="cap">opening canonical source</span>
                  </div>
                ) : view === 'rendered' ? (
                  <MarkdownDocument content={document.content} />
                ) : (
                  <pre className="overflow-x-auto whitespace-pre-wrap font-mono text-2xs leading-relaxed text-ink">
                    {document.content}
                  </pre>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </div>
  )
}
