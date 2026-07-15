import type { ReactNode } from 'react'

export function Panel({
  title,
  right,
  children,
  className = '',
  pad = true,
}: {
  title?: ReactNode
  right?: ReactNode
  children: ReactNode
  className?: string
  pad?: boolean
}) {
  return (
    <section className={`panel ${className}`}>
      {title !== undefined && (
        <header className="panel-head">
          <span className="cap text-ink">{title}</span>
          {right !== undefined && <span className="ml-auto flex items-center gap-2">{right}</span>}
        </header>
      )}
      <div className={pad ? 'p-3' : ''}>{children}</div>
    </section>
  )
}

export type LedTone = 'green' | 'red' | 'amber' | 'cyan' | 'off'

export function Led({ tone, pulse = false }: { tone: LedTone; pulse?: boolean }) {
  const toneClass = tone === 'off' ? '' : `led-${tone}`
  return <span className={`led ${toneClass} ${pulse ? 'led-pulse' : ''}`} aria-hidden />
}

const TAG_TONES: Record<string, string> = {
  amber: 'text-amber border-amber/40 bg-amber/10',
  cyan: 'text-cyan border-cyan/40 bg-cyan/10',
  green: 'text-green border-green/40 bg-green/10',
  red: 'text-red border-red/40 bg-red/10',
  violet: 'text-violet border-violet/40 bg-violet/10',
  dim: 'text-dim border-line-2 bg-panel-2',
}

export function Tag({ tone = 'dim', children }: { tone?: string; children: ReactNode }) {
  return (
    <span
      className={`inline-flex items-center border px-1.5 py-px text-3xs font-medium uppercase tracking-cap ${TAG_TONES[tone] ?? TAG_TONES.dim}`}
    >
      {children}
    </span>
  )
}

export function PassFail({ value }: { value: boolean | null | undefined }) {
  if (value === null || value === undefined) return <Tag tone="dim">n/a</Tag>
  return value ? <Tag tone="green">pass</Tag> : <Tag tone="red">fail</Tag>
}

export function KV({
  label,
  children,
  mono = true,
}: {
  label: string
  children: ReactNode
  mono?: boolean
}) {
  return (
    <div className="flex min-w-0 flex-col gap-0.5">
      <span className="cap">{label}</span>
      <span className={`${mono ? 'font-mono' : 'font-display'} text-xs break-words text-ink`}>
        {children}
      </span>
    </div>
  )
}

export function Hash({ value }: { value: string | null | undefined }) {
  if (!value) return <span className="text-faint">—</span>
  return (
    <button
      type="button"
      title={`${value}\n(click to copy)`}
      onClick={() => void navigator.clipboard?.writeText(value)}
      className="cursor-pointer font-mono text-2xs text-cyan/90 hover:text-cyan hover:underline decoration-cyan/40"
    >
      {value.slice(0, 12)}…
    </button>
  )
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-1 py-10 text-center">
      <span className="text-faint text-lg">▚▚</span>
      <span className="cap">{children}</span>
    </div>
  )
}

export function ErrorState({ error }: { error: Error }) {
  return (
    <div className="panel border-red/40 p-3">
      <div className="flex items-center gap-2">
        <Led tone="red" pulse />
        <span className="cap text-red">link fault</span>
      </div>
      <p className="mt-1 font-mono text-2xs text-dim break-all">{error.message}</p>
    </div>
  )
}
