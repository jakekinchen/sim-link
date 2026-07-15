import type { ReactNode } from 'react'

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

export default function MarkdownDocument({ content }: { content: string }) {
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
        while (index < lines.length && lines[index].trim() && !startsMarkdownBlock(lines[index])) {
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
        while (index < lines.length && lines[index].trim() && !startsMarkdownBlock(lines[index])) {
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
