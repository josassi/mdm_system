import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  MagnifyingGlassIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  UserGroupIcon,
  ServerIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { entityApi } from '../api/client'
import type { Entity } from '../types'

type SortField = 'entity_id' | 'party_count' | 'match_evidence_count' | 'conflict_count' | 'resolution_score' | 'updated_at'
type SortDirection = 'asc' | 'desc'

export default function EntityList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterConflicts, setFilterConflicts] = useState<'all' | 'with-conflicts' | 'no-conflicts'>('all')
  const [sortField, setSortField] = useState<SortField>('entity_id')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const { data: entities, isLoading, error } = useQuery({
    queryKey: ['entities'],
    queryFn: entityApi.getEntities,
  })

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('asc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? 
      <ChevronUpIcon className="h-3 w-3 inline ml-1" /> : 
      <ChevronDownIcon className="h-3 w-3 inline ml-1" />
  }

  const filteredAndSortedEntities = entities?.filter(entity => {
    const matchesSearch = !searchQuery || 
      entity.primary_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      entity.entity_id.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesFilter = 
      filterConflicts === 'all' ||
      (filterConflicts === 'with-conflicts' && entity.has_conflicts) ||
      (filterConflicts === 'no-conflicts' && !entity.has_conflicts)
    
    return matchesSearch && matchesFilter
  }).sort((a, b) => {
    let aVal: any = a[sortField]
    let bVal: any = b[sortField]
    
    // Handle special cases
    if (sortField === 'updated_at') {
      aVal = new Date(aVal).getTime()
      bVal = new Date(bVal).getTime()
    }
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading entities...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Entities</h3>
          <p className="text-gray-600">Unable to load entity data. Please check the API connection.</p>
        </div>
      </div>
    )
  }

  const stats = {
    total: entities?.length || 0,
    withConflicts: entities?.filter(e => e.has_conflicts).length || 0,
    avgParties: entities?.length ? 
      (entities.reduce((sum, e) => sum + e.party_count, 0) / entities.length).toFixed(1) : '0',
  }

  return (
    <div className="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div className="mb-2">
        <h2 className="text-lg font-bold text-gray-900 mb-1">Master Entities</h2>
        <p className="text-xs text-gray-600">
          Resolved entities from multiple source systems
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Total</p>
              <p className="text-xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <UserGroupIcon className="h-8 w-8 text-primary-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Conflicts</p>
              <p className="text-xl font-bold text-red-600">{stats.withConflicts}</p>
            </div>
            <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Avg Parties</p>
              <p className="text-xl font-bold text-gray-900">{stats.avgParties}</p>
            </div>
            <ServerIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Clean</p>
              <p className="text-xl font-bold text-green-600">{stats.total - stats.withConflicts}</p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </div>

      <div className="card mb-2">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name or entity ID..."
              className="input w-full pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <div className="flex gap-1">
            <button
              onClick={() => setFilterConflicts('all')}
              className={`btn-secondary ${
                filterConflicts === 'all' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              All
            </button>
            <button
              onClick={() => setFilterConflicts('with-conflicts')}
              className={`btn-secondary ${
                filterConflicts === 'with-conflicts' ? 'bg-red-600 text-white' : ''
              }`}
            >
              Conflicts
            </button>
            <button
              onClick={() => setFilterConflicts('no-conflicts')}
              className={`btn-secondary ${
                filterConflicts === 'no-conflicts' ? 'bg-green-600 text-white' : ''
              }`}
            >
              Clean
            </button>
          </div>
        </div>
      </div>

      <div className="card overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="w-12">#</th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('entity_id')}>
                Entity ID <SortIcon field="entity_id" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('party_count')}>
                Parties <SortIcon field="party_count" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('match_evidence_count')}>
                Evidence <SortIcon field="match_evidence_count" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('conflict_count')}>
                Conflicts <SortIcon field="conflict_count" />
              </th>
              <th className="w-32">Source Systems</th>
              <th className="w-20 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('resolution_score')}>
                Score <SortIcon field="resolution_score" />
              </th>
              <th className="w-32 cursor-pointer hover:bg-gray-50" onClick={() => handleSort('updated_at')}>
                Updated <SortIcon field="updated_at" />
              </th>
              <th className="w-20 text-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedEntities?.map((entity, idx) => (
              <tr key={entity.entity_id} className="cursor-pointer" onClick={() => window.location.href = `/entities/${entity.entity_id}`}>
                <td className="text-gray-500">{idx + 1}</td>
                <td className="font-mono text-sm font-medium text-gray-900">{entity.entity_id}</td>
                <td className="text-center">
                  <span className={`inline-flex items-center justify-center w-8 h-8 rounded font-bold text-xs ${
                    entity.has_conflicts ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                  }`}>
                    {entity.party_count}
                  </span>
                </td>
                <td className="text-center text-gray-700">{entity.match_evidence_count || '-'}</td>
                <td className="text-center">
                  {entity.has_conflicts ? (
                    <span className="badge badge-danger">
                      {entity.conflict_count}
                    </span>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
                <td className="text-xs text-gray-600">{entity.source_systems.join(', ')}</td>
                <td className="text-center">
                  <span className={`font-medium ${
                    entity.resolution_score >= 0.9 ? 'text-green-600' :
                    entity.resolution_score >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {(entity.resolution_score * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="text-xs text-gray-500">{new Date(entity.updated_at).toLocaleDateString()}</td>
                <td className="text-center">
                  {entity.has_conflicts ? (
                    <span className="badge badge-danger">
                      <ExclamationTriangleIcon className="h-3 w-3" />
                    </span>
                  ) : (
                    <span className="badge badge-success">
                      <CheckCircleIcon className="h-3 w-3" />
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedEntities?.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-gray-500">No entities found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}
