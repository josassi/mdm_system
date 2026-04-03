import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeftIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline'
import { partyApi } from '../api/client'
import EvidencePanel from '../components/EvidencePanel'
import BlockingPanel from '../components/BlockingPanel'
import AttributeTable from '../components/AttributeTable'
import ClusterTable from '../components/ClusterTable'
import EntityTableForCluster from '../components/EntityTableForCluster'

export default function PartyDetail() {
  const { partyId } = useParams<{ partyId: string }>()
  const [activeTab, setActiveTab] = useState<'attributes' | 'entities' | 'clusters' | 'evidence' | 'blocking'>('attributes')

  const { data: partyDetail, isLoading, error } = useQuery({
    queryKey: ['party', partyId],
    queryFn: () => partyApi.getPartyDetail(partyId!),
    enabled: !!partyId,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading party details...</p>
        </div>
      </div>
    )
  }

  if (error || !partyDetail) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ShieldExclamationIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Party</h3>
          <p className="text-gray-600">Unable to load party details.</p>
          <Link to="/" className="btn-primary mt-4 inline-block">
            Back to Entities
          </Link>
        </div>
      </div>
    )
  }

  const hasConflicts = partyDetail.blocking.length > 0
  const focusParty = partyDetail.parties.find(p => p.is_focus)
  const clusterPartyCount = partyDetail.parties.filter(p => p.in_cluster).length
  const entityPartyCount = partyDetail.parties.filter(p => p.in_entity).length

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
                  Party: {focusParty?.source_system}.{focusParty?.source_table}
                </h1>
                <p className="text-xs text-gray-500 font-mono">
                  {partyId}
                </p>
                <p className="text-xs text-gray-500">
                  Cluster: {clusterPartyCount} parties • Entity: {entityPartyCount} parties • {partyDetail.match_evidence.length} evidence
                  {hasConflicts && <span className="text-red-600"> • {partyDetail.blocking.length} conflicts</span>}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {partyDetail.cluster_id && (
                <div className="badge bg-blue-100 text-blue-700 text-xs">
                  Cluster
                </div>
              )}
              {partyDetail.entity_id && (
                <Link 
                  to={`/entities/${partyDetail.entity_id}`}
                  className="badge bg-purple-100 text-purple-700 text-xs hover:bg-purple-200"
                >
                  View Entity
                </Link>
              )}
              {hasConflicts && (
                <div className="badge badge-danger">
                  <ShieldExclamationIcon className="h-3 w-3 mr-1" />
                  Conflicts
                </div>
              )}
            </div>
          </div>

          <div className="flex gap-1 mt-1">
            <button
              onClick={() => setActiveTab('attributes')}
              className={`btn-secondary ${
                activeTab === 'attributes' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Attributes
            </button>
            <button
              onClick={() => setActiveTab('entities')}
              className={`btn-secondary ${
                activeTab === 'entities' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Entities
            </button>
            <button
              onClick={() => setActiveTab('clusters')}
              className={`btn-secondary ${
                activeTab === 'clusters' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Clusters
            </button>
            <button
              onClick={() => setActiveTab('evidence')}
              className={`btn-secondary ${
                activeTab === 'evidence' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Evidence ({partyDetail.match_evidence.length})
            </button>
            <button
              onClick={() => setActiveTab('blocking')}
              className={`btn-secondary ${
                activeTab === 'blocking' ? 'bg-red-600 text-white' : hasConflicts ? 'bg-red-100 text-red-700' : ''
              }`}
            >
              Blocking ({partyDetail.blocking.length})
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full px-2 py-1">
          <div className="h-full">
            <div className="h-full card overflow-hidden flex flex-col">
              {activeTab === 'attributes' && (
                <AttributeTable
                  parties={partyDetail.parties}
                />
              )}
              {activeTab === 'entities' && (
                <EntityTableForCluster
                  parties={partyDetail.parties}
                />
              )}
              {activeTab === 'clusters' && (
                <ClusterTable
                  parties={partyDetail.parties}
                />
              )}
              {activeTab === 'evidence' && (
                <EvidencePanel
                  evidence={partyDetail.match_evidence}
                />
              )}
              {activeTab === 'blocking' && (
                <BlockingPanel
                  blocking={partyDetail.blocking}
                  parties={partyDetail.parties}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
