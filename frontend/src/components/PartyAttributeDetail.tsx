import type { Party } from '../types'

interface PartyAttributeDetailProps {
  party: Party
}

export default function PartyAttributeDetail({ party }: PartyAttributeDetailProps) {
  const displayAttrs = party.attributes
    .filter(a => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE', 'ATTR_GENDER'].includes(a.attribute_type))
    .sort((a, b) => a.attribute_type.localeCompare(b.attribute_type))

  return (
    <div className="h-full flex flex-col p-2">
      <div className="mb-2">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Party Attributes</h2>
        <div className="bg-gray-50 border border-gray-200 rounded p-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Party ID:</span>
            <span className="font-mono text-gray-900 truncate">{party.party_id}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">System:</span>
            <span className="text-gray-900">{party.source_system}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Table:</span>
            <span className="text-gray-900">{party.source_table}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-semibold text-gray-700 min-w-[80px]">Type:</span>
            <span className="badge bg-gray-100 text-gray-800 text-xs">{party.party_type}</span>
          </div>
          {party.cluster_id && (
            <div className="flex items-center gap-2 col-span-2">
              <span className="font-semibold text-gray-700 min-w-[80px]">Cluster:</span>
              <span className="font-mono text-blue-600 truncate">{party.cluster_id}</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <h3 className="text-xs font-bold text-gray-900 mb-1">Attributes ({displayAttrs.length})</h3>
        <div className="grid grid-cols-2 gap-2">
          {displayAttrs.map((attr, idx) => (
            <div key={idx} className="bg-white border border-gray-200 rounded p-2">
              <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-0.5 truncate">
                {attr.attribute_type.replace('ATTR_', '').replace(/_/g, ' ')}
              </div>
              <div className="font-mono text-xs text-gray-900 font-medium truncate">
                {attr.standardized_value}
              </div>
              {attr.source_system && (
                <div className="badge bg-blue-100 text-blue-700 text-xs mt-0.5 inline-block">
                  {attr.source_system}
                </div>
              )}
            </div>
          ))}
          {displayAttrs.length === 0 && (
            <div className="col-span-2 text-center p-4 text-gray-500 text-xs">
              <p>No attributes available</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
