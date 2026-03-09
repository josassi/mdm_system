import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import EntityList from './pages/EntityList'
import EntityDetail from './pages/EntityDetail'
import PartyDetail from './pages/PartyDetail'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<EntityList />} />
        <Route path="/entities/:entityId" element={<EntityDetail />} />
        <Route path="/parties/:partyId" element={<PartyDetail />} />
      </Routes>
    </Layout>
  )
}

export default App
