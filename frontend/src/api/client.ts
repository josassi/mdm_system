import axios from 'axios'
import type { Entity, EntityDetail, PartyDetail, Party, MatchEvidence, Blocking, Relationship } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Add response interceptor to fix JSON parsing
api.interceptors.response.use(
  (response) => {
    // If data is a string, parse it
    if (typeof response.data === 'string') {
      try {
        response.data = JSON.parse(response.data)
      } catch (e) {
        console.error('Failed to parse JSON response:', e)
      }
    }
    
    return response
  },
  (error) => {
    return Promise.reject(error)
  }
)

export const entityApi = {
  getEntities: async (): Promise<Entity[]> => {
    const { data } = await api.get('/entities')
    return data
  },

  getEntityDetail: async (entityId: string): Promise<EntityDetail> => {
    const { data } = await api.get(`/entities/${entityId}`)
    return data
  },

  searchEntities: async (query: string): Promise<Entity[]> => {
    const { data } = await api.get('/search', { params: { q: query } })
    return data
  },
}

export const partyApi = {
  getPartyDetail: async (partyId: string): Promise<PartyDetail> => {
    const { data } = await api.get(`/parties/${partyId}/detail`)
    return data
  },
}

export const dashboardApi = {
  getStats: async (): Promise<any> => {
    const { data } = await api.get('/dashboard/stats')
    return data
  },
}

export interface ConfigInfo {
  current_config: string
  available_configs: string[]
}

export interface ConfigChangeResponse {
  success: boolean
  current_config: string
  entity_count: number
  party_count: number
}

export const configApi = {
  getConfig: async (): Promise<ConfigInfo> => {
    const { data } = await api.get('/config')
    return data
  },

  setConfig: async (config: string): Promise<ConfigChangeResponse> => {
    const { data } = await api.post('/config', { config })
    return data
  },
}

export interface ClusterDetail {
  cluster_id: string
  parties: Party[]
  match_evidence: MatchEvidence[]
  blocking: Blocking[]
  relationships: Relationship[]
}

export const clusterApi = {
  getClusterDetail: async (clusterId: string): Promise<ClusterDetail> => {
    const { data } = await api.get(`/clusters/${clusterId}`)
    return data
  },
}

export default api
