import { useState, useMemo } from 'react'
import { MagnifyingGlassIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline'
import type { Party } from '../types'

interface PartyAttributeTableProps {
  parties: Party[]
}

interface PartyRow {
  party_id: string
  source_system: string
  source_table: string
  party_type: string
  attribute_count: number
  attributes: {
    attribute_type: string
    attribute_label: string
    value: string
  }[]
}

type SortField = 'party_id' | 'source_system' | 'source_table' | 'attribute_count'
type SortDirection = 'asc' | 'desc'

export default function PartyAttributeTable({ parties }: PartyAttributeTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filterSource, setFilterSource] = useState<'all' | string>('all')
  const [filterTable, setFilterTable] = useState<'all' | string>('all')
  const [sortField, setSortField] = useState<SortField>('party_id')
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

  const partyRows = useMemo(() => {
    return parties.map(party => {
      const filteredAttributes = party.attributes
        .filter(attr => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE', 'ATTR_GENDER'].includes(attr.attribute_type))
        .map(attr => ({
          attribute_type: attr.attribute_type,
          attribute_label: attr.attribute_type.replace('ATTR_', '').replace(/_/g, ' '),
          value: attr.standardized_value,
        }))

      return {
        party_id: party.party_id,
        source_system: party.source_system,
        source_table: party.source_table,
        party_type: party.party_type,
        attribute_count: filteredAttributes.length,
        attributes: filteredAttributes.sort((a, b) => 
          a.attribute_label.localeCompare(b.attribute_label)
        ),
      }
    })
  }, [parties])

  const sourceSystems = useMemo(() => {
    const systems = new Set<string>()
    parties.forEach(p => systems.add(p.source_system))
    return Array.from(systems).sort()
  }, [parties])

  const sourceTables = useMemo(() => {
    const tables = new Set<string>()
    parties.forEach(p => tables.add(p.source_table))
    return Array.from(tables).sort()
  }, [parties])

  const filteredAndSortedRows = useMemo(() => {
    return partyRows
      .filter(row => {
        const matchesSearch = !searchQuery || 
          row.party_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
          row.source_system.toLowerCase().includes(searchQuery.toLowerCase()) ||
          row.source_table.toLowerCase().includes(searchQuery.toLowerCase())
        
        const matchesSource = filterSource === 'all' || row.source_system === filterSource
        const matchesTable = filterTable === 'all' || row.source_table === filterTable
        
        return matchesSearch && matchesSource && matchesTable
      })
      .sort((a, b) => {
        let aVal: any = a[sortField]
        let bVal: any = b[sortField]
        
        if (typeof aVal === 'string') {
          aVal = aVal.toLowerCase()
          bVal = bVal.toLowerCase()
        }
        
        if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1
        if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1
        return 0
      })
  }, [partyRows, searchQuery, filterSource, filterTable, sortField, sortDirection])

  return (
    <div className="h-full flex flex-col p-3">
      <div className="mb-3">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Party Details</h2>
        <p className="text-xs text-gray-600">
          All parties and their attributes ({parties.length} parties)
        </p>
      </div>

      <div className="flex gap-2 mb-3">
        <div className="flex-1 relative">
          <MagnifyingGlassIcon className="absolute left-2 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search parties..."
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
          <option value="all">All Systems</option>
          {sourceSystems.map(system => (
            <option key={system} value={system}>{system}</option>
          ))}
        </select>

        <select
          value={filterTable}
          onChange={(e) => setFilterTable(e.target.value)}
          className="px-3 py-1.5 text-xs border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <option value="all">All Tables</option>
          {sourceTables.map(table => (
            <option key={table} value={table}>{table}</option>
          ))}
        </select>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="data-table">
          <thead>
            <tr>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('party_id')}>
                Party ID <SortIcon field="party_id" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('source_system')}>
                System <SortIcon field="source_system" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('source_table')}>
                Table <SortIcon field="source_table" />
              </th>
              <th className="cursor-pointer hover:bg-gray-50" onClick={() => handleSort('attribute_count')}>
                Attributes <SortIcon field="attribute_count" />
              </th>
              <th>Attribute Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedRows.map((row) => (
              <tr key={row.party_id}>
                <td className="font-mono text-xs font-medium text-gray-900">{row.party_id}</td>
                <td className="text-sm text-gray-700">{row.source_system}</td>
                <td className="text-sm text-gray-700">{row.source_table}</td>
                <td className="text-center">
                  <span className="badge bg-blue-100 text-blue-700">{row.attribute_count}</span>
                </td>
                <td>
                  <div className="space-y-1 max-w-2xl">
                    {row.attributes.map((attr, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <span className="font-semibold text-gray-700 min-w-[120px]">{attr.attribute_label}:</span>
                        <span className="font-mono text-gray-900">{attr.value}</span>
                      </div>
                    ))}
                    {row.attributes.length === 0 && (
                      <span className="text-gray-400 italic text-xs">No attributes</span>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAndSortedRows.length === 0 && (
          <div className="p-8 text-center">
            <p className="text-gray-500">No parties found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}
