import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Shell from './components/Shell'
import { StatusProvider } from './state/StatusContext'
import Dashboard from './pages/Dashboard'
import Episodes from './pages/Episodes'
import EpisodeDetail from './pages/EpisodeDetail'
import Tasks from './pages/Tasks'
import Workcells from './pages/Workcells'
import AgentFeed from './pages/AgentFeed'

export default function App() {
  return (
    <BrowserRouter>
      <StatusProvider>
        <Routes>
          <Route element={<Shell />}>
            <Route index element={<Dashboard />} />
            <Route path="episodes" element={<Episodes />} />
            <Route path="episodes/:kind/:stem" element={<EpisodeDetail />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="workcells" element={<Workcells />} />
            <Route path="feed" element={<AgentFeed />} />
          </Route>
        </Routes>
      </StatusProvider>
    </BrowserRouter>
  )
}
