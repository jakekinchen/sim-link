import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, mediaUrl, usePoll } from '../api/client'
import type { EpisodeSummary } from '../api/types'
import { phaseColor } from '../lib/format'
import { ErrorState, Led, PassFail, Tag } from './ui'

function strictOutcome(episode: EpisodeSummary): boolean | null {
  if (episode.source === 'expert') return episode.outcome?.strict_success ?? null
  return episode.strict_success ?? null
}

function clock(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainder = Math.floor(seconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

export default function ReplayStage({
  episode,
  episodes,
  onSelect,
  onReturnToScene,
}: {
  episode: EpisodeSummary
  episodes: EpisodeSummary[]
  onSelect: (episodeId: string) => void
  onReturnToScene: () => void
}) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const { data, error } = usePoll((signal) => api.episode(episode.id, signal), null)
  const [playing, setPlaying] = useState(false)
  const [duration, setDuration] = useState(0)
  const [currentTime, setCurrentTime] = useState(0)
  const [rate, setRate] = useState(1)
  const timeline = data?.timeline ?? []
  const progress = duration > 0 ? Math.min(1, currentTime / duration) : 0

  const togglePlay = async () => {
    const video = videoRef.current
    if (!video) return
    if (video.paused) {
      try {
        await video.play()
      } catch {
        setPlaying(false)
      }
    } else {
      video.pause()
    }
  }

  const seek = (seconds: number) => {
    const video = videoRef.current
    if (!video || !Number.isFinite(seconds)) return
    video.currentTime = seconds
    setCurrentTime(seconds)
  }

  const cycleRate = () => {
    const nextRate = rate === 1 ? 2 : rate === 2 ? 0.5 : 1
    setRate(nextRate)
    if (videoRef.current) videoRef.current.playbackRate = nextRate
  }

  return (
    <div className="foundry-replay">
      <div className="foundry-replay-hud">
        <span className="flex items-center gap-2">
          <Led tone={error ? 'red' : playing ? 'green' : 'amber'} pulse={playing} />
          <span className="cap text-ink">recorded mirror projection</span>
          <Tag tone="violet">no new execution</Tag>
        </span>
        <span className="ml-auto flex items-center gap-2">
          <PassFail value={strictOutcome(episode)} />
          <Tag tone="dim">seed {episode.seed ?? '—'}</Tag>
          <Tag tone="dim">{episode.frame_count ?? timeline.length} frames</Tag>
        </span>
      </div>

      <div className="foundry-replay-screen">
        {episode.mirror_video ? (
          <video
            ref={videoRef}
            src={mediaUrl(episode.mirror_video)}
            className="h-full w-full object-contain"
            preload="metadata"
            playsInline
            muted
            loop
            onLoadedMetadata={(event) => setDuration(event.currentTarget.duration || 0)}
            onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            <span className="cap">this episode has no mirror projection</span>
          </div>
        )}
        <div className="foundry-replay-title">
          <span className="cap text-faint">episode</span>
          <strong>{episode.id.split('/')[1]}</strong>
          <span className="font-mono text-3xs text-dim">{episode.source.replace('_', ' ')}</span>
        </div>
      </div>

      <div className="foundry-replay-transport">
        <button type="button" className="foundry-transport-play" onClick={() => void togglePlay()}>
          <span aria-hidden>{playing ? 'Ⅱ' : '▶'}</span>
          <span>{playing ? 'pause replay' : 'play replay'}</span>
        </button>
        <span className="tabular w-11 text-right font-mono text-2xs text-ink">
          {clock(currentTime)}
        </span>
        <div className="min-w-0 flex-1">
          <div className="foundry-phase-track" aria-label="Episode phase timeline">
            {timeline.map((frame) => (
              <span
                key={frame.frame_index}
                className="h-full min-w-px flex-1"
                style={{ background: phaseColor(frame.phase ?? frame.task_phase) }}
                title={`frame ${frame.frame_index} · ${frame.phase ?? frame.task_phase ?? 'unknown'}`}
                aria-hidden="true"
              />
            ))}
            <span className="foundry-phase-playhead" style={{ left: `${progress * 100}%` }} />
          </div>
          <input
            type="range"
            min={0}
            max={Math.max(duration, 0.01)}
            step={0.01}
            value={Math.min(currentTime, Math.max(duration, 0.01))}
            onInput={(event) => seek(Number(event.currentTarget.value))}
            className="foundry-replay-range"
            aria-label="Scrub recorded episode"
          />
        </div>
        <span className="tabular w-11 font-mono text-2xs text-dim">{clock(duration)}</span>
        <button type="button" className="btn btn-quiet" onClick={cycleRate}>
          {rate}×
        </button>
      </div>

      <div className="foundry-replay-dock">
        <label className="flex min-w-0 flex-1 items-center gap-2">
          <span className="cap flex-none">recorded run</span>
          <select
            value={episode.id}
            onChange={(event) => onSelect(event.target.value)}
            className="field min-w-0"
            aria-label="Select recorded replay"
          >
            {episodes.map((item) => (
              <option key={item.id} value={item.id}>
                {item.id.split('/')[1]} · seed {item.seed ?? '—'}
              </option>
            ))}
          </select>
        </label>
        <Link to={`/episodes/${episode.id}`} className="btn btn-quiet">
          inspect evidence
        </Link>
        <button type="button" className="btn btn-primary" onClick={onReturnToScene}>
          return to 3D scene
        </button>
      </div>
      {error && <ErrorState error={error} />}
    </div>
  )
}
