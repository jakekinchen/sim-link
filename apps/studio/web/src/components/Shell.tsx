import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useStatus } from '../state/StatusContext'
import { fmtClock } from '../lib/format'
import { Led } from './ui'

const NAV = [
  { to: '/', label: 'Dashboard', code: '01' },
  { to: '/episodes', label: 'Episodes', code: '02' },
  { to: '/tasks', label: 'Tasks', code: '03' },
  { to: '/workcells', label: 'Workcells', code: '04' },
  { to: '/feed', label: 'Agent Feed', code: '05' },
  { to: '/robot', label: 'Robot', code: '06' },
]

function SessionClock() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return <span className="tabular font-mono text-xs text-ink">{fmtClock(now)}</span>
}

export default function Shell() {
  const { data: status, error, syncedAt } = useStatus()
  const linkUp = !error && syncedAt !== null

  return (
    <div className="flex min-h-screen">
      {/* left rail */}
      <aside className="fixed inset-y-0 left-0 z-20 flex w-52 flex-col border-r border-line bg-panel/80 backdrop-blur-sm">
        <div className="border-b border-line px-4 py-4">
          <div className="flex items-center gap-2">
            <span className="grid size-7 flex-none grid-cols-2 gap-px" aria-hidden>
              <span className="bg-amber" />
              <span className="border border-line-2" />
              <span className="border border-line-2" />
              <span className="bg-cyan" />
            </span>
            <div className="leading-tight">
              <div className="font-display text-sm font-bold tracking-wide2 text-ink uppercase">
                SceneSmith
              </div>
              <div className="cap text-amber">Studio // Foundry</div>
            </div>
          </div>
        </div>

        <nav className="flex flex-col gap-px p-2">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `group flex items-center gap-2.5 border-l-2 px-3 py-2 font-mono text-xs transition-colors ${
                  isActive
                    ? 'border-amber bg-amber/10 text-amber'
                    : 'border-transparent text-dim hover:bg-panel-2 hover:text-ink'
                }`
              }
            >
              <span className="text-3xs text-faint group-[.active]:text-amber/70">{item.code}</span>
              <span className="tracking-wide2 uppercase">{item.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="mt-auto space-y-2 border-t border-line px-4 py-3">
          <div className="flex items-center gap-2">
            <Led tone={linkUp ? 'green' : 'red'} pulse />
            <span className="cap">{linkUp ? 'api link up' : 'api link down'}</span>
          </div>
          <p className="font-mono text-3xs leading-snug break-all text-faint">
            {status?.data_root ?? 'awaiting first sync…'}
          </p>
        </div>
      </aside>

      {/* main column */}
      <div className="ml-52 flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-11 items-center gap-4 border-b border-line bg-bg/90 px-5 backdrop-blur-sm">
          <span className="cap">
            slice{' '}
            <span className="ml-1 font-semibold text-amber">{status?.current_task ?? '——'}</span>
          </span>
          <span className="hidden truncate text-2xs text-dim md:inline">
            {status?.current_milestone ?? ''}
          </span>
          <span className="ml-auto flex items-center gap-4">
            <span className="cap hidden lg:inline">
              sim-only{' '}
              <span className={status?.run_window?.simulation_only ? 'text-green' : 'text-red'}>
                {status?.run_window?.simulation_only ? 'yes' : '??'}
              </span>
            </span>
            <span className="flex items-center gap-2">
              <Led tone={linkUp ? 'amber' : 'off'} pulse={linkUp} />
              <SessionClock />
            </span>
          </span>
        </header>

        <main className="min-w-0 flex-1 p-5" style={{ animation: 'rise-in 240ms ease-out' }}>
          <Outlet />
        </main>

        <footer className="flex items-center gap-3 border-t border-line px-5 py-2">
          <span className="cap">SceneSmith Studio v0</span>
          <span className="text-3xs text-faint">
            read-only artifact console — the repository is the source of truth
          </span>
          <span
            className="ml-auto inline-block h-3 w-1.5 bg-amber"
            style={{ animation: 'blink-cursor 1.2s step-end infinite' }}
            aria-hidden
          />
        </footer>
      </div>
    </div>
  )
}
