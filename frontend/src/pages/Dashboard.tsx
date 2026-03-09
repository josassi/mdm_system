import { useQuery } from '@tanstack/react-query'
import { 
  UserGroupIcon, 
  BuildingOfficeIcon,
  IdentificationIcon,
  ChartBarIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClipboardDocumentListIcon,
  LinkIcon
} from '@heroicons/react/24/outline'
import { dashboardApi } from '../api/client'

export default function Dashboard() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: dashboardApi.getStats,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-gray-500">Loading dashboard...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-red-500">Error loading dashboard statistics</div>
      </div>
    )
  }

  const totals = stats?.totals || {}
  const matchScoreDistribution = stats?.match_score_distribution || {}
  const entitySizeDistribution = stats?.entity_size_distribution || {}
  const conflicts = stats?.conflicts || {}
  const qualityMetrics = stats?.quality_metrics || {}
  const partiesBySystem = stats?.parties_by_system || {}

  const StatCard = ({ icon: Icon, title, value, subtitle, color = 'primary' }: any) => (
    <div className="card">
      <div className="flex items-center">
        <div className={`flex-shrink-0 p-3 rounded-lg bg-${color}-100`}>
          <Icon className={`h-8 w-8 text-${color}-600`} />
        </div>
        <div className="ml-4 flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value?.toLocaleString() || 0}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
      </div>
    </div>
  )

  const DistributionCard = ({ title, data, colors }: any) => {
    const colorMap: Record<string, string> = {
      'green': '#10b981',
      'blue': '#3b82f6',
      'yellow': '#f59e0b',
      'orange': '#f97316',
      'red': '#ef4444',
      'purple': '#a855f7',
      'indigo': '#6366f1',
      'gray': '#6b7280',
    }
    
    return (
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">{title}</h3>
        <div className="space-y-3">
          {Object.entries(data).map(([key, value]: [string, any]) => {
            const percentage = totals.total_entities > 0 
              ? ((value / totals.total_entities) * 100).toFixed(1) 
              : 0
            const color = colors[key] || 'gray'
            const bgColor = colorMap[color] || colorMap['gray']
            const label = key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())
            
            return (
              <div key={key}>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm font-medium text-gray-700">{label}</span>
                  <span className="text-sm text-gray-500">{value} ({percentage}%)</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="h-2 rounded-full transition-all duration-300"
                    style={{ width: `${percentage}%`, backgroundColor: bgColor }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">Overview of entity resolution metrics and data quality</p>
        </div>

      {/* Key Metrics */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Key Metrics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            icon={UserGroupIcon}
            title="Total Parties"
            value={totals.total_parties}
            subtitle="Across all source systems"
            color="blue"
          />
          <StatCard
            icon={BuildingOfficeIcon}
            title="Master Entities"
            value={totals.total_entities}
            subtitle="Resolved entities"
            color="green"
          />
          <StatCard
            icon={IdentificationIcon}
            title="Distinct HKIDs"
            value={totals.distinct_hkids}
            subtitle="Unique government IDs"
            color="purple"
          />
          <StatCard
            icon={ChartBarIcon}
            title="Source Systems"
            value={totals.total_systems}
            subtitle="Connected data sources"
            color="indigo"
          />
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          icon={LinkIcon}
          title="Relationships"
          value={totals.total_relationships}
          subtitle="Active business relationships"
          color="cyan"
        />
        <StatCard
          icon={ClipboardDocumentListIcon}
          title="Attributes"
          value={totals.total_attributes}
          subtitle={`${totals.unique_attribute_types} unique types`}
          color="teal"
        />
        <StatCard
          icon={CheckCircleIcon}
          title="Match Evidence"
          value={qualityMetrics.total_match_evidence}
          subtitle={`Avg ${qualityMetrics.avg_match_evidence_per_entity?.toFixed(1)} per entity`}
          color="green"
        />
      </div>

      {/* Distributions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DistributionCard
          title="Entities by Match Score"
          data={matchScoreDistribution}
          colors={{
            perfect_match: 'green',
            high_match: 'emerald',
            medium_match: 'yellow',
            low_match: 'orange',
            no_match: 'gray'
          }}
        />
        <DistributionCard
          title="Entities by Party Count"
          data={entitySizeDistribution}
          colors={{
            single_party: 'gray',
            two_parties: 'blue',
            three_parties: 'indigo',
            four_plus_parties: 'purple'
          }}
        />
      </div>

      {/* Quality Metrics */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Data Quality Metrics</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div>
            <p className="text-sm font-medium text-gray-500">Avg Match Score</p>
            <p className="text-3xl font-bold text-green-600">
              {(qualityMetrics.avg_entity_match_score * 100)?.toFixed(1)}%
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Avg Unique Attributes</p>
            <p className="text-3xl font-bold text-blue-600">
              {qualityMetrics.avg_unique_attrs_per_entity?.toFixed(1)}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Avg Contradictions</p>
            <p className="text-3xl font-bold text-orange-600">
              {qualityMetrics.avg_contradicting_attrs?.toFixed(2)}
            </p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Match Evidence/Entity</p>
            <p className="text-3xl font-bold text-purple-600">
              {qualityMetrics.avg_match_evidence_per_entity?.toFixed(1)}
            </p>
          </div>
        </div>
      </div>

      {/* Conflicts */}
      <div className="card bg-red-50 border-red-200">
        <div className="flex items-start">
          <ExclamationTriangleIcon className="h-6 w-6 text-red-600 mt-1" />
          <div className="ml-3 flex-1">
            <h3 className="text-lg font-semibold text-red-900 mb-4">Conflicts & Issues</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <p className="text-sm font-medium text-red-700">Blocking Pairs</p>
                <p className="text-2xl font-bold text-red-900">{conflicts.total_blocking_pairs}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-red-700">Entities with Conflicts</p>
                <p className="text-2xl font-bold text-red-900">{conflicts.entities_with_conflicts}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-red-700">Entities with Contradictions</p>
                <p className="text-2xl font-bold text-red-900">{conflicts.entities_with_contradictions}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Parties by System */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Parties by Source System</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(partiesBySystem).map(([systemId, count]: [string, any]) => (
            <div key={systemId} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-medium text-gray-700">{systemId}</span>
              <span className="text-xl font-bold text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </div>
      </div>
    </div>
  )
}
