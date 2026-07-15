import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, mediaUrl, usePoll } from '../api/client'
import type { EpisodeSummary } from '../api/types'
import { EmptyState, ErrorState, Led, Panel, Tag } from '../components/ui'
import { sci } from '../lib/format'

type MirroredEpisode = EpisodeSummary & { mirror_video: string }

function timecode(seconds: number): string {
  if (!Number.isFinite(seconds) || seconds < 0) return '00:00.0'
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds - minutes * 60
  return `${String(minutes).padStart(2, '0')}:${remainder.toFixed(1).padStart(4, '0')}`
}

function episodeLabel(episode: EpisodeSummary): string {
  const stem = episode.id.split('/')[1]
  const role = episode.seed_role ? ` · ${episode.seed_role}` : ''
  return `${stem} · seed ${episode.seed ?? '—'}${role}`
}

function EpisodePicker({
  label,
  episodes,
  value,
  otherValue,
  onChange,
}: {
  label: string
  episodes: MirroredEpisode[]
  value: string
  otherValue: string
  onChange: (episodeId: string) => void
}) {
  return (
    <label className="block min-w-0">
      <span className="cap mb-1 block">{label}</span>
      <select className="field" value={value} onChange={(event) => onChange(event.target.value)}>
        {episodes.map((episode) => (
          <option key={episode.id} value={episode.id} disabled={episode.id === otherValue}>
            {episodeLabel(episode)}
          </option>
        ))}
      </select>
    </label>
  )
}

function MirrorPanel({
  side,
  episode,
  videoRef,
  onLoadedMetadata,
  onTimeUpdate,
  onEnded,
  onToggle,
}: {
  side: 'A' | 'B'
  episode: MirroredEpisode
  videoRef: React.RefObject<HTMLVideoElement | null>
  onLoadedMetadata: () => void
  onTimeUpdate?: () => void
  onEnded: () => void
  onToggle: () => void
}) {
  return (
    <Panel
      title={`mirror ${side} · ${episode.id.split('/')[1]}`}
      right={
        <span className="flex items-center gap-2">
          <Tag tone={episode.seed_role === 'held_out' ? 'violet' : 'cyan'}>
            {episode.seed_role ?? 'policy'}
          </Tag>
          <Tag tone="dim">seed {episode.seed ?? '—'}</Tag>
        </span>
      }
      pad={false}
    >
      <button
        type="button"
        className="group relative block w-full bg-black text-left focus-visible:outline-1 focus-visible:outline-cyan"
        onClick={onToggle}
        aria-label={`Toggle synchronized playback from mirror ${side}`}
      >
        <video
          ref={videoRef}
          src={mediaUrl(episode.mirror_video)}
          preload="metadata"
          muted
          playsInline
          className="aspect-video max-h-[440px] w-full bg-black object-contain"
          onLoadedMetadata={onLoadedMetadata}
          onTimeUpdate={onTimeUpdate}
          onEnded={onEnded}
        />
        <span className="pointer-events-none absolute right-2 bottom-2 border border-line-2 bg-bg/80 px-1.5 py-1 opacity-0 transition-opacity group-hover:opacity-100">
          <span className="cap text-cyan">shared transport</span>
        </span>
      </button>
      <div className="grid grid-cols-[auto_minmax(0,1fr)_auto] gap-2 border-t border-line p-2">
        <span className="cap">frames · {episode.frame_count ?? '—'}</span>
        <span className="cap whitespace-nowrap text-center">
          max lift · {sci(episode.maximum_anchor_lift_m)} m
        </span>
        <Link to={`/episodes/${episode.id}`} className="cap text-right text-cyan hover:underline">
          inspect trace →
        </Link>
      </div>
    </Panel>
  )
}

