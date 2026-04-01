import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeftIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline'
import { clusterApi } from '../api/client'
import PartyGraph from '../components/PartyGraph'
import PartyAttributesPanel from '../components/PartyAttributesPanel'
import EvidencePanel from '../components/EvidencePanel'
import AttributeTable from '../components/AttributeTable'
import PartyAttributeTable from '../components/PartyAttributeTable'
import EntityTableForCluster from '../components/EntityTableForCluster'

export default function ClusterDetail() {
  const { clusterId } = useParams<{ clusterId: string }>()
  const [selectedPartyId, setSelectedPartyId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'graph' | 'attributes' | 'parties' | 'entities' | 'evidence'>('graph')

  const { data: clusterDetail, isLoading, error } = useQuery({
    queryKey: ['cluster', clusterId],
    queryFn: () => clusterApi.getClusterDetail(clusterId!),
    enabled: !!clusterId,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading cluster details...</p>
        </div>
      </div>
    )
  }

  if (error || !clusterDetail) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ShieldExclamationIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Cluster</h3>
          <p className="text-gray-600">Unable to load cluster details.</p>
          <Link to="/" className="btn-primary mt-4 inline-block">
            Back to Dashboard
          </Link>
        </div>
      </div>
    )
  }

  const selectedParty = selectedPartyId 
    ? clusterDetail.parties.find(p => p.party_id === selectedPartyId)
    : null

  const clusterPartyCount = clusterDetail.parties.filter(p => p.in_cluster).length
  const totalPartyCount = clusterDetail.parties.length
  
  // Get unique entity IDs
  const entityIds = [...new Set(
    clusterDetail.parties
      .filter(p => p.in_entity)
      .map(p => (p as any).entity_id)
      .filter(id => id)
  )]

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white border-b border-gray-200 px-2 py-1">
        <div className="max-w-full mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Link to="/" className="text-gray-500 hover:text-gray-700">
                <ArrowLeftIcon className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-sm font-bold text-gray-900">
                  Cluster
                </h1>
                <p className="text-xs text-gray-500 font-mono">
                  {clusterId}
                </p>
                <p className="text-xs text-gray-500">
                  {clusterPartyCount} cluster parties • {totalPartyCount} total parties • {clusterDetail.match_evidence.length} evidence
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
            </div>
          </div>

          <div className="flex gap-1 mt-1">
            <button
              onClick={() => setActiveTab('graph')}
              className={`btn-secondary ${
                activeTab === 'graph' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Graph
            </button>
            <button
              onClick={() => setActiveTab('attributes')}
              className={`btn-secondary ${
                activeTab === 'attributes' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Attributes
            </button>
            <button
              onClick={() => setActiveTab('parties')}
              className={`btn-secondary ${
                activeTab === 'parties' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Parties
            </button>
            <button
              onClick={() => setActiveTab('entities')}
              className={`btn-secondary ${
                activeTab === 'entities' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Entities ({entityIds.length})
            </button>
            <button
              onClick={() => setActiveTab('evidence')}
              className={`btn-secondary ${
                activeTab === 'evidence' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Evidence ({clusterDetail.match_evidence.length})
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full px-2 py-1">
          <div className="h-full flex gap-2">
            <div className="flex-1 card overflow-hidden flex flex-col">
              {activeTab === 'graph' && (
                <PartyGraph
                  parties={clusterDetail.parties}
                  matchEvidence={clusterDetail.match_evidence}
                  blocking={[]}
                  relationships={clusterDetail.relationships}
                  focusPartyId={null}
                  onPartySelect={setSelectedPartyId}
                />
              )}
              {activeTab === 'attributes' && (
                <AttributeTable
                  parties={clusterDetail.parties}
                />
              )}
              {activeTab === 'parties' && (
                <PartyAttributeTable
                  parties={clusterDetail.parties}
                />
              )}
              {activeTab === 'entities' && (
                <EntityTableForCluster
                  parties={clusterDetail.parties}
                />
              )}
              {activeTab === 'evidence' && (
                <EvidencePanel
                  evidence={clusterDetail.match_evidence}
                />
              )}
            </div>

            {selectedParty && activeTab === 'graph' && (
              <div className="w-80 flex-shrink-0">
                <PartyAttributesPanel
                  party={selectedParty}
                  onClose={() => setSelectedPartyId(null)}
                />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
