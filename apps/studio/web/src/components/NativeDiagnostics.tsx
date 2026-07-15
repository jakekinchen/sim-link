import { invoke, isTauri } from '@tauri-apps/api/core'
import { listen, type UnlistenFn } from '@tauri-apps/api/event'
import { useEffect, useState } from 'react'
import { Led, Panel, Tag, type LedTone } from './ui'

interface BackendLogEntry {
  atMs: number
  stream: string
  message: string
}

interface BackendDiagnostics {
  runtime: 'native'
  state: 'booting' | 'starting' | 'ready' | 'fault' | 'stopped'
  pid: number | null
  exitCode: number | null
  signal: number | null
  logs: BackendLogEntry[]
}

function stateTone(state: BackendDiagnostics['state']): LedTone {
  if (state === 'ready') return 'green'
  if (state === 'fault') return 'red'
  if (state === 'stopped') return 'off'
  return 'amber'
}

function logTime(atMs: number): string {
  const date = new Date(atMs)
  if (Number.isNaN(date.getTime())) return '--:--:--'
  return date.toLocaleTimeString([], { hour12: false })
}

export default function NativeDiagnostics() {
  const native = isTauri()
  const [diagnostics, setDiagnostics] = useState<BackendDiagnostics | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [expanded, setExpanded] = useState(false)

  useEffect(() => {
    if (!native) return
    let disposed = false
    let unlisten: UnlistenFn | undefined

    const connect = async () => {
      try {
        unlisten = await listen<BackendDiagnostics>('studio-backend-diagnostics', (event) => {
          if (!disposed) setDiagnostics(event.payload)
        })
        const snapshot = await invoke<BackendDiagnostics>('native_diagnostics')
        if (!disposed) {
          setDiagnostics(snapshot)
          setError(null)
        }
      } catch (connectError) {
        if (!disposed) {
          setError(
            connectError instanceof Error ? connectError : new Error(String(connectError)),
          )
        }
      }
    }

    void connect()
    return () => {
      disposed = true
      unlisten?.()
    }
  }, [native])

  if (!native) {
    return (
      <div className="flex flex-wrap items-center gap-2 border border-line bg-panel px-3 py-2">
        <Tag tone="dim">web preview</Tag>
        <span className="cap text-faint">
          native sidecar lifecycle and logs appear here in the Mac app
        </span>
        <span className="cap ml-auto text-faint">operational diagnostics · not evidence</span>
      </div>
    )
  }

  const state = error ? 'fault' : (diagnostics?.state ?? 'booting')
  const logs = diagnostics?.logs ?? []
  return (
    <Panel
      title={
        <span className="flex items-center gap-2">
          <Led tone={stateTone(state)} pulse={state === 'booting' || state === 'starting'} />
          native backend · <span className={state === 'fault' ? 'text-red' : 'text-ink'}>{state}</span>
        </span>
      }
      right={
        <span className="flex items-center gap-2">
          {diagnostics?.pid && <Tag tone="dim">pid {diagnostics.pid}</Tag>}
          {diagnostics?.exitCode !== null && diagnostics?.exitCode !== undefined && (
            <Tag tone={diagnostics.exitCode === 0 ? 'green' : 'red'}>
              exit {diagnostics.exitCode}
            </Tag>
          )}
          <button
            type="button"
            className="btn btn-quiet"
            onClick={() => setExpanded((value) => !value)}
            aria-expanded={expanded}
          >
            {expanded ? 'hide logs' : `logs ${logs.length}`}
          </button>
        </span>
      }
      pad={false}
    >
      <div className="flex flex-wrap items-center gap-2 px-3 py-2">
        <span className="cap text-faint">loopback 127.0.0.1:8321</span>
        <span className="cap text-faint">operational diagnostics · not repository evidence</span>
        {diagnostics?.signal !== null && diagnostics?.signal !== undefined && (
          <Tag tone="red">signal {diagnostics.signal}</Tag>
        )}
        {error && <span className="font-mono text-3xs text-red">{error.message}</span>}
      </div>
      {expanded && (
        <div className="max-h-48 overflow-auto border-t border-line bg-bg px-3 py-2" role="log">
          {logs.length === 0 ? (
            <p className="cap py-3 text-faint">no sidecar output captured yet</p>
          ) : (
            logs.map((entry, index) => (
              <p
                key={`${entry.atMs}-${index}`}
                className={`grid grid-cols-[4.5rem_4rem_minmax(0,1fr)] gap-2 font-mono text-3xs leading-relaxed ${
                  entry.stream === 'error' ? 'text-red' : 'text-dim'
                }`}
              >
                <span className="tabular text-faint">{logTime(entry.atMs)}</span>
                <span className="uppercase text-faint">{entry.stream}</span>
                <span className="break-all">{entry.message}</span>
              </p>
            ))
          )}
        </div>
      )}
    </Panel>
  )
}
