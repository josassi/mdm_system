import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  MagnifyingGlassIcon, 
  ExclamationTriangleIcon,
  UserIcon,
  ServerIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline'
import { partyApi, type PartySummary } from '../api/client'

type SortField = 'party_id' | 'source_system' | 'entity_party_count' | 'match_score' | 'display_name'
type SortDirection = 'asc' | 'desc'

export default function PartyList() {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSource, setFilterSource] = useState<string>('all')
  const [filterType, setFilterType] = useState<string>('all')
  const [filterHasEntity, setFilterHasEntity] = useState<'all' | 'with-entity' | 'no-entity'>('all')
  const [minMatchScore, setMinMatchScore] = useState<number | ''>('')
  const [sortField, setSortField] = useState<SortField>('party_id')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

  const { data: parties, isLoading, error } = useQuery({
    queryKey: ['parties'],
    queryFn: partyApi.getParties,
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

  // Get unique source systems and party types for filters
  const sourceSystems = [...new Set(parties?.map(p => p.source_system) || [])]
  const partyTypes = [...new Set(parties?.map(p => p.party_type) || [])]

  const filteredAndSortedParties = parties?.filter(party => {
    const matchesSearch = !searchQuery || 
      (party.display_name && party.display_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      party.party_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (party.email && party.email.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (party.gov_id && party.gov_id.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesSource = filterSource === 'all' || party.source_system === filterSource
    const matchesType = filterType === 'all' || party.party_type === filterType
    
    const matchesEntityFilter = 
      filterHasEntity === 'all' ||
      (filterHasEntity === 'with-entity' && party.entity_id !== null) ||
      (filterHasEntity === 'no-entity' && party.entity_id === null)
    
    const matchesMinScore = minMatchScore === '' || 
      (party.match_score !== null && party.match_score >= minMatchScore / 100)
    
    return matchesSearch && matchesSource && matchesType && matchesEntityFilter && matchesMinScore
  }).sort((a, b) => {
    let aVal: any = a[sortField]
    let bVal: any = b[sortField]
    
    // Handle null values
    if (aVal === null) return 1
    if (bVal === null) return -1
    
    if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
    if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
    return 0
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading parties...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Parties</h3>
          <p className="text-gray-600">Unable to load party data. Please check the API connection.</p>
        </div>
      </div>
    )
  }

  const stats = {
    total: parties?.length || 0,
    withEntity: parties?.filter(p => p.entity_id !== null).length || 0,
    avgMatchScore: parties?.filter(p => p.match_score !== null).length ? 
      ((parties.filter(p => p.match_score !== null).reduce((sum, p) => sum + (p.match_score || 0), 0) / 
        parties.filter(p => p.match_score !== null).length) * 100).toFixed(1) : '0',
  }

  return (
    <div className="max-w-7xl mx-auto px-2 sm:px-4 py-2">
      <div className="mb-2">
        <h2 className="text-lg font-bold text-gray-900 mb-1">Parties</h2>
        <p className="text-xs text-gray-600">
          All parties from source systems
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Total Parties</p>
              <p className="text-xl font-bold text-gray-900">{stats.total}</p>
            </div>
            <UserIcon className="h-8 w-8 text-primary-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">In Entities</p>
              <p className="text-xl font-bold text-gray-900">{stats.withEntity}</p>
            </div>
            <ServerIcon className="h-8 w-8 text-green-500" />
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-gray-600">Avg Match Score</p>
              <p className="text-xl font-bold text-gray-900">{stats.avgMatchScore}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="card mb-2 p-2">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-2 items-end">
          <div className="md:col-span-2">
            <div className="relative">
              <MagnifyingGlassIcon className="h-3 w-3 absolute left-2 top-2 text-gray-400" />
              <input
                type="text"
                placeholder="Search: Name, ID, email, gov ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-7 pr-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>

          <div>
            <select
              value={filterSource}
              onChange={(e) => setFilterSource(e.target.value)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Systems</option>
              {sourceSystems.map(system => (
                <option key={system} value={system}>{system}</option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Types</option>
              {partyTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>

          <div>
            <select
              value={filterHasEntity}
              onChange={(e) => setFilterHasEntity(e.target.value as any)}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All</option>
              <option value="with-entity">In Entity</option>
              <option value="no-entity">No Entity</option>
            </select>
          </div>

          <div>
            <input
              type="number"
              placeholder="Min Score %"
              value={minMatchScore}
              onChange={(e) => setMinMatchScore(e.target.value === '' ? '' : Number(e.target.value))}
              className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
              min="0"
              max="100"
            />
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th 
                  className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('party_id')}
                >
                  Party ID <SortIcon field="party_id" />
                </th>
                <th 
                  className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('display_name')}
                >
                  Name <SortIcon field="display_name" />
                </th>
                <th 
                  className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('source_system')}
                >
                  Source <SortIcon field="source_system" />
                </th>
                <th className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Key Attributes
                </th>
                <th 
                  className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('entity_party_count')}
                >
                  Entity Parties <SortIcon field="entity_party_count" />
                </th>
                <th 
                  className="px-2 py-1 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('match_score')}
                >
                  Match Score <SortIcon field="match_score" />
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredAndSortedParties?.map((party) => (
                <tr key={party.party_id} className="hover:bg-gray-50">
                  <td className="px-2 py-1 whitespace-nowrap">
                    <Link
                      to={`/parties/${party.party_id}`}
                      className="font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline"
                    >
                      {party.party_id}
                    </Link>
                  </td>
                  <td className="px-2 py-1">
                    <div className="text-xs text-gray-900">{party.display_name || '-'}</div>
                  </td>
                  <td className="px-2 py-1">
                    <div className="text-xs">
                      <div className="inline-block px-1.5 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">{party.source_system}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{party.source_table}</div>
                    </div>
                  </td>
                  <td className="px-2 py-1">
                    <div className="text-xs text-gray-600 space-y-0.5">
                      {party.dob && <div>DOB: {party.dob}</div>}
                      {party.email && <div className="truncate max-w-[150px]">Email: {party.email}</div>}
                      {party.phone && <div>Phone: {party.phone}</div>}
                      {party.gov_id && <div>Gov ID: {party.gov_id}</div>}
                      {!party.dob && !party.email && !party.phone && !party.gov_id && (
                        <div className="text-gray-400">{party.attribute_count} attrs</div>
                      )}
                    </div>
                  </td>
                  <td className="px-2 py-1 whitespace-nowrap">
                    {party.entity_id ? (
                      <Link
                        to={`/entities/${party.entity_id}`}
                        className="inline-block px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded text-xs hover:bg-purple-200"
                      >
                        {party.entity_party_count} parties
                      </Link>
                    ) : (
                      <span className="text-xs text-gray-400">No entity</span>
                    )}
                  </td>
                  <td className="px-2 py-1 whitespace-nowrap">
                    {party.match_score !== null ? (
                      <div className="flex items-center">
                        <div className="w-12 bg-gray-200 rounded-full h-1.5 mr-1.5">
                          <div
                            className="bg-green-500 h-1.5 rounded-full"
                            style={{ width: `${party.match_score * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-700">{(party.match_score * 100).toFixed(0)}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-400">-</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredAndSortedParties && filteredAndSortedParties.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No parties found matching your filters</p>
          </div>
        )}
      </div>

      <div className="mt-2 text-xs text-gray-600">
        Showing {filteredAndSortedParties?.length || 0} of {parties?.length || 0} parties
      </div>
    </div>
  )
}
