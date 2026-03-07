import { ShieldExclamationIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline'
import type { Blocking, Party } from '../types'

interface BlockingPanelProps {
  blocking: Blocking[]
  parties: Party[]
}

export default function BlockingPanel({ blocking, parties }: BlockingPanelProps) {
  const getPartyName = (partyId: string) => {
    const party = parties.find(p => p.party_id === partyId)
    if (!party) return 'Unknown'
    
    const firstName = party.attributes.find(a => a.attribute_type === 'ATTR_FIRST_NAME')?.standardized_value
    const lastName = party.attributes.find(a => a.attribute_type === 'ATTR_LAST_NAME')?.standardized_value
    
    if (firstName && lastName) {
      return `${firstName} ${lastName}`
    }
    return party.source_system + ' - ' + party.source_table
  }

  const getReasonLabel = (reason: string) => {
    const labels: Record<string, string> = {
      'DIFFERENT_HKID': 'Conflicting HKID Numbers',
      'DIFFERENT_PASSPORT': 'Conflicting Passport Numbers',
      'GENDER_CONFLICT': 'Gender Mismatch with Same Name',
      'DOB_DIFFERENCE': 'Date of Birth Exceeds Threshold',
    }
    return labels[reason] || reason
  }

  const getReasonExplanation = (reason: string, details: Record<string, any>) => {
    switch (reason) {
      case 'DIFFERENT_HKID':
        return `Two parties have different HKID numbers (${details.party1_SUB_HKID || 'N/A'} vs ${details.party2_SUB_HKID || 'N/A'}), which should be unique per person.`
      case 'DIFFERENT_PASSPORT':
        return `Two parties have different passport numbers (${details.party1_SUB_PASSPORT || 'N/A'} vs ${details.party2_SUB_PASSPORT || 'N/A'}), which should be unique per person.`
      case 'GENDER_CONFLICT':
        return `Two parties with identical names (${details.shared_name}) have different genders (${details.party1_gender} vs ${details.party2_gender}).`
      case 'DOB_DIFFERENCE':
        return 'The date of birth difference between these parties exceeds the acceptable threshold.'
      default:
        return 'These parties have been blocked from matching due to conflicting information.'
    }
  }

  if (blocking.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <ShieldExclamationIcon className="h-12 w-12 text-green-300 mx-auto mb-2" />
          <p className="text-xs text-gray-500">No blocking conflicts</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-2">
      <div className="mb-2">
        <div className="flex items-center gap-1 mb-1">
          <ShieldExclamationIcon className="h-4 w-4 text-red-600" />
          <h2 className="text-sm font-bold text-gray-900">Blocking Conflicts ({blocking.length})</h2>
        </div>
        <div className="p-2 bg-red-50 border border-red-200 rounded text-xs">
          <div className="flex items-start gap-1">
            <ExclamationCircleIcon className="h-3 w-3 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="text-red-800">
              <p className="font-semibold">Steward Action Required</p>
              <p>Conflicts indicate false positive or data quality issues</p>
            </div>
          </div>
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Reason</th>
            <th>Party 1</th>
            <th>Party 2</th>
            <th>Rule</th>
            <th>Explanation</th>
            <th className="w-20 text-center">Source</th>
          </tr>
        </thead>
        <tbody>
          {blocking.map((block) => (
            <tr key={block.blocking_id} className="bg-red-50">
              <td>
                <div className="flex items-center gap-1">
                  <ShieldExclamationIcon className="h-3 w-3 text-red-600 flex-shrink-0" />
                  <span className="font-medium text-red-900">{getReasonLabel(block.blocking_reason_code)}</span>
                </div>
              </td>
              <td className="text-gray-700">{getPartyName(block.party_id_1)}</td>
              <td className="text-gray-700">{getPartyName(block.party_id_2)}</td>
              <td className="text-gray-600">
                {block.rule_info.rule_name || '-'}
              </td>
              <td className="text-xs text-red-900">
                {getReasonExplanation(block.blocking_reason_code, block.conflict_details)}
              </td>
              <td className="text-center">
                <span className={`badge ${
                  block.blocking_source === 'AUTOMATIC' ? 'badge-danger' : 'bg-purple-100 text-purple-800'
                }`}>
                  {block.blocking_source === 'AUTOMATIC' ? 'Auto' : 'Manual'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
