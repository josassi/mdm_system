import { XMarkIcon } from '@heroicons/react/24/outline'
import type { Party } from '../types'

interface EdgeDetailsModalProps {
  party1: Party
  party2: Party
  onClose: () => void
}

export default function EdgeDetailsModal({ party1, party2, onClose }: EdgeDetailsModalProps) {
  const compareAttributes = () => {
    const allAttrTypes = new Set<string>()
    party1.attributes.forEach(a => a.attribute_type && allAttrTypes.add(a.attribute_type))
    party2.attributes.forEach(a => a.attribute_type && allAttrTypes.add(a.attribute_type))

    // Filter out metadata attributes
    const filteredAttrTypes = Array.from(allAttrTypes).filter(
      type => !['ATTR_GOV_ID_TYPE', 'ATTR_RELATIONSHIP_TYPE'].includes(type)
    )

    const comparisons = filteredAttrTypes.map(attrType => {
      const attr1 = party1.attributes.find(a => a.attribute_type === attrType)
      const attr2 = party2.attributes.find(a => a.attribute_type === attrType)
      
      const value1 = attr1?.standardized_value || null
      const value2 = attr2?.standardized_value || null
      
      let status: 'match' | 'mismatch' | 'missing' = 'missing'
      if (value1 && value2) {
        status = value1 === value2 ? 'match' : 'mismatch'
      } else if (value1 || value2) {
        status = 'missing'
      }

      return {
        attribute: attrType.replace('ATTR_', ''),
        value1,
        value2,
        status,
      }
    }).sort((a, b) => {
      const order = { match: 0, mismatch: 1, missing: 2 }
      return order[a.status] - order[b.status]
    })

    return comparisons
  }

  const comparisons = compareAttributes()
  const matchCount = comparisons.filter(c => c.status === 'match').length
  const totalCount = comparisons.filter(c => c.value1 && c.value2).length

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded shadow-lg max-w-3xl w-full max-h-[80vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between p-3 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-900">Attribute Comparison</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-3">
          <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
            <div className="bg-blue-50 p-2 rounded">
              <div className="font-semibold text-gray-700">Party 1</div>
              <div className="text-gray-900">{party1.party_id}</div>
              <div className="text-gray-500">{party1.source_system} • {party1.source_table}</div>
            </div>
            <div className="bg-blue-50 p-2 rounded">
              <div className="font-semibold text-gray-700">Party 2</div>
              <div className="text-gray-900">{party2.party_id}</div>
              <div className="text-gray-500">{party2.source_system} • {party2.source_table}</div>
            </div>
          </div>

          <div className="bg-gray-50 p-2 rounded mb-3 text-xs">
            <span className="font-semibold">Match Score: </span>
            <span className="text-green-600 font-bold">{matchCount}/{totalCount}</span>
            <span className="text-gray-600"> ({totalCount > 0 ? ((matchCount / totalCount) * 100).toFixed(1) : 0}% match)</span>
          </div>

          <div className="overflow-auto max-h-96">
            <table className="data-table">
              <thead>
                <tr>
                  <th className="w-32">Attribute</th>
                  <th>Party 1 Value</th>
                  <th>Party 2 Value</th>
                  <th className="w-20">Status</th>
                </tr>
              </thead>
              <tbody>
                {comparisons.map((comp, idx) => (
                  <tr key={idx} className={
                    comp.status === 'match' ? 'bg-green-50' :
                    comp.status === 'mismatch' ? 'bg-red-50' : ''
                  }>
                    <td className="font-medium text-gray-700">{comp.attribute}</td>
                    <td className="font-mono">{comp.value1 || <span className="text-gray-400 italic">-</span>}</td>
                    <td className="font-mono">{comp.value2 || <span className="text-gray-400 italic">-</span>}</td>
                    <td>
                      {comp.status === 'match' && <span className="badge badge-success">Match</span>}
                      {comp.status === 'mismatch' && <span className="badge badge-danger">Mismatch</span>}
                      {comp.status === 'missing' && <span className="badge text-gray-600 bg-gray-100">Missing</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}
