import { Link } from 'react-router-dom'
import type { Party } from '../types'

interface EntityDetailProps {
  entityId: string | null
  parties: Party[]
}

export default function EntityDetail({ entityId, parties }: EntityDetailProps) {
  if (!entityId) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center p-8 text-gray-500">
          <p>This party is not part of any entity</p>
        </div>
      </div>
    )
  }

  const entityParties = parties.filter(p => p.in_entity)
  const sourceSystems = [...new Set(entityParties.map(p => p.source_system))]
  const partyTypes = [...new Set(entityParties.map(p => p.party_type))]
  
  // Get all unique clusters from entity parties
  const clusterIds = [...new Set(entityParties.map(p => p.cluster_id).filter(Boolean))]

  return (
    <div className="h-full flex flex-col p-2">
      <div className="mb-2">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Entity Details</h2>
        <div className="bg-purple-50 border border-purple-200 rounded p-2 text-xs space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Entity ID:</span>
            <Link
              to={`/entities/${entityId}`}
              className="font-mono text-purple-600 hover:text-purple-800 hover:underline truncate"
            >
              {entityId}
            </Link>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Parties:</span>
            <span className="badge bg-purple-100 text-purple-700 text-xs">{entityParties.length}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Systems:</span>
            <div className="flex flex-wrap gap-1">
              {sourceSystems.map((system, idx) => (
                <span key={idx} className="badge bg-blue-100 text-blue-800 text-xs">{system}</span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Types:</span>
            <div className="flex flex-wrap gap-1">
              {partyTypes.map((type, idx) => (
                <span key={idx} className="badge bg-gray-100 text-gray-800 text-xs">{type}</span>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Clusters:</span>
            <div className="flex flex-wrap gap-1">
              {clusterIds.map((clusterId, idx) => (
                <Link key={idx} to={`/clusters/${clusterId}`} className="badge bg-blue-100 text-blue-700 text-xs hover:bg-blue-200 truncate max-w-[200px]">
                  {clusterId}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <h3 className="text-xs font-bold text-gray-900 mb-1">
          Parties in Entity ({entityParties.length})
        </h3>
        <div className="grid grid-cols-2 gap-1">
          {entityParties.map((party) => (
            <div key={party.party_id} className="bg-white border border-gray-200 rounded p-1.5 hover:bg-gray-50">
              <Link
                to={`/parties/${party.party_id}`}
                className="font-mono text-xs text-blue-600 hover:text-blue-800 hover:underline block truncate"
              >
                {party.party_id}
              </Link>
              <div className="flex gap-1 mt-0.5">
                <span className="badge bg-blue-100 text-blue-700 text-xs">
                  {party.source_system}
                </span>
                <span className="badge bg-gray-100 text-gray-800 text-xs">
                  {party.party_type}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
