import { useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeftIcon, ShieldExclamationIcon } from '@heroicons/react/24/outline'
import { entityApi } from '../api/client'
import EntityGraph from '../components/EntityGraph'
import PartyAttributesPanel from '../components/PartyAttributesPanel'
import EvidencePanel from '../components/EvidencePanel'
import BlockingPanel from '../components/BlockingPanel'
import AttributeTable from '../components/AttributeTable'
import PartyAttributeTable from '../components/PartyAttributeTable'

export default function EntityDetail() {
  const { entityId } = useParams<{ entityId: string }>()
  const navigate = useNavigate()
  const [selectedPartyId, setSelectedPartyId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'graph' | 'attributes' | 'parties' | 'evidence' | 'blocking'>('graph')

  const { data: entityDetail, isLoading, error } = useQuery({
    queryKey: ['entity', entityId],
    queryFn: () => entityApi.getEntityDetail(entityId!),
    enabled: !!entityId,
  })

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          <p className="mt-4 text-gray-600">Loading entity details...</p>
        </div>
      </div>
    )
  }

  if (error || !entityDetail) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card p-8 text-center">
          <ShieldExclamationIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Error Loading Entity</h3>
          <p className="text-gray-600">Unable to load entity details.</p>
          <button onClick={() => navigate(-1)} className="btn-primary mt-4 inline-block">
            Back to Previous Page
          </button>
        </div>
      </div>
    )
  }

  const selectedParty = selectedPartyId 
    ? entityDetail.parties?.find(p => p.party_id === selectedPartyId)
    : null

  const hasConflicts = (entityDetail.blocking?.length ?? 0) > 0

  return (
    <div className="h-screen flex flex-col">
      <div className="bg-white border-b border-gray-200 px-2 py-1">
        <div className="max-w-full mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <button 
                onClick={() => navigate(-1)} 
                className="text-gray-500 hover:text-gray-700 transition-colors"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
              <div>
                <h1 className="text-sm font-bold text-gray-900">
                  Entity {entityId?.substring(0, 12)}
                </h1>
                <p className="text-xs text-gray-500">
                  {entityDetail.parties?.length ?? 0} parties • {entityDetail.match_evidence?.length ?? 0} evidence
                  {hasConflicts && <span className="text-red-600"> • {entityDetail.blocking?.length ?? 0} conflicts</span>}
                </p>
              </div>
            </div>
            
            {hasConflicts && (
              <div className="badge badge-danger">
                <ShieldExclamationIcon className="h-3 w-3 mr-1" />
                Conflicts
              </div>
            )}
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
              onClick={() => setActiveTab('evidence')}
              className={`btn-secondary ${
                activeTab === 'evidence' ? 'bg-primary-600 text-white' : ''
              }`}
            >
              Evidence ({entityDetail.match_evidence?.length ?? 0})
            </button>
            <button
              onClick={() => setActiveTab('blocking')}
              className={`btn-secondary ${
                activeTab === 'blocking' ? 'bg-red-600 text-white' : hasConflicts ? 'bg-red-100 text-red-700' : ''
              }`}
            >
              Blocking ({entityDetail.blocking?.length ?? 0})
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full px-2 py-1">
          <div className="h-full flex gap-2">
            <div className="flex-1 card overflow-hidden flex flex-col">
              {activeTab === 'graph' && (
                <EntityGraph
                  parties={entityDetail.parties ?? []}
                  matchEvidence={entityDetail.match_evidence ?? []}
                  blocking={entityDetail.blocking ?? []}
                  relationships={entityDetail.relationships ?? []}
                  selectedPartyId={selectedPartyId}
                  onPartySelect={setSelectedPartyId}
                />
              )}
              {activeTab === 'attributes' && (
                <AttributeTable
                  parties={entityDetail.parties ?? []}
                />
              )}
              {activeTab === 'parties' && (
                <PartyAttributeTable
                  parties={entityDetail.parties ?? []}
                />
              )}
              {activeTab === 'evidence' && (
                <EvidencePanel
                  evidence={entityDetail.match_evidence ?? []}
                />
              )}
              {activeTab === 'blocking' && (
                <BlockingPanel
                  blocking={entityDetail.blocking ?? []}
                  parties={entityDetail.parties ?? []}
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
