import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { StudioDocument, StudioDocumentKind } from '../api/types'
import { EmptyState, ErrorState, Led, Panel, Tag } from '../components/ui'
import { parseDocName } from '../lib/format'
import { useStatus } from '../state/StatusContext'

function inlineMarkdown(text: string): ReactNode[] {
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g)
  return tokens.filter(Boolean).map((token, index) => {
    if (token.startsWith('**') && token.endsWith('**')) {
      return <strong key={index}>{token.slice(2, -2)}</strong>
    }
    if (token.startsWith('`') && token.endsWith('`')) {
      return <code key={index}>{token.slice(1, -1)}</code>
    }
    const link = /^\[([^\]]+)\]\(([^)]+)\)$/.exec(token)
    if (link && /^https?:\/\//.test(link[2])) {
      return (
        <a key={index} href={link[2]} target="_blank" rel="noreferrer">
          {link[1]}
        </a>
      )
    }
    return token
  })
}

function startsMarkdownBlock(line: string): boolean {
  return /^(#{1,4})\s+|^```|^[-*]\s+|^\d+\.\s+|^>\s?|^---+$/.test(line)
}

function appendSoftWrap(body: string, continuation: string): string {
  return body.endsWith('-') ? `${body}${continuation}` : `${body} ${continuation}`
}

function MarkdownDocument({ content }: { content: string }) {
  const lines = content.replace(/\r\n/g, '\n').split('\n')
  const blocks: ReactNode[] = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    if (!line.trim()) {
      index += 1
      continue
    }
    if (line.startsWith('```')) {
      const language = line.slice(3).trim()
      const code: string[] = []
      index += 1
      while (index < lines.length && !lines[index].startsWith('```')) {
        code.push(lines[index])
        index += 1
      }
      index += 1
      blocks.push(
        <pre key={`code-${index}`} data-language={language || undefined}>
          <code>{code.join('\n')}</code>
        </pre>,
      )
      continue
    }
    const heading = /^(#{1,4})\s+(.+)$/.exec(line)
    if (heading) {
      const level = heading[1].length
      const body = inlineMarkdown(heading[2])
      if (level === 1) blocks.push(<h1 key={`h-${index}`}>{body}</h1>)
      else if (level === 2) blocks.push(<h2 key={`h-${index}`}>{body}</h2>)
      else blocks.push(<h3 key={`h-${index}`}>{body}</h3>)
      index += 1
      continue
    }
    if (/^---+$/.test(line)) {
      blocks.push(<hr key={`hr-${index}`} />)
      index += 1
      continue
    }
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = []
      while (index < lines.length) {
        const item = /^[-*]\s+(.+)$/.exec(lines[index])
        if (!item) break
        let body = item[1]
        index += 1
        while (
          index < lines.length &&
          lines[index].trim() &&
          !startsMarkdownBlock(lines[index])
        ) {
          body = appendSoftWrap(body, lines[index].trim())
          index += 1
        }
        items.push(body)
      }
      blocks.push(
        <ul key={`ul-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{inlineMarkdown(item)}</li>
          ))}
        </ul>,
      )
      continue
    }
    if (/^\d+\.\s+/.test(line)) {
      const items: string[] = []
      while (index < lines.length) {
        const item = /^\d+\.\s+(.+)$/.exec(lines[index])
        if (!item) break
        let body = item[1]
        index += 1
        while (
          index < lines.length &&
          lines[index].trim() &&
          !startsMarkdownBlock(lines[index])
        ) {
          body = appendSoftWrap(body, lines[index].trim())
          index += 1
        }
        items.push(body)
      }
      blocks.push(
        <ol key={`ol-${index}`}>
          {items.map((item, itemIndex) => (
            <li key={itemIndex}>{inlineMarkdown(item)}</li>
          ))}
        </ol>,
      )
      continue
    }
    if (line.startsWith('>')) {
      const quote: string[] = []
      while (index < lines.length && lines[index].startsWith('>')) {
        quote.push(lines[index].replace(/^>\s?/, ''))
        index += 1
      }
      blocks.push(<blockquote key={`quote-${index}`}>{inlineMarkdown(quote.join(' '))}</blockquote>)
      continue
    }

    const paragraph = [line.trim()]
    index += 1
    while (index < lines.length && lines[index].trim() && !startsMarkdownBlock(lines[index])) {
      paragraph.push(lines[index].trim())
      index += 1
    }
    const body = paragraph.slice(1).reduce(appendSoftWrap, paragraph[0])
    blocks.push(<p key={`p-${index}`}>{inlineMarkdown(body)}</p>)
  }

  return <article className="studio-markdown">{blocks}</article>
}

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
      <Panel title="run state" className="xl:col-span-2">
        <p className="font-mono text-2xs leading-relaxed text-dim">{data?.ledger.run_state ?? '—'}</p>
        <p className="cap mt-2">next step</p>
        <p className="font-mono text-2xs leading-relaxed text-ink">{data?.ledger.next_step ?? '—'}</p>
      </Panel>
    </div>
  )
}
