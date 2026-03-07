import axios from 'axios'
import type { Entity, EntityDetail } from '../types'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

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

export default api
