import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  MagnifyingGlassIcon, 
  UserGroupIcon,
  ServerIcon,
  CubeIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { clusterApi } from '../api/client'
import type { Cluster } from '../types'

type SortField = 'cluster_id' | 'party_count' | 'entity_count' | 'resolution_rate' | 'relationship_count' | 'evidence_count'
type SortDirection = 'asc' | 'desc'

export default function ClusterList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [minParties, setMinParties] = useState<number | ''>('')
  const [maxParties, setMaxParties] = useState<number | ''>('')
  const [sortField, setSortField] = useState<SortField>('party_count')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  const { data: clusters, isLoading, error } = useQuery({
    queryKey: ['clusters'],
    queryFn: clusterApi.getClusters,
  })

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return null
    return sortDirection === 'asc' ? 
      <ChevronUpIcon className="h-3 w-3 inline ml-1" /> : 
      <ChevronDownIcon className="h-3 w-3 inline ml-1" />
  }

  const filteredAndSortedClusters = clusters?.filter(cluster => {
    const matchesSearch = !searchQuery || 
      cluster.cluster_id.toLowerCase().includes(searchQuery.toLowerCase())
    
    const matchesMinParties = minParties === '' || cluster.party_count >= minParties
    const matchesMaxParties = maxParties === '' || cluster.party_count <= maxParties
    
    return matchesSearch && matchesMinParties && matchesMaxParties
  }).sort((a, b) => {
    let aVal: any = a[sortField]
    let bVal: any = b[sortField]
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading clusters...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ServerIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Clusters</h3>
          <p className="text-gray-600">Unable to load cluster data. Please check the API connection.</p>
        </div>
      </div>
    )
  }

  const stats = {
    total: clusters?.length || 0,
    totalParties: clusters?.reduce((sum, c) => sum + c.party_count, 0) || 0,
    totalEntities: clusters?.reduce((sum, c) => sum + c.entity_count, 0) || 0,
    avgResolutionRate: clusters?.length ? 
      (clusters.reduce((sum, c) => sum + c.resolution_rate, 0) / clusters.length * 100).toFixed(1) : '0',
  }

  return (
    <div className="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div className="mb-2">
        <h2 className="text-lg font-bold text-gray-900 mb-1">Clusters</h2>
        <p className="text-xs text-gray-600">
          Business relationship groups formed by foreign key relationships
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-2 mb-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Total Clusters</p>
              <p className="text-xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <ServerIcon className="h-8 w-8 text-primary-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Total Parties</p>
              <p className="text-xl font-bold text-blue-600">{stats.totalParties}</p>
            </div>
            <UserGroupIcon className="h-8 w-8 text-blue-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Total Entities</p>
              <p className="text-xl font-bold text-purple-600">{stats.totalEntities}</p>
            </div>
            <CubeIcon className="h-8 w-8 text-purple-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Avg Resolution</p>
              <p className="text-xl font-bold text-green-600">{stats.avgResolutionRate}%</p>
            </div>
            <CubeIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>
      </div>

      <div className="card mb-2">
        <div className="flex flex-col sm:flex-row gap-2">
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search by cluster ID..."
              className="input w-full pl-8"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center text-xs">
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

          <button
            onClick={() => {
              setMinParties('')
              setMaxParties('')
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
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('cluster_id')}>
                Cluster ID <SortIcon field="cluster_id" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('party_count')}>
                Parties <SortIcon field="party_count" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('entity_count')}>
                Entities <SortIcon field="entity_count" />
              </th>
              <th className="w-32 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('resolution_rate')}>
                Resolution Rate <SortIcon field="resolution_rate" />
              </th>
              <th className="w-32 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('relationship_count')}>
                Relationships <SortIcon field="relationship_count" />
              </th>
              <th className="w-24 text-center cursor-pointer hover:bg-gray-50" onClick={() => handleSort('evidence_count')}>
                Evidence <SortIcon field="evidence_count" />
              </th>
              <th>Source Systems</th>
              <th>Party Types</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedClusters?.map((cluster, idx) => (
              <tr key={cluster.cluster_id} className="cursor-pointer hover:bg-gray-50" onClick={() => window.location.href = `/clusters/${cluster.cluster_id}`}>
                <td className="text-gray-500">{idx + 1}</td>
                <td className="font-mono text-xs">
                  <Link 
                    to={`/clusters/${cluster.cluster_id}`}
                    className="text-blue-600 hover:text-blue-800 hover:underline"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {cluster.cluster_id}
                  </Link>
                </td>
                <td className="text-center">
                  <span className="inline-flex items-center justify-center w-10 h-8 rounded font-bold text-sm bg-blue-100 text-blue-700">
                    {cluster.party_count}
                  </span>
                </td>
                <td className="text-center">
                  <span className="inline-flex items-center justify-center w-10 h-8 rounded font-bold text-sm bg-purple-100 text-purple-700">
                    {cluster.entity_count}
                  </span>
                </td>
                <td className="text-center">
                  <span className={`font-semibold ${
                    cluster.resolution_rate >= 0.9 ? 'text-green-600' :
                    cluster.resolution_rate >= 0.7 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {(cluster.resolution_rate * 100).toFixed(0)}%
                  </span>
                </td>
                <td className="text-center text-gray-700">{cluster.relationship_count}</td>
                <td className="text-center text-gray-700">{cluster.evidence_count}</td>
                <td>
                  <div className="flex flex-wrap gap-1">
                    {cluster.source_systems.slice(0, 3).map((system, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {system}
                      </span>
                    ))}
                    {cluster.source_systems.length > 3 && (
                      <span className="text-xs text-gray-500">+{cluster.source_systems.length - 3}</span>
                    )}
                  </div>
                </td>
                <td>
                  <div className="flex flex-wrap gap-1">
                    {cluster.party_types.slice(0, 3).map((type, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {type}
                      </span>
                    ))}
                    {cluster.party_types.length > 3 && (
                      <span className="text-xs text-gray-500">+{cluster.party_types.length - 3}</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedClusters?.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-gray-500">No clusters found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}
