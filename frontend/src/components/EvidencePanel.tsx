import { CheckCircleIcon, DocumentTextIcon } from '@heroicons/react/24/outline'
import { Link } from 'react-router-dom'
import type { MatchEvidence } from '../types'

interface EvidencePanelProps {
  evidence: MatchEvidence[]
}

export default function EvidencePanel({ evidence }: EvidencePanelProps) {
  const getRuleLabel = (ruleId: string) => {
    const labels: Record<string, string> = {
      'RULE_EXACT_HKID': 'Exact HKID Match',
      'RULE_EXACT_PASSPORT': 'Exact Passport Match',
      'RULE_EXACT_EMAIL': 'Exact Email Match',
      'RULE_EXACT_PHONE': 'Exact Phone Match',
      'RULE_EXACT_NAME_DOB': 'Exact Name + DOB Match',
      'RULE_EXACT_NAME_EMAIL': 'Exact Name + Email Match',
    }
    return labels[ruleId] || ruleId
  }

  const getConfidenceColor = (score: number) => {
    if (score >= 0.95) return 'text-green-700 bg-green-100'
    if (score >= 0.85) return 'text-blue-700 bg-blue-100'
    if (score >= 0.75) return 'text-yellow-700 bg-yellow-100'
    return 'text-orange-700 bg-orange-100'
  }

  if (evidence.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <DocumentTextIcon className="h-12 w-12 text-gray-300 mx-auto mb-2" />
          <p className="text-xs text-gray-500">No match evidence</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full overflow-y-auto p-2">
      <div className="mb-2">
        <h2 className="text-sm font-bold text-gray-900 mb-1">Match Evidence ({evidence.length})</h2>
        <p className="text-xs text-gray-600">
          Evidence showing why parties were matched
        </p>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Rule</th>
            <th>Party 1</th>
            <th>Party 2</th>
            <th>Match Key</th>
            <th>Evidence Value</th>
            <th className="w-16 text-center">Conf</th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((ev) => (
            <tr key={ev.evidence_id}>
              <td>
                <div className="flex items-center gap-1">
                  <CheckCircleIcon className="h-3 w-3 text-green-600 flex-shrink-0" />
                  <span className="font-medium">{getRuleLabel(ev.match_rule_id)}</span>
                </div>
              </td>
              <td>
                <Link
                  to={`/parties/${ev.party_id_1}`}
                  className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {ev.party_id_1}
                </Link>
              </td>
              <td>
                <Link
                  to={`/parties/${ev.party_id_2}`}
                  className="font-mono text-sm text-blue-600 hover:text-blue-800 hover:underline"
                >
                  {ev.party_id_2}
                </Link>
              </td>
              <td className="font-medium">{ev.match_key}</td>
              <td className="font-mono text-gray-900">{ev.evidence_value}</td>
              <td className="text-center">
                <span className={`badge ${getConfidenceColor(ev.confidence_score)}`}>
                  {(ev.confidence_score * 100).toFixed(0)}%
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