export default function EpisodeCompare() {
  const { data, error } = usePoll((signal) => api.episodes(signal), 10000)
  const mirrored = useMemo(
    () =>
      (data?.episodes ?? []).filter(
        (episode): episode is MirroredEpisode => typeof episode.mirror_video === 'string',
      ),
    [data],
  )
  const mirroredKey = mirrored.map((episode) => episode.id).join('\u0000')
  const [leftId, setLeftId] = useState('')
  const [rightId, setRightId] = useState('')
  const [durations, setDurations] = useState({ left: 0, right: 0 })
  const [currentTime, setCurrentTime] = useState(0)
  const [playing, setPlaying] = useState(false)
  const leftVideo = useRef<HTMLVideoElement>(null)
  const rightVideo = useRef<HTMLVideoElement>(null)

  useEffect(() => {
    const available = mirroredKey ? mirroredKey.split('\u0000') : []
    setLeftId((current) => (available.includes(current) ? current : (available[0] ?? '')))
    setRightId((current) => (available.includes(current) ? current : (available[1] ?? available[0] ?? '')))
  }, [mirroredKey])

  useEffect(() => {
    leftVideo.current?.pause()
    rightVideo.current?.pause()
    setPlaying(false)
    setCurrentTime(0)
    setDurations({
      left: Number.isFinite(leftVideo.current?.duration) ? (leftVideo.current?.duration ?? 0) : 0,
      right: Number.isFinite(rightVideo.current?.duration) ? (rightVideo.current?.duration ?? 0) : 0,
    })
  }, [leftId, rightId])

  useEffect(
    () => () => {
      leftVideo.current?.pause()
      rightVideo.current?.pause()
    },
    [],
  )

  if (error && !data) return <ErrorState error={error} />
  if (mirrored.length < 2) {
    return (
      <Panel title="episode mirror compare">
        <EmptyState>at least two rendered policy mirrors are required</EmptyState>
      </Panel>
    )
  }

  const left = mirrored.find((episode) => episode.id === leftId) ?? mirrored[0]
  const right = mirrored.find((episode) => episode.id === rightId) ?? mirrored[1]
  const sharedDuration =
    durations.left > 0 && durations.right > 0 ? Math.min(durations.left, durations.right) : 0

  const pauseBoth = () => {
    leftVideo.current?.pause()
    rightVideo.current?.pause()
    setPlaying(false)
  }

  const seekBoth = (requestedTime: number) => {
    const next = Math.max(0, Math.min(requestedTime, sharedDuration || requestedTime))
    if (leftVideo.current) leftVideo.current.currentTime = next
    if (rightVideo.current) rightVideo.current.currentTime = next
    setCurrentTime(next)
  }

  const togglePlayback = async () => {
    if (playing) {
      pauseBoth()
      return
    }
    if (!leftVideo.current || !rightVideo.current || sharedDuration <= 0) return
    if (currentTime >= sharedDuration - 0.03) seekBoth(0)
    rightVideo.current.currentTime = leftVideo.current.currentTime
    const results = await Promise.allSettled([leftVideo.current.play(), rightVideo.current.play()])
    if (results.some((result) => result.status === 'rejected')) {
      pauseBoth()
      return
    }
    setPlaying(true)
  }

  const updateDuration = (side: 'left' | 'right') => {
    const video = side === 'left' ? leftVideo.current : rightVideo.current
    const duration = video && Number.isFinite(video.duration) ? video.duration : 0
    setDurations((current) => ({ ...current, [side]: duration }))
  }

  const syncFromLeft = () => {
    const lead = leftVideo.current
    const follower = rightVideo.current
    if (!lead) return
    const next = Math.min(lead.currentTime, sharedDuration || lead.currentTime)
    setCurrentTime(next)
    if (follower && Math.abs(follower.currentTime - next) > 0.12) follower.currentTime = next
    if (sharedDuration > 0 && next >= sharedDuration - 0.03) pauseBoth()
  }

  return (
    <div className="flex flex-col gap-3">
      <Panel
        title={
          <span>
            <Link to="/episodes" className="text-faint hover:text-ink">
              episodes /
            </Link>{' '}
            mirror compare
          </span>
        }
        right={
          <span className="flex items-center gap-2">
            <Led tone={playing ? 'green' : 'cyan'} pulse={playing} />
            <Tag tone="dim">visualization only</Tag>
          </span>
        }
      >
        <div className="grid gap-3 md:grid-cols-2">
          <EpisodePicker
            label="mirror A"
            episodes={mirrored}
            value={left.id}
            otherValue={right.id}
            onChange={setLeftId}
          />
          <EpisodePicker
            label="mirror B"
            episodes={mirrored}
            value={right.id}
            otherValue={left.id}
            onChange={setRightId}
          />
        </div>
      </Panel>

      <div className="grid gap-3 lg:grid-cols-2">
        <MirrorPanel
          side="A"
          episode={left}
          videoRef={leftVideo}
          onLoadedMetadata={() => updateDuration('left')}
          onTimeUpdate={syncFromLeft}
          onEnded={pauseBoth}
          onToggle={() => void togglePlayback()}
        />
        <MirrorPanel
          side="B"
          episode={right}
          videoRef={rightVideo}
          onLoadedMetadata={() => updateDuration('right')}
          onEnded={pauseBoth}
          onToggle={() => void togglePlayback()}
        />
      </div>

      <Panel
        title="synchronized transport"
        right={<span className="cap text-faint">clamped to shorter mirror</span>}
      >
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn btn-primary w-24"
            disabled={sharedDuration <= 0}
            onClick={() => void togglePlayback()}
          >
            {playing ? 'pause' : 'play both'}
          </button>
          <button
            type="button"
            className="btn btn-quiet"
            disabled={sharedDuration <= 0}
            onClick={() => seekBoth(currentTime - 1)}
          >
            − 1s
          </button>
          <input
            type="range"
            min={0}
            max={sharedDuration || 1}
            step={0.01}
            value={Math.min(currentTime, sharedDuration || 1)}
            disabled={sharedDuration <= 0}
            onChange={(event) => seekBoth(Number(event.target.value))}
            className="min-w-0 flex-1 accent-cyan"
            aria-label="Synchronized mirror time"
          />
          <button
            type="button"
            className="btn btn-quiet"
            disabled={sharedDuration <= 0}
            onClick={() => seekBoth(currentTime + 1)}
          >
            + 1s
          </button>
          <span className="tabular w-28 text-right font-mono text-2xs text-ink">
            {timecode(currentTime)} / {timecode(sharedDuration)}
          </span>
        </div>
        <p className="cap mt-2 text-faint">
          Mirror videos are visualization artifacts. Playback alignment grants no policy, training,
          transfer, or promotion authority.
        </p>
      </Panel>
    </div>
  )
}
