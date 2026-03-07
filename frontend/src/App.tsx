import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import EntityList from './pages/EntityList'
import EntityDetail from './pages/EntityDetail'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<EntityList />} />
        <Route path="/entities/:entityId" element={<EntityDetail />} />
      </Routes>
    </Layout>
  )
}

export default App
