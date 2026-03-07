import { useState, useMemo } from 'react'
import { MagnifyingGlassIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import type { Party } from '../types'

interface AttributeTableProps {
  parties: Party[]
}

interface AttributeRow {
  attribute_type: string
  attribute_label: string
  values: {
    party_id: string
    source_system: string
    source_table: string
    value: string
  }[]
  unique_values: number
  match_percentage: number
  total_occurrences: number
}

type SortField = 'attribute_label' | 'unique_values' | 'match_percentage' | 'total_occurrences'
type SortDirection = 'asc' | 'desc'

export default function AttributeTable({ parties }: AttributeTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSource, setFilterSource] = useState<'all' | string>('all')
  const [sortField, setSortField] = useState<SortField>('attribute_label')
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc')

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

  const attributeRows = useMemo(() => {
    const attrMap = new Map<string, AttributeRow>()

    // Collect all attributes from all parties
    parties.forEach(party => {
      party.attributes
        .filter(attr => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE', 'ATTR_GENDER'].includes(attr.attribute_type))
        .forEach(attr => {
          const key = attr.attribute_type
          
          if (!attrMap.has(key)) {
            attrMap.set(key, {
              attribute_type: attr.attribute_type,
              attribute_label: attr.attribute_type.replace('ATTR_', '').replace(/_/g, ' '),
              values: [],
              unique_values: 0,
              match_percentage: 0,
              total_occurrences: 0,
            })
          }

          const row = attrMap.get(key)!
          row.values.push({
            party_id: party.party_id,
            source_system: party.source_system,
            source_table: party.source_table,
            value: attr.standardized_value,
          })
        })
    })

    // Calculate statistics for each attribute
    attrMap.forEach(row => {
      row.total_occurrences = row.values.length
      const uniqueValues = new Set(row.values.map(v => v.value.toLowerCase()))
      row.unique_values = uniqueValues.size
      
      // Match percentage: how many parties have the most common value
      const valueCounts = new Map<string, number>()
      row.values.forEach(v => {
        const normalized = v.value.toLowerCase()
        valueCounts.set(normalized, (valueCounts.get(normalized) || 0) + 1)
      })
      
      const maxCount = Math.max(...Array.from(valueCounts.values()))
      row.match_percentage = row.total_occurrences > 0 ? (maxCount / row.total_occurrences) * 100 : 0
    })

    return Array.from(attrMap.values())
  }, [parties])

  const sourceSystems = useMemo(() => {
    const systems = new Set<string>()
    parties.forEach(p => systems.add(p.source_system))
    return Array.from(systems).sort()
  }, [parties])

  const filteredAndSortedRows = useMemo(() => {
    return attributeRows
      .filter(row => {
        const matchesSearch = !searchQuery || 
          row.attribute_label.toLowerCase().includes(searchQuery.toLowerCase())
        
        const matchesSource = filterSource === 'all' || 
          row.values.some(v => v.source_system === filterSource)
        
        return matchesSearch && matchesSource
      })
      .sort((a, b) => {
        let aVal: any = a[sortField]
        let bVal: any = b[sortField]
        
        if (sortField === 'attribute_label') {
          aVal = aVal.toLowerCase()
          bVal = bVal.toLowerCase()
        }
        
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
        return 0
      })
  }, [attributeRows, searchQuery, filterSource, sortField, sortDirection])

  const getMatchColor = (percentage: number) => {
    if (percentage === 100) return 'text-green-600 bg-green-50'
    if (percentage >= 50) return 'text-orange-600 bg-orange-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="h-full flex flex-col p-3">
      <div className="mb-3">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Attribute Analysis</h2>
        <p className="text-xs text-gray-600">
          All attributes across {parties.length} parties
        </p>
      </div>

      <div className="flex gap-2 mb-3">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search attributes..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
        
        <select
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="px-3 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="all">All Sources</option>
          {sourceSystems.map(system => (
            <option key={system} value={system}>{system}</option>
          ))}
        </select>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('attribute_label')}>
                Attribute <SortIcon field="attribute_label" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('total_occurrences')}>
                Occurrences <SortIcon field="total_occurrences" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('unique_values')}>
                Unique Values <SortIcon field="unique_values" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('match_percentage')}>
                Match % <SortIcon field="match_percentage" />
              </th>
              <th>Values by Party</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedRows.map((row) => (
              <tr key={row.attribute_type}>
                <td className="font-medium text-gray-900">{row.attribute_label}</td>
                <td className="text-center">
                  <span className="badge bg-blue-100 text-blue-700">{row.total_occurrences}</span>
                </td>
                <td className="text-center">
                  <span className={`badge ${
                    row.unique_values === 1 ? 'bg-green-100 text-green-700' : 
                    row.unique_values <= row.total_occurrences / 2 ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {row.unique_values}
                  </span>
                </td>
                <td className="text-center">
                  <span className={`badge font-semibold ${getMatchColor(row.match_percentage)}`}>
                    {row.match_percentage.toFixed(0)}%
                  </span>
                </td>
                <td>
                  <div className="space-y-1 max-w-lg">
                    {row.values.map((v, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <span className="font-mono text-gray-900 font-medium">{v.value}</span>
                        <span className="text-gray-400">•</span>
                        <span className="text-gray-600">{v.source_system}.{v.source_table}</span>
                      </div>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedRows.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-gray-500">No attributes found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}
