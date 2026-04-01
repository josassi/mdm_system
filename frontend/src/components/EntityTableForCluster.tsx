import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import type { Party } from '../types'

interface EntityTableForClusterProps {
  parties: Party[]
}

interface EntityInfo {
  entity_id: string
  party_count: number
  party_ids: string[]
  source_systems: string[]
  party_types: string[]
}

export default function EntityTableForCluster({ parties }: EntityTableForClusterProps) {
  const entities = useMemo(() => {
    const entityMap = new Map<string, EntityInfo>()
    
    parties.forEach(party => {
      const entityId = (party as any).entity_id
      if (!entityId) return
      
      if (!entityMap.has(entityId)) {
        entityMap.set(entityId, {
          entity_id: entityId,
          party_count: 0,
          party_ids: [],
          source_systems: [],
          party_types: [],
        })
      }
      
      const entity = entityMap.get(entityId)!
      entity.party_count++
      entity.party_ids.push(party.party_id)
      
      if (!entity.source_systems.includes(party.source_system)) {
        entity.source_systems.push(party.source_system)
      }
      
      if (!entity.party_types.includes(party.party_type)) {
        entity.party_types.push(party.party_type)
      }
    })
    
    return Array.from(entityMap.values()).sort((a, b) => b.party_count - a.party_count)
  }, [parties])

  if (entities.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No entities formed from parties in this cluster</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Entities</h2>
        <p className="text-sm text-gray-600 mt-1">
          {entities.length} {entities.length === 1 ? 'entity' : 'entities'} formed from parties in this cluster
        </p>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Entity ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Parties
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source Systems
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Party Types
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Party IDs
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {entities.map((entity) => (
              <tr key={entity.entity_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <Link
                    to={`/entities/${entity.entity_id}`}
                    className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {entity.entity_id}
                  </Link>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="inline-flex items-center justify-center w-10 h-8 rounded font-bold text-sm bg-purple-100 text-purple-700">
                    {entity.party_count}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {entity.source_systems.map((system, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {system}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {entity.party_types.map((type, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-col gap-0.5">
                    {entity.party_ids.map((partyId, idx) => (
                      <Link
                        key={idx}
                        to={`/parties/${partyId}`}
                        className="font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline"
                      >
                        {partyId}
                      </Link>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
