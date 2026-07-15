/** Formatting + phase-color helpers shared across the console. */

export function shortHash(hash: string | null | undefined, n = 12): string {
  if (!hash) return '—'
  return hash.length > n ? `${hash.slice(0, n)}…` : hash
}

/** 1.4556e-7 → "1.456e-7"; 0.5282 → "0.5282" */
export function sci(value: number | null | undefined, digits = 3): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—'
  if (value === 0) return '0'
  const abs = Math.abs(value)
  if (abs >= 0.001 && abs < 10000) {
    return value.toPrecision(4).replace(/\.?0+$/, '')
  }
  return value.toExponential(digits)
}

export function fmtClock(date: Date): string {
  const hh = String(date.getHours()).padStart(2, '0')
  const mm = String(date.getMinutes()).padStart(2, '0')
  const ss = String(date.getSeconds()).padStart(2, '0')
  return `${hh}:${mm}:${ss}`
}

export function fmtLocal(iso: string | null | undefined): string {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return `${d.toLocaleDateString(undefined, { month: 'short', day: '2-digit' })} ${fmtClock(d)}`
}

export interface CountdownParts {
  negative: boolean
  days: number
  hours: number
  minutes: number
  seconds: number
  totalMs: number
}

export function countdownTo(iso: string, now: number): CountdownParts {
  const target = new Date(iso).getTime()
  let delta = target - now
  const negative = delta < 0
  delta = Math.abs(delta)
  const seconds = Math.floor(delta / 1000) % 60
  const minutes = Math.floor(delta / 60000) % 60
  const hours = Math.floor(delta / 3600000) % 24
  const days = Math.floor(delta / 86400000)
  return { negative, days, hours, minutes, seconds, totalMs: target - now }
}

export function fmtCountdown(parts: CountdownParts): string {
  const core = [parts.hours, parts.minutes, parts.seconds]
    .map((v) => String(v).padStart(2, '0'))
    .join(':')
  const day = parts.days > 0 ? `${parts.days}d ` : ''
  return `${parts.negative ? '-' : ''}${day}${core}`
}

/**
 * Manipulation-cycle phase palette: cool blues on approach, heat through
 * grasp/lift/hold, cooling reds/violets on release/retreat.
 */
const PHASE_COLORS: Record<string, string> = {
  approach: '#4a7dbf',
  pregrasp: '#56b3d8',
  close: '#58c9a5',
  grasp_hold: '#86d96c',
  grasp_confirmed: '#86d96c',
  lift: '#ffd166',
  unassisted_lift: '#ffd166',
  unsupported_lift_hold: '#ffb454',
  stable_hold: '#ff9e2c',
  recording_stable_hold: '#ff9e2c',
  lower: '#f4845f',
  release: '#e26d5c',
  release_settle: '#b86a9f',
  retreat: '#8f8af2',
}

const FALLBACK_COLORS = ['#7a8aa0', '#56c8d8', '#8f8af2', '#58d9a2']

export function phaseColor(phase: string | null | undefined): string {
  if (!phase) return '#47546a'
  const known = PHASE_COLORS[phase]
  if (known) return known
  let h = 0
  for (let i = 0; i < phase.length; i++) h = (h * 31 + phase.charCodeAt(i)) >>> 0
  return FALLBACK_COLORS[h % FALLBACK_COLORS.length]
}

/** "181-t20-35o-flow-trajectory-consistency-audit.md" → {id, title} */
export function parseDocName(name: string): { id: string; title: string } {
  const stem = name.replace(/\.md$/, '')
  const match = /^(\d+)-(.*)$/.exec(stem)
  if (!match) return { id: '—', title: stem.replace(/-/g, ' ') }
  return { id: match[1], title: match[2].replace(/-/g, ' ') }
}

/** "scenesmith.t20_35_rank_capacity_result.v1" → "t20_35_rank_capacity" */
export function gateLabel(schemaVersion: string): string {
  const middle = schemaVersion.replace(/^scenesmith\./, '').replace(/\.v\d+$/, '')
  return middle.replace(/_result$/, '')
}
