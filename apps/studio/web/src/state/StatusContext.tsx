import { createContext, useContext, type ReactNode } from 'react'
import { api, usePoll, type Polled } from '../api/client'
import type { StatusResponse } from '../api/types'

const StatusContext = createContext<Polled<StatusResponse> | null>(null)

/** Single 5s status poll shared by the shell chrome and the dashboard. */
export function StatusProvider({ children }: { children: ReactNode }) {
  const polled = usePoll<StatusResponse>((signal) => api.status(signal), 5000)
  return <StatusContext.Provider value={polled}>{children}</StatusContext.Provider>
}

export function useStatus(): Polled<StatusResponse> {
  const ctx = useContext(StatusContext)
  if (!ctx) throw new Error('useStatus outside StatusProvider')
  return ctx
}
