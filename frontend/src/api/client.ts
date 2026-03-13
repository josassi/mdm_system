import axios from 'axios'
import type { Entity, EntityDetail, PartyDetail } from '../types'

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

export default api
