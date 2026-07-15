import { Link } from 'react-router-dom'
import { useStatus } from '../state/StatusContext'
import { useNow } from '../lib/useNow'
import { countdownTo, fmtCountdown, fmtLocal, parseDocName, shortHash } from '../lib/format'
import { EmptyState, ErrorState, KV, Led, Panel } from '../components/ui'
import type { RunWindow } from '../api/types'

function CountdownBlock({ label, iso, now }: { label: string; iso: string; now: number }) {
  const parts = countdownTo(iso, now)
  const tone = parts.negative
    ? 'text-red'
    : parts.totalMs < 60 * 60 * 1000
      ? 'text-amber-hot'
      : 'text-ink'
  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="cap">{label}</span>
      <span className={`tabular font-mono text-[28px] leading-none font-semibold ${tone}`}>
        {fmtCountdown(parts)}
      </span>
      <span className="text-3xs text-faint">
        {parts.negative ? 'elapsed since' : 'until'} {fmtLocal(iso)}
      </span>
    </div>
  )
}

function WindowBar({ window, now }: { window: RunWindow; now: number }) {
  const start = new Date(window.actual_start).getTime()
  const cutoff = new Date(window.no_new_major_slice_after).getTime()
  const end = new Date(window.hard_closeout).getTime()
  const span = end - start
  if (!(span > 0)) return null
  const pct = Math.min(100, Math.max(0, ((now - start) / span) * 100))
  const cutoffPct = ((cutoff - start) / span) * 100
  return (
    <div className="mt-3">
      <div className="relative h-2 border border-line-2 bg-inset">
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber/50 to-amber"
          style={{ width: `${pct}%` }}
        />
        <div
          className="absolute inset-y-[-3px] w-px bg-red"
          style={{ left: `${cutoffPct}%` }}
          title={`no new major slice after ${fmtLocal(window.no_new_major_slice_after)}`}
        />
      </div>
      <div className="mt-1 flex justify-between text-3xs text-faint">
        <span>start {fmtLocal(window.actual_start)}</span>
        <span>
          window {pct.toFixed(1)}% elapsed · {window.total_duration_hours ?? '—'}h total
        </span>
        <span>closeout {fmtLocal(window.hard_closeout)}</span>
      </div>
    </div>
  )
}

