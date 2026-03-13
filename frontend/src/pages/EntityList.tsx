import { useState, useEffect } from 'react'
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

type SortField = 'entity_id' | 'party_count' | 'match_evidence_count' | 'conflict_count' | 'resolution_score' | 'updated_at' | 'total_pairs' | 'matching_pairs' | 'ok_pairs' | 'non_matching_pairs' | 'pairs_blocked' | 'unique_attributes' | 'contradicting_attributes' | 'avg_pair_score'
type SortDirection = 'asc' | 'desc'

export default function EntityList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterConflicts, setFilterConflicts] = useState<'all' | 'with-conflicts' | 'no-conflicts'>('all')
  const [hideSingleParties, setHideSingleParties] = useState(false)
  const [minParties, setMinParties] = useState<number | ''>('')
  const [maxParties, setMaxParties] = useState<number | ''>('')
  const [minScore, setMinScore] = useState<number | ''>('')
  const [sortField, setSortField] = useState<SortField>(() => {
    const saved = localStorage.getItem('entityListSortField')
    return (saved as SortField) || 'entity_id'
  })
  const [sortDirection, setSortDirection] = useState<SortDirection>(() => {
    const saved = localStorage.getItem('entityListSortDirection')
    return (saved as SortDirection) || 'asc'
  })

  const { data: entities, isLoading, error } = useQuery({
    queryKey: ['entities'],
    queryFn: entityApi.getEntities,
  })

  // Persist sort settings to localStorage
  useEffect(() => {
    localStorage.setItem('entityListSortField', sortField)
    localStorage.setItem('entityListSortDirection', sortDirection)
  }, [sortField, sortDirection])

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
    
    const matchesConflictFilter = 
      filterConflicts === 'all' ||
      (filterConflicts === 'with-conflicts' && entity.has_conflicts) ||
      (filterConflicts === 'no-conflicts' && !entity.has_conflicts)
    
    const matchesSinglePartyFilter = !hideSingleParties || entity.party_count > 1
    
    const matchesMinParties = minParties === '' || entity.party_count >= minParties
    const matchesMaxParties = maxParties === '' || entity.party_count <= maxParties
    
    const matchesMinScore = minScore === '' || 
      (entity.avg_pair_score !== null && entity.avg_pair_score !== undefined && entity.avg_pair_score >= minScore / 100)
    
    return matchesSearch && matchesConflictFilter && matchesSinglePartyFilter && 
           matchesMinParties && matchesMaxParties && matchesMinScore
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

        <div className="flex flex-wrap gap-2 items-center text-xs">
          <label className="flex items-center gap-1">
            <input
              type="checkbox"
              checked={hideSingleParties}
              onChange={(e) => setHideSingleParties(e.target.checked)}
              className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-gray-700">Hide single parties</span>
          </label>

          <div className="flex items-center gap-1">
            <span className="text-gray-600">Parties:</span>
            <input
              type="number"
              placeholder="Min"
              value={minParties}
              onChange={(e) => setMinParties(e.target.value ? parseInt(e.target.value) : '')}
              className="input w-16 text-xs px-1 py-0.5"
              min="1"
            />
            <span className="text-gray-500">-</span>
            <input
              type="number"
              placeholder="Max"
              value={maxParties}
              onChange={(e) => setMaxParties(e.target.value ? parseInt(e.target.value) : '')}
              className="input w-16 text-xs px-1 py-0.5"
              min="1"
            />
          </div>

          <div className="flex items-center gap-1">
            <span className="text-gray-600">Min Score:</span>
            <input
              type="number"
              placeholder="0-100"
              value={minScore}
              onChange={(e) => setMinScore(e.target.value ? parseInt(e.target.value) : '')}
              className="input w-16 text-xs px-1 py-0.5"
              min="0"
              max="100"
            />
            <span className="text-gray-500 text-xs">%</span>
          </div>

          <button
            onClick={() => {
              setHideSingleParties(false)
              setMinParties('')
              setMaxParties('')
              setMinScore('')
            }}
            className="btn-secondary text-xs px-2 py-0.5"
          >
            Clear Filters
          </button>
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
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('total_pairs')}>
                Total Pairs <SortIcon field="total_pairs" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('matching_pairs')}>
                Full Match <SortIcon field="matching_pairs" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('ok_pairs')}>
                Partial Match <SortIcon field="ok_pairs" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('non_matching_pairs')}>
                Different <SortIcon field="non_matching_pairs" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('pairs_blocked')}>
                Blocked Pairs <SortIcon field="pairs_blocked" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('unique_attributes')}>
                Unique Attrs <SortIcon field="unique_attributes" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('contradicting_attributes')}>
                Attr Conflicts <SortIcon field="contradicting_attributes" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('avg_pair_score')}>
                Match Score <SortIcon field="avg_pair_score" />
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
                <td className="text-center text-gray-700">{entity.total_pairs ?? '-'}</td>
                <td className="text-center">
                  <span className="inline-flex items-center justify-center px-2 py-1 rounded-full font-semibold text-xs bg-green-100 text-green-700">
                    {entity.matching_pairs ?? 0}
                  </span>
                </td>
                <td className="text-center">
                  <span className="inline-flex items-center justify-center px-2 py-1 rounded-full font-semibold text-xs bg-yellow-100 text-yellow-700">
                    {entity.ok_pairs ?? 0}
                  </span>
                </td>
                <td className="text-center">
                  <span className="inline-flex items-center justify-center px-2 py-1 rounded-full font-semibold text-xs bg-gray-100 text-gray-700">
                    {entity.non_matching_pairs ?? 0}
                  </span>
                </td>
                <td className="text-center">
                  <span className={`inline-flex items-center justify-center px-2 py-1 rounded-full font-semibold text-xs ${
                    (entity.pairs_blocked ?? 0) > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {entity.pairs_blocked ?? 0}
                  </span>
                </td>
                <td className="text-center text-gray-700">{entity.unique_attributes ?? '-'}</td>
                <td className="text-center">
                  <span className={`inline-flex items-center justify-center px-2 py-1 rounded-full font-semibold text-xs ${
                    (entity.contradicting_attributes ?? 0) > 0 ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'
                  }`}>
                    {entity.contradicting_attributes ?? 0}
                  </span>
                </td>
                <td className="text-center">
                  {entity.avg_pair_score === null || entity.avg_pair_score === undefined ? (
                    <span className="text-gray-400 text-sm">N/A</span>
                  ) : (
                    <span className={`font-semibold ${
                      entity.avg_pair_score >= 0.9 ? 'text-green-600' :
                      entity.avg_pair_score >= 0.7 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {(entity.avg_pair_score * 100).toFixed(0)}%
                    </span>
                  )}
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
