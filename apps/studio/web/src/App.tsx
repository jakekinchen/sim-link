import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Shell from './components/Shell'
import { StatusProvider } from './state/StatusContext'
import Dashboard from './pages/Dashboard'
import Episodes from './pages/Episodes'
import EpisodeCompare from './pages/EpisodeCompare'
import EpisodeDetail from './pages/EpisodeDetail'
import EventLedger from './pages/EventLedger'
import Tasks from './pages/Tasks'
import Workcells from './pages/Workcells'
import AgentFeed from './pages/AgentFeed'
import Robot from './pages/Robot'

export default function App() {
  return (
    <BrowserRouter>
      <StatusProvider>
        <Routes>
          <Route element={<Shell />}>
            <Route index element={<Dashboard />} />
            <Route path="events" element={<EventLedger />} />
            <Route path="episodes" element={<Episodes />} />
            <Route path="episodes/compare" element={<EpisodeCompare />} />
            <Route path="episodes/:kind/:stem" element={<EpisodeDetail />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="workcells" element={<Workcells />} />
            <Route path="feed" element={<AgentFeed />} />
            <Route path="robot" element={<Robot />} />
          </Route>
        </Routes>
      </StatusProvider>
    </BrowserRouter>
  )
}
