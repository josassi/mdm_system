import { XMarkIcon, ShieldCheckIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import type { Party } from '../types'

interface PartyAttributesPanelProps {
  party: Party
  onClose: () => void
}

export default function PartyAttributesPanel({ party, onClose }: PartyAttributesPanelProps) {
  const getAttributeLabel = (attrType: string) => {
    const labels: Record<string, string> = {
      'ATTR_FIRST_NAME': 'First Name',
      'ATTR_LAST_NAME': 'Last Name',
      'ATTR_DOB': 'Date of Birth',
      'ATTR_EMAIL': 'Email',
      'ATTR_PHONE': 'Phone',
      'ATTR_ADDRESS': 'Address',
      'ATTR_GOV_ID': 'Government ID',
      'ATTR_GOV_ID_TYPE': 'ID Type',
      'ATTR_GENDER': 'Gender',
    }
    return labels[attrType] || attrType
  }

  const getSubtypeLabel = (subtypeId: string) => {
    const labels: Record<string, string> = {
      'SUB_HKID': 'HKID',
      'SUB_PASSPORT': 'Passport',
      'SUB_DRIVERS_LICENSE': 'Driver\'s License',
      'SUB_GENDER': 'Gender',
      'SUB_DOB': 'Date of Birth',
    }
    return labels[subtypeId] || subtypeId
  }

  return (
    <div className="card h-full flex flex-col">
      <div className="p-2 border-b border-gray-200 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-900">Party Details</h3>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 transition-colors"
        >
          <XMarkIcon className="h-4 w-4" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <div className="space-y-2">
          <div>
            <h4 className="text-xs font-semibold text-gray-700 mb-1">Source Information</h4>
            <div className="bg-gray-50 rounded p-2 space-y-1 text-xs">
              <div>
                <span className="text-gray-500">Party ID:</span>
                <span className="ml-1 font-medium text-gray-900 font-mono text-xs">{party.party_id}</span>
              </div>
              <div>
                <span className="text-gray-500">Type:</span>
                <span className="ml-1 font-medium text-gray-900">{party.party_type}</span>
              </div>
              <div>
                <span className="text-gray-500">System:</span>
                <span className="ml-1 font-medium text-gray-900">{party.source_system}</span>
              </div>
              <div>
                <span className="text-gray-500">Table:</span>
                <span className="ml-2 font-medium text-gray-900">{party.source_table}</span>
              </div>
              {party.resolution_method && (
                <div>
                  <span className="text-gray-500">Resolution:</span>
                  <span className="ml-2 font-medium text-gray-900">{party.resolution_method}</span>
                </div>
              )}
              {party.resolution_score !== undefined && (
                <div>
                  <span className="text-gray-500">Score:</span>
                  <span className="ml-2 font-medium text-gray-900">
                    {(party.resolution_score * 100).toFixed(1)}%
                  </span>
                </div>
              )}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-semibold text-gray-700 mb-1">Attributes ({party.attributes.length})</h4>
            <div className="overflow-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th className="w-24">Type</th>
                    <th>Value</th>
                    <th className="w-20">Source</th>
                    <th className="w-12 text-center">Conf</th>
                    <th className="w-12 text-center">Qual</th>
                  </tr>
                </thead>
                <tbody>
                  {party.attributes.map((attr, index) => (
                    <tr key={index}>
                      <td className="font-medium">
                        <div className="flex items-center gap-1">
                          {attr.is_pii && <ShieldCheckIcon className="h-3 w-3 text-amber-500 flex-shrink-0" />}
                          <span>{attr.attribute_type?.replace('ATTR_', '')}</span>
                        </div>
                      </td>
                      <td>
                        <div className="font-mono text-gray-900">{attr.standardized_value}</div>
                        {attr.raw_value !== attr.standardized_value && (
                          <div className="text-gray-500 italic">{attr.raw_value}</div>
                        )}
                      </td>
                      <td className="text-gray-600">{attr.source_column}</td>
                      <td className="text-center">
                        <span className={`font-medium ${
                          attr.confidence_score >= 0.9 ? 'text-green-600' :
                          attr.confidence_score >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {(attr.confidence_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td className="text-center">
                        <span className={`font-medium ${
                          attr.quality_score >= 0.9 ? 'text-green-600' :
                          attr.quality_score >= 0.7 ? 'text-yellow-600' : 'text-red-600'
                        }`}>
                          {(attr.quality_score * 100).toFixed(0)}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {party.attributes.length === 0 && (
            <div className="text-center py-8">
              <ExclamationCircleIcon className="h-12 w-12 text-gray-300 mx-auto mb-2" />
              <p className="text-sm text-gray-500">No attributes found</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
