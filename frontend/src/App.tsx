import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import EntityList from './pages/EntityList'
import EntityDetail from './pages/EntityDetail'
import PartyList from './pages/PartyList'
import PartyDetail from './pages/PartyDetail'
import ClusterList from './pages/ClusterList'
import ClusterDetail from './pages/ClusterDetail'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/entities" element={<EntityList />} />
        <Route path="/entities/:entityId" element={<EntityDetail />} />
        <Route path="/parties" element={<PartyList />} />
        <Route path="/parties/:partyId" element={<PartyDetail />} />
        <Route path="/clusters" element={<ClusterList />} />
        <Route path="/clusters/:clusterId" element={<ClusterDetail />} />
      </Routes>
    </Layout>
  )
}

export default App
