import { memo } from 'react'
import { Handle, Position } from 'reactflow'
import { ShieldExclamationIcon } from '@heroicons/react/24/solid'
import { useNavigate } from 'react-router-dom'
import type { Party } from '../types'

interface PartyNodeData {
  party: Party
  isSelected: boolean
  hasConflict: boolean
  onClick: () => void
}

function PartyNode({ data }: { data: PartyNodeData }) {
  const { party, isSelected, hasConflict, onClick } = data
  const navigate = useNavigate()
  
  // Filter out metadata/non-matching attributes, then show first 10
  const displayAttrs = party.attributes
    .filter(a => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE', 'ATTR_GENDER'].includes(a.attribute_type))
    .slice(0, 10)
  
  const handlePartyIdClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    navigate(`/parties/${party.party_id}`)
  }

  const handleClusterIdClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (party.cluster_id) {
      navigate(`/clusters/${party.cluster_id}`)
    }
  }

  const handleEntityIdClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    const entityId = (party as any).entity_id
    if (entityId) {
      navigate(`/entities/${entityId}`)
    }
  }

  return (
    <div
      onClick={onClick}
      className={`cursor-pointer transition-all relative ${
        isSelected ? 'scale-105' : 'hover:scale-102'
      }`}
    >
      {/* Invisible handles at center for all connections */}
      <Handle 
        type="source" 
        position={Position.Bottom}
        style={{ 
          background: 'transparent',
          border: 'none',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      />
      <Handle 
        type="target" 
        position={Position.Top}
        style={{ 
          background: 'transparent',
          border: 'none',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
        }}
      />
      
      <div
        className={`rounded p-2 shadow min-w-[200px] max-w-[280px] ${
          hasConflict
            ? 'bg-red-50 border border-red-400'
            : isSelected
            ? 'bg-blue-50 border border-blue-400'
            : 'bg-white border border-gray-300'
        }`}
      >
        <div className="flex items-center gap-1 mb-0.5">
          {hasConflict && <ShieldExclamationIcon className="h-3 w-3 text-red-600 flex-shrink-0" />}
          <h3 className="font-semibold text-xs text-gray-900 truncate flex-1">
            {party.source_system} • {party.source_table}
          </h3>
          {party.resolution_score !== undefined && (
            <span className="text-xs font-medium text-gray-600">
              {(party.resolution_score * 100).toFixed(0)}%
            </span>
          )}
        </div>
        
        <div 
          className="font-mono text-[10px] text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
          onClick={handlePartyIdClick}
          title="Click to view party details"
        >
          Party: {party.party_id}
        </div>
        
        {party.cluster_id && (
          <div 
            className="font-mono text-[9px] text-blue-600 hover:text-blue-800 hover:underline cursor-pointer"
            onClick={handleClusterIdClick}
            title="Click to view cluster details"
          >
            Cluster: {party.cluster_id}
          </div>
        )}
        
        {(party as any).entity_id && (
          <div 
            className="font-mono text-[9px] text-purple-600 hover:text-purple-800 hover:underline cursor-pointer mb-1"
            onClick={handleEntityIdClick}
            title="Click to view entity details"
          >
            Entity: {(party as any).entity_id}
          </div>
        )}
        
        <div className="border-t border-gray-200 pt-1 space-y-0.5">
          {displayAttrs.map((attr, idx) => (
            <div key={idx} className="flex text-xs">
              <span className="text-gray-500 w-16 truncate">{attr.attribute_type?.replace('ATTR_', '')}:</span>
              <span className="text-gray-900 font-medium truncate flex-1">{attr.standardized_value}</span>
            </div>
          ))}
          {party.attributes.length > displayAttrs.length && (
            <div className="text-xs text-gray-400 italic">
              +{party.attributes.length - displayAttrs.length} more
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default memo(PartyNode)
