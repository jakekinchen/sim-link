import { lazy, Suspense, useEffect, useMemo, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import { api, mediaUrl, usePoll } from '../api/client'
import type { RunWindow, StudioEvent, WorkcellManifest } from '../api/types'
import ReplayStage from '../components/ReplayStage'
import { ErrorState, Led, Tag } from '../components/ui'
import { countdownTo, fmtCountdown, fmtLocal, shortHash } from '../lib/format'
import { useNow } from '../lib/useNow'
import { useStatus } from '../state/StatusContext'

type StageMode = 'scene' | 'replay'

const WorkcellOrbit = lazy(() => import('../components/WorkcellOrbit'))

const EVENT_TONE: Record<StudioEvent['kind'], string> = {
  briefs: 'foundry-event-brief',
  'reviewer-messages': 'foundry-event-review',
  'session-logs': 'foundry-event-session',
  'manager-log': 'foundry-event-manager',
}

function ageLabel(iso: string, now: number): string {
  const elapsed = Math.max(0, now - new Date(iso).getTime())
  if (elapsed < 60_000) return `${Math.floor(elapsed / 1000)}s`
  if (elapsed < 3_600_000) return `${Math.floor(elapsed / 60_000)}m`
  return `${Math.floor(elapsed / 3_600_000)}h`
}

function AuthorityStack({ window }: { window: RunWindow | null }) {
  const closed = (value: string | undefined) => (value ?? '').toLowerCase().includes('closed')
  const items = [
    { label: 'simulation', value: window?.simulation_only ? 'enforced' : 'unknown', safe: window?.simulation_only === true },
    { label: 'hardware', value: window?.hardware_authority ?? 'unknown', safe: closed(window?.hardware_authority) },
    { label: 'external compute', value: window?.external_compute_authority ?? 'unknown', safe: closed(window?.external_compute_authority) },
    { label: 'Brev', value: window?.brev_authority ?? 'unknown', safe: closed(window?.brev_authority) },
  ]
  return (
    <div className="foundry-authority-stack">
      {items.map((item) => (
        <div key={item.label} className="foundry-authority-row">
          <Led tone={item.safe ? 'green' : 'red'} />
          <span>{item.label}</span>
          <strong>{item.value}</strong>
        </div>
      ))}
    </div>
  )
}

function ActivityRibbon({ events, now }: { events: StudioEvent[]; now: number }) {
  const ordered = events.slice(0, 28).reverse()
  const latest = events[0]
  return (
    <section className="foundry-activity" aria-label="Observed workflow activity">
      <div className="foundry-activity-heading">
        <span className="flex items-center gap-2">
          <Led tone="cyan" pulse />
          <span className="cap text-ink">evidence activity</span>
        </span>
        <span className="hidden truncate text-2xs text-dim lg:block">
          {latest ? `${latest.title} · observed ${ageLabel(latest.observed_at, now)} ago` : 'awaiting workflow documents'}
        </span>
        <Link to="/events" className="btn btn-quiet">
          open ledger
        </Link>
      </div>
      <div className="foundry-activity-track">
        {ordered.map((event, index) => (
          <Link
            key={event.id}
            to="/events"
            className={`foundry-activity-event ${EVENT_TONE[event.kind]}`}
            style={{ '--event-index': index } as CSSProperties}
            title={`${event.title}\n${event.kind} #${event.sequence}\nObserved ${ageLabel(event.observed_at, now)} ago`}
            aria-label={`${event.kind} ${event.sequence}: ${event.title}`}
          >
            <span className="foundry-activity-pulse" />
            <span className="foundry-activity-stem" />
            <span className="foundry-activity-sequence">{event.sequence}</span>
          </Link>
        ))}
      </div>
      <div className="foundry-activity-legend" aria-hidden>
        <span className="foundry-event-brief">brief</span>
        <span className="foundry-event-review">review</span>
        <span className="foundry-event-session">session</span>
        <span className="foundry-event-manager">manager</span>
        <span className="ml-auto">filesystem observation order · never authority</span>
      </div>
    </section>
  )
}

function MissionRail({ now }: { now: number }) {
  const { data: status, syncedAt } = useStatus()
  if (!status) return null
  const ledger = status.ledger ?? {}
  const boundary = status.latest_verified_boundary
  const blockersRaised =
    !!ledger.blockers && !/^(none|no\b|—|n\/a)/i.test(ledger.blockers.trim())
  const closeout = status.run_window
    ? countdownTo(status.run_window.hard_closeout, now)
    : null
  const cutoff = status.run_window
    ? countdownTo(status.run_window.no_new_major_slice_after, now)
    : null

  return (
    <aside className="foundry-mission-rail">
      <section className="foundry-mission-block foundry-mission-primary">
        <span className="cap text-amber">active mission</span>
        <h2>{status.current_task ?? '——'}</h2>
        <p>{status.current_milestone ?? 'No milestone recorded'}</p>
        <span className="foundry-sync">
          <Led tone="green" pulse />
          observed {syncedAt ? `${Math.max(0, Math.round((now - syncedAt) / 1000))}s ago` : 'now'}
        </span>
      </section>

      <section className="foundry-mission-block">
        <span className="cap">run window</span>
        <div className="foundry-clock-pair">
          <div>
            <span>new work cutoff</span>
            <strong>{cutoff ? fmtCountdown(cutoff) : '——:——:——'}</strong>
          </div>
          <div>
            <span>hard closeout</span>
            <strong>{closeout ? fmtCountdown(closeout) : '——:——:——'}</strong>
          </div>
        </div>
        {status.run_window && (
          <p className="font-mono text-3xs text-faint">
            closeout {fmtLocal(status.run_window.hard_closeout)}
          </p>
        )}
      </section>

      <section className="foundry-mission-block">
        <span className="cap">authority perimeter</span>
        <AuthorityStack window={status.run_window} />
      </section>

      <section className="foundry-mission-block">
        <span className="cap">next move</span>
        <p className="foundry-mission-copy">{ledger.next_step ?? 'No next step recorded.'}</p>
      </section>

      {boundary && (
        <Link to="/events" className="foundry-boundary">
          <span className="cap text-cyan">verified boundary</span>
          <strong>{boundary.summary ?? 'Recorded boundary'}</strong>
          <span>
            brief #{boundary.brief_id ?? '—'} · review #{boundary.reviewer_decision_id ?? '—'} ·{' '}
            {shortHash(boundary.commit, 9)}
          </span>
        </Link>
      )}

      <details className="foundry-mission-details">
        <summary>
          <span>blockers</span>
          <Led tone={blockersRaised ? 'red' : 'green'} pulse={blockersRaised} />
        </summary>
        <p>{ledger.blockers ?? 'None recorded.'}</p>
      </details>
    </aside>
  )
}

function scenePreview(workcell: WorkcellManifest | null): string | null {
  if (!workcell) return null
  const values = Object.values(workcell.previews ?? {})
  return values[1] ?? values[0] ?? null
}

export default function Dashboard() {
  const { data: status, error: statusError } = useStatus()
  const workcellPoll = usePoll((signal) => api.workcells(signal), 15_000)
  const episodePoll = usePoll((signal) => api.episodes(signal), 15_000)
  const eventPoll = usePoll((signal) => api.events(80, signal), 5_000)
  const now = useNow(1000)
  const [mode, setMode] = useState<StageMode>('scene')
  const [selectedSceneId, setSelectedSceneId] = useState<string | null>(null)
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string | null>(null)

  const workcells = useMemo(
    () => (workcellPoll.data?.workcells ?? []).filter((item) => typeof item.scene_xml === 'string'),
    [workcellPoll.data],
  )
  const mirroredEpisodes = useMemo(
    () => (episodePoll.data?.episodes ?? []).filter((episode) => Boolean(episode.mirror_video)),
    [episodePoll.data],
  )

  useEffect(() => {
    if (!selectedSceneId && workcells[0]) setSelectedSceneId(workcells[0].scene_id)
  }, [selectedSceneId, workcells])

  useEffect(() => {
    if (!selectedEpisodeId && mirroredEpisodes[0]) setSelectedEpisodeId(mirroredEpisodes[0].id)
  }, [mirroredEpisodes, selectedEpisodeId])

  const selectedWorkcell =
    workcells.find((workcell) => workcell.scene_id === selectedSceneId) ?? workcells[0] ?? null
  const selectedEpisode =
    mirroredEpisodes.find((episode) => episode.id === selectedEpisodeId) ?? mirroredEpisodes[0] ?? null
  const preview = scenePreview(selectedWorkcell)
  const combinedError = statusError ?? workcellPoll.error ?? episodePoll.error ?? eventPoll.error

  if (!status && statusError) return <ErrorState error={statusError} />
  if (!status)
    return (
      <div className="flex items-center justify-center gap-2 py-16">
        <Led tone="amber" pulse />
        <span className="cap">lighting the foundry…</span>
      </div>
    )

  return (
    <div className="foundry-home">
      <header className="foundry-heading">
        <div>
          <span className="cap text-amber">robot-learning foundry</span>
          <h1>Foundry stage</h1>
          <p>
            {selectedWorkcell?.task_prompt ??
              'Inspect a compiled workcell, then project a recorded policy episode into the stage.'}
          </p>
        </div>
        <div className="foundry-heading-state">
          <Tag tone="cyan">live artifact view</Tag>
          <Tag tone="amber">simulation only</Tag>
          <span className="flex items-center gap-2">
            <Led tone={combinedError ? 'red' : 'green'} pulse={!combinedError} />
            <span className="cap">{combinedError ? 'partial link' : 'foundry linked'}</span>
          </span>
        </div>
      </header>

      <div className="foundry-layout">
        <section className="foundry-stage-shell" aria-label="Interactive foundry stage">
          <div className="foundry-stage-topbar">
            <div className="foundry-mode-switch" aria-label="Stage projection mode">
              <button
                type="button"
                className={mode === 'scene' ? 'active' : ''}
                onClick={() => setMode('scene')}
                aria-pressed={mode === 'scene'}
              >
                3D workcell
              </button>
              <button
                type="button"
                className={mode === 'replay' ? 'active' : ''}
                onClick={() => selectedEpisode && setMode('replay')}
                disabled={!selectedEpisode}
                aria-pressed={mode === 'replay'}
              >
                recorded replay
              </button>
            </div>
            <span className="foundry-stage-proof">
              <Led tone={mode === 'scene' ? 'cyan' : 'amber'} pulse />
              {mode === 'scene' ? 'compiled simulation fixture' : 'recorded mirror · read only'}
            </span>
          </div>

          <div className="foundry-stage-viewport">
            {mode === 'scene' ? (
              selectedWorkcell?.scene_xml ? (
                <>
                  <Suspense
                    fallback={
                      <div className="flex h-[32rem] items-center justify-center gap-2">
                        <Led tone="cyan" pulse />
                        <span className="cap">lighting 3D scene…</span>
                      </div>
                    }
                  >
                    <WorkcellOrbit
                      sceneXml={selectedWorkcell.scene_xml}
                      sceneId={selectedWorkcell.scene_id}
                      immersive
                    />
                  </Suspense>
                  <div className="foundry-scene-identity">
                    <span className="cap text-cyan">compiled workcell</span>
                    <strong>{selectedWorkcell.scene_id}</strong>
                    <span>
                      {selectedWorkcell.cube_count ?? '—'} cubes · {selectedWorkcell.tray_count ?? '—'} trays ·{' '}
                      {selectedWorkcell.all_cubes_stable ? 'settled' : 'stability unverified'}
                    </span>
                  </div>
                </>
              ) : (
                <div className="flex h-full items-center justify-center">
                  <span className="cap">no compiled workcell available</span>
                </div>
              )
            ) : selectedEpisode ? (
              <ReplayStage
                key={selectedEpisode.id}
                episode={selectedEpisode}
                episodes={mirroredEpisodes}
                onSelect={setSelectedEpisodeId}
                onReturnToScene={() => setMode('scene')}
              />
            ) : (
              <div className="flex h-full items-center justify-center">
                <span className="cap">no recorded mirror available</span>
              </div>
            )}
          </div>

          {mode === 'scene' && (
            <div className="foundry-stage-dock">
              <button
                type="button"
                className="foundry-launch"
                onClick={() => selectedEpisode && setMode('replay')}
                disabled={!selectedEpisode}
              >
                <span className="foundry-launch-plus" aria-hidden>+</span>
                <span>
                  <strong>Launch recorded replay</strong>
                  <small>watch an existing episode · no new execution</small>
                </span>
              </button>

              {preview && (
                <img
                  src={mediaUrl(preview)}
                  alt={`${selectedWorkcell?.scene_id ?? 'workcell'} overhead preview`}
                  className="foundry-scene-thumb"
                />
              )}
              <label className="foundry-scene-select">
                <span className="cap">scene</span>
                <select
                  value={selectedWorkcell?.scene_id ?? ''}
                  onChange={(event) => setSelectedSceneId(event.target.value)}
                  aria-label="Select compiled workcell"
                >
                  {workcells.map((workcell) => (
                    <option key={workcell.scene_id} value={workcell.scene_id}>
                      {workcell.scene_id}
                    </option>
                  ))}
                </select>
              </label>
              <Link to="/workcells" className="btn btn-quiet">
                open workbench
              </Link>
            </div>
          )}
        </section>

        <MissionRail now={now} />
      </div>

      <ActivityRibbon events={eventPoll.data?.events ?? []} now={now} />
      {combinedError && <ErrorState error={combinedError} />}
    </div>
  )
}
