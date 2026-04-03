import type { Party } from '../types'

interface PartyAttributeDetailProps {
  party: Party
}

export default function PartyAttributeDetail({ party }: PartyAttributeDetailProps) {
  const displayAttrs = party.attributes
    .filter(a => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE', 'ATTR_GENDER'].includes(a.attribute_type))
    .sort((a, b) => a.attribute_type.localeCompare(b.attribute_type))

  return (
    <div className="h-full flex flex-col p-4">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-gray-900 mb-2">Party Attributes</h2>
        <div className="bg-gray-50 border border-gray-200 rounded p-3 space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700 min-w-[140px]">Party ID:</span>
            <span className="font-mono text-sm text-gray-900">{party.party_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700 min-w-[140px]">Source System:</span>
            <span className="text-sm text-gray-900">{party.source_system}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700 min-w-[140px]">Source Table:</span>
            <span className="text-sm text-gray-900">{party.source_table}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold text-gray-700 min-w-[140px]">Party Type:</span>
            <span className="badge bg-gray-100 text-gray-800">{party.party_type}</span>
          </div>
          {party.cluster_id && (
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-gray-700 min-w-[140px]">Cluster ID:</span>
              <span className="font-mono text-xs text-blue-600">{party.cluster_id}</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <h3 className="text-sm font-bold text-gray-900 mb-2">Attributes ({displayAttrs.length})</h3>
        <div className="space-y-2">
          {displayAttrs.map((attr, idx) => (
            <div key={idx} className="bg-white border border-gray-200 rounded p-3">
              <div className="flex items-start gap-3">
                <div className="flex-1">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
                    {attr.attribute_type.replace('ATTR_', '').replace(/_/g, ' ')}
                  </div>
                  <div className="font-mono text-sm text-gray-900 font-medium">
                    {attr.standardized_value}
                  </div>
                </div>
                {attr.source_system && (
                  <div className="badge bg-blue-100 text-blue-700 text-xs">
                    {attr.source_system}
                  </div>
                )}
              </div>
            </div>
          ))}
          {displayAttrs.length === 0 && (
            <div className="text-center p-8 text-gray-500">
              <p>No attributes available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
