import { XMarkIcon } from '@heroicons/react/24/outline'
import type { Relationship } from '../types'

interface RelationshipDetailsModalProps {
  relationship: Relationship
  onClose: () => void
}

export default function RelationshipDetailsModal({ relationship, onClose }: RelationshipDetailsModalProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-gray-900">Relationship Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Relationship ID</h3>
            <p className="font-mono text-sm text-gray-900">{relationship.relationship_id}</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Type</h3>
            <span className="badge bg-blue-100 text-blue-700">
              {relationship.metadata.relationship_type}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">From Party</h3>
              <p className="font-mono text-xs text-gray-900">{relationship.from_party_id}</p>
              {relationship.from_matching_value && (
                <p className="text-xs text-gray-600 mt-1">
                  Value: <span className="font-medium">{relationship.from_matching_value}</span>
                </p>
              )}
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">To Party</h3>
              <p className="font-mono text-xs text-gray-900">{relationship.to_party_id}</p>
              {relationship.to_matching_value && (
                <p className="text-xs text-gray-600 mt-1">
                  Value: <span className="font-medium">{relationship.to_matching_value}</span>
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Bidirectional</h3>
              <span className={`badge ${relationship.metadata.is_bidirectional ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                {relationship.metadata.is_bidirectional ? 'Yes' : 'No'}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Same Party</h3>
              <span className={`badge ${relationship.metadata.guarantees_same_party ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>
                {relationship.metadata.guarantees_same_party ? 'Yes' : 'No'}
              </span>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Confidence</h3>
              <span className="badge bg-purple-100 text-purple-700">
                {relationship.metadata.confidence_score !== null ? `${(relationship.metadata.confidence_score * 100).toFixed(0)}%` : 'N/A'}
              </span>
            </div>
          </div>

          <div className="bg-blue-50 p-3 rounded">
            <h3 className="text-sm font-semibold text-blue-900 mb-1">Metadata ID</h3>
            <p className="font-mono text-xs text-blue-700">{relationship.metadata_relationship_id}</p>
          </div>
        </div>

        <div className="flex justify-end gap-2 p-4 border-t border-gray-200">
          <button onClick={onClose} className="btn-secondary">
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
