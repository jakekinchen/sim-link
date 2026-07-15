import { useCallback, useEffect, useRef, useState } from 'react'
import type {
  EpisodeDetail,
  EpisodesResponse,
  RobotResponse,
  StatusResponse,
  StudioDocument,
  StudioDocumentKind,
  TasksResponse,
  WorkcellArrangementSpec,
  WorkcellManifest,
  WorkcellsResponse,
} from './types'

export class ApiError extends Error {
  status: number
  url: string
  constructor(status: number, url: string, detail: string) {
    super(`${status} ${url}: ${detail}`)
    this.status = status
    this.url = url
  }
}

async function getJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const res = await fetch(url, { signal })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      if (body && typeof body.detail === 'string') detail = body.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, url, detail)
  }
  return (await res.json()) as T
}

async function postJson<T>(url: string, body: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const payload = await res.json()
      if (payload && typeof payload.detail === 'string') detail = payload.detail
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, url, detail)
  }
  return (await res.json()) as T
}

export const api = {
  status: (signal?: AbortSignal) => getJson<StatusResponse>('/api/status', signal),
  episodes: (signal?: AbortSignal) => getJson<EpisodesResponse>('/api/episodes', signal),
  episode: (id: string, signal?: AbortSignal) =>
    getJson<EpisodeDetail>(`/api/episodes/${id}`, signal),
  workcells: (signal?: AbortSignal) => getJson<WorkcellsResponse>('/api/workcells', signal),
  tasks: (signal?: AbortSignal) => getJson<TasksResponse>('/api/tasks', signal),
  robot: (signal?: AbortSignal) => getJson<RobotResponse>('/api/robot', signal),
  document: (kind: StudioDocumentKind, filename: string, signal?: AbortSignal) =>
    getJson<StudioDocument>(
      `/api/documents/${encodeURIComponent(kind)}/${encodeURIComponent(filename)}`,
      signal,
    ),
  buildWorkcell: (spec: WorkcellArrangementSpec) =>
    postJson<WorkcellManifest>('/api/actions/build-workcell', spec),
}

/** URL for a whitelisted media file (mirror mp4, workcell preview png). */
export function mediaUrl(relPath: string): string {
  return `/api/media?path=${encodeURIComponent(relPath)}`
}

/** URL for an expert episode camera frame PNG. */
export function frameUrl(episodeId: string, index: number, view: string): string {
  return `/api/episodes/${episodeId}/frame/${index}/${view}`
}

export interface Polled<T> {
  data: T | null
  error: Error | null
  /** ms timestamp of the last successful fetch */
  syncedAt: number | null
  refresh: () => void
}

/**
 * Poll a fetcher on an interval. Fetches immediately on mount, keeps the
 * last good payload when a poll fails, and aborts in-flight requests on
 * unmount.
 */
export function usePoll<T>(
  fetcher: (signal: AbortSignal) => Promise<T>,
  intervalMs: number | null,
): Polled<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [syncedAt, setSyncedAt] = useState<number | null>(null)
  const [tick, setTick] = useState(0)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    let cancelled = false

    const run = async () => {
      try {
        const payload = await fetcherRef.current(controller.signal)
        if (cancelled) return
        setData(payload)
        setError(null)
        setSyncedAt(Date.now())
      } catch (err) {
        if (cancelled || (err instanceof DOMException && err.name === 'AbortError')) return
        setError(err instanceof Error ? err : new Error(String(err)))
      } finally {
        if (!cancelled && intervalMs !== null) {
          timer = setTimeout(run, intervalMs)
        }
      }
    }

    void run()
    return () => {
      cancelled = true
      controller.abort()
      if (timer !== undefined) clearTimeout(timer)
    }
  }, [intervalMs, tick])

  const refresh = useCallback(() => setTick((n) => n + 1), [])
  return { data, error, syncedAt, refresh }
}