function AuthorityChips({ window }: { window: RunWindow }) {
  const closed = (v: string | undefined) => (v ?? '').toLowerCase().includes('closed')
  const items: Array<{ label: string; ok: boolean; text: string }> = [
    {
      label: 'simulation only',
      ok: window.simulation_only === true,
      text: window.simulation_only ? 'enforced' : 'unknown',
    },
    { label: 'hardware', ok: closed(window.hardware_authority), text: window.hardware_authority ?? '—' },
    {
      label: 'ext compute',
      ok: closed(window.external_compute_authority),
      text: window.external_compute_authority ?? '—',
    },
    { label: 'brev', ok: closed(window.brev_authority), text: window.brev_authority ?? '—' },
  ]
  return (
    <div className="mt-3 grid grid-cols-2 gap-2 lg:grid-cols-4">
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-2 border border-line bg-inset px-2 py-1.5">
          <Led tone={item.ok ? 'green' : 'red'} />
          <div className="min-w-0 leading-tight">
            <div className="cap">{item.label}</div>
            <div className="truncate font-mono text-3xs text-dim">{item.text}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function DocList({
  title,
  tone,
  names,
}: {
  title: string
  tone: 'amber' | 'cyan'
  names: string[]
}) {
  return (
    <Panel
      title={title}
      right={
        <Link to="/feed" className="cap text-faint hover:text-amber">
          feed →
        </Link>
      }
      pad={false}
    >
      {names.length === 0 ? (
        <EmptyState>no documents indexed</EmptyState>
      ) : (
        <ul>
          {names.map((name) => {
            const doc = parseDocName(name)
            return (
              <li
                key={name}
                className="flex items-baseline gap-3 border-b border-line/60 px-3 py-2 last:border-b-0 hover:bg-panel-2"
                title={name}
              >
                <span
                  className={`tabular w-9 flex-none text-right font-mono text-xs font-semibold ${tone === 'amber' ? 'text-amber' : 'text-cyan'}`}
                >
                  #{doc.id}
                </span>
                <span className="min-w-0 truncate text-xs text-ink">{doc.title}</span>
              </li>
            )
          })}
        </ul>
      )}
    </Panel>
  )
}

export default function Dashboard() {
  const { data: status, error, syncedAt } = useStatus()
  const now = useNow(1000)

  if (!status && error) return <ErrorState error={error} />
  if (!status)
    return (
      <div className="flex items-center gap-2 py-16 justify-center">
        <Led tone="amber" pulse />
        <span className="cap">acquiring loop telemetry…</span>
      </div>
    )

  const ledger = status.ledger ?? {}
  const boundary = status.latest_verified_boundary
  const blockersRaised = !!ledger.blockers && !/^(none|no\b|—|n\/a)/i.test(ledger.blockers.trim())

  return (
    <div className="space-y-4">
      {/* row 1: slice + window */}
      <div className="grid grid-cols-12 gap-4">
        <Panel title="Current slice" className="col-span-12 xl:col-span-5">
          <div className="font-display text-[44px] leading-none font-bold tracking-tight text-amber">
            {status.current_task ?? '——'}
          </div>
          <div className="mt-2 text-xs text-dim">{status.current_milestone ?? '—'}</div>
          <div className="mt-4 border-t border-line pt-3">
            <span className="cap">latest verified boundary</span>
            {boundary ? (
              <div className="mt-2 grid grid-cols-3 gap-3">
                <KV label="brief">#{boundary.brief_id ?? '—'}</KV>
                <KV label="decision">#{boundary.reviewer_decision_id ?? '—'}</KV>
                <KV label="commit">{shortHash(boundary.commit, 10)}</KV>
                <div className="col-span-3">
                  <KV label="summary">{boundary.summary ?? '—'}</KV>
                </div>
              </div>
            ) : (
              <div className="mt-2 text-xs text-faint">none recorded</div>
            )}
          </div>
        </Panel>

        <Panel
          title="Run window"
          className="col-span-12 xl:col-span-7"
          right={
            <span className="cap text-faint">
              synced {syncedAt ? `${Math.max(0, Math.round((now - syncedAt) / 1000))}s ago` : '—'}
            </span>
          }
        >
          {status.run_window ? (
            <>
              <div className="grid grid-cols-2 gap-6">
                <CountdownBlock
                  label="No new major slice"
                  iso={status.run_window.no_new_major_slice_after}
                  now={now}
                />
                <CountdownBlock label="Hard closeout" iso={status.run_window.hard_closeout} now={now} />
              </div>
              <WindowBar window={status.run_window} now={now} />
              <AuthorityChips window={status.run_window} />
            </>
          ) : (
            <EmptyState>no run window recorded</EmptyState>
          )}
        </Panel>
      </div>

      {/* row 2: ledger state */}
      <div className="grid grid-cols-12 gap-4">
        <Panel title="Run state" className="col-span-12 xl:col-span-7">
          <p className="text-xs leading-relaxed text-ink">{ledger.run_state ?? '—'}</p>
          {ledger.training_lock && (
            <p className="mt-3 border-t border-line pt-2 text-2xs text-dim">
              <span className="cap mr-2 text-faint">training lock</span>
              {ledger.training_lock}
            </p>
          )}
        </Panel>
        <div className="col-span-12 flex flex-col gap-4 xl:col-span-5">
          <Panel title="Next step">
            <p className="text-xs leading-relaxed text-ink">{ledger.next_step ?? '—'}</p>
          </Panel>
          <Panel
            title="Blockers"
            right={<Led tone={blockersRaised ? 'red' : 'green'} pulse={blockersRaised} />}
          >
            <p className={`text-xs leading-relaxed ${blockersRaised ? 'text-red' : 'text-dim'}`}>
              {ledger.blockers ?? 'none recorded'}
            </p>
          </Panel>
        </div>
      </div>

      {/* row 3: recent documents */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 xl:col-span-6">
          <DocList title="Recent briefs" tone="amber" names={status.recent_briefs ?? []} />
        </div>
        <div className="col-span-12 xl:col-span-6">
          <DocList
            title="Reviewer decisions"
            tone="cyan"
            names={status.recent_reviewer_decisions ?? []}
          />
        </div>
      </div>

      {error && <ErrorState error={error} />}
    </div>
  )
}
