import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import type { Party } from '../types'

interface ClusterTableProps {
  parties: Party[]
}

interface ClusterStats {
  cluster_id: string
  parties_in_entity: number
  total_parties: number
  source_systems: string[]
  party_types: string[]
}

export default function ClusterTable({ parties }: ClusterTableProps) {
  const clusterStats = useMemo(() => {
    // Group parties by cluster_id
    const clusterMap = new Map<string, Party[]>()
    
    parties.forEach(party => {
      const clusterId = party.cluster_id || 'NO_CLUSTER'
      if (!clusterMap.has(clusterId)) {
        clusterMap.set(clusterId, [])
      }
      clusterMap.get(clusterId)!.push(party)
    })
    
    // Convert to stats array
    const stats: ClusterStats[] = []
    clusterMap.forEach((clusterParties, clusterId) => {
      const sourceSystems = [...new Set(clusterParties.map(p => p.source_system))]
      const partyTypes = [...new Set(clusterParties.map(p => p.party_type))]
      
      stats.push({
        cluster_id: clusterId,
        parties_in_entity: clusterParties.length,
        total_parties: clusterParties.length, // Will be updated with actual cluster size from backend
        source_systems: sourceSystems,
        party_types: partyTypes,
      })
    })
    
    return stats.sort((a, b) => b.parties_in_entity - a.parties_in_entity)
  }, [parties])

  if (clusterStats.length === 0) {
    return (
      <div className="p-8 text-center text-gray-500">
        <p>No cluster information available</p>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <h2 className="text-lg font-semibold text-gray-900">Clusters</h2>
        <p className="text-sm text-gray-600 mt-1">
          Business relationship groups that contain parties in this entity
        </p>
      </div>

      <div className="flex-1 overflow-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cluster ID
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Parties in Entity
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Total Parties
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Source Systems
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Party Types
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {clusterStats.map((cluster) => (
              <tr key={cluster.cluster_id} className="hover:bg-gray-50">
                <td className="px-4 py-3 whitespace-nowrap">
                  <Link
                    to={`/clusters/${cluster.cluster_id}`}
                    className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    {cluster.cluster_id}
                  </Link>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-sm font-semibold text-gray-900">
                      {cluster.parties_in_entity}
                    </span>
                    <span className="ml-2 text-xs text-gray-500">
                      ({((cluster.parties_in_entity / cluster.total_parties) * 100).toFixed(0)}%)
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className="text-sm text-gray-700">
                    {cluster.total_parties}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {cluster.source_systems.map((system, idx) => (
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
                    {cluster.party_types.map((type, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="text-sm text-gray-600">
          <p>
            <strong>{clusterStats.length}</strong> {clusterStats.length === 1 ? 'cluster' : 'clusters'} contribute
            to this entity
          </p>
        </div>
      </div>
    </div>
  )
}
