import { useState, useEffect } from 'react'
import { configApi, type ConfigInfo } from '../api/client'
import { CogIcon, ArrowTrendingUpIcon, ShieldCheckIcon, ChartBarIcon } from '@heroicons/react/24/outline'

export default function ConfigSelector() {
  const [configInfo, setConfigInfo] = useState<ConfigInfo | null>(null)
  const [isChanging, setIsChanging] = useState(false)
  const [showDropdown, setShowDropdown] = useState(false)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const info = await configApi.getConfig()
      setConfigInfo(info)
    } catch (error) {
      console.error('Failed to load config:', error)
    }
  }

  const handleConfigChange = async (newConfig: string) => {
    if (newConfig === configInfo?.current_config) {
      setShowDropdown(false)
      return
    }

    setIsChanging(true)
    try {
      const result = await configApi.setConfig(newConfig)
      if (result.success) {
        setConfigInfo({
          current_config: result.current_config,
          available_configs: configInfo?.available_configs || []
        })
        // Reload the page to refresh all data with new config
        window.location.reload()
      }
    } catch (error) {
      console.error('Failed to change config:', error)
      alert('Failed to change configuration. Please try again.')
    } finally {
      setIsChanging(false)
      setShowDropdown(false)
    }
  }

  const getConfigIcon = (config: string) => {
    switch (config) {
      case 'operational':
        return <ShieldCheckIcon className="w-4 h-4" />
      case 'analytics':
        return <ArrowTrendingUpIcon className="w-4 h-4" />
      default:
        return <ChartBarIcon className="w-4 h-4" />
    }
  }

  const getConfigLabel = (config: string) => {
    switch (config) {
      case 'operational':
        return 'Operational'
      case 'analytics':
        return 'Analytics'
      default:
        return 'Default'
    }
  }

  const getConfigDescription = (config: string) => {
    switch (config) {
      case 'operational':
        return 'Strict thresholds - Zero errors (payment, contracts)'
      case 'analytics':
        return 'Lenient thresholds - Customer counting & insights'
      default:
        return 'Balanced approach'
    }
  }

  const getConfigBadgeColor = (config: string) => {
    switch (config) {
      case 'operational':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'analytics':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  if (!configInfo) {
    return null
  }

  return (
    <div className="relative">
      <button
        onClick={() => setShowDropdown(!showDropdown)}
        disabled={isChanging}
        className={`
          flex items-center gap-2 px-4 py-2 rounded-lg border transition-all
          ${getConfigBadgeColor(configInfo.current_config)}
          hover:shadow-md disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {getConfigIcon(configInfo.current_config)}
        <span className="font-medium">{getConfigLabel(configInfo.current_config)}</span>
        <CogIcon className={`w-4 h-4 transition-transform ${showDropdown ? 'rotate-90' : ''}`} />
      </button>

      {showDropdown && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setShowDropdown(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-20">
            <div className="p-3 border-b border-gray-200">
              <h3 className="font-semibold text-gray-900">Entity Resolution Mode</h3>
              <p className="text-xs text-gray-500 mt-1">
                Switch between operational and analytics views
              </p>
            </div>

            <div className="p-2">
              {configInfo.available_configs.map((config) => (
                <button
                  key={config}
                  onClick={() => handleConfigChange(config)}
                  disabled={isChanging}
                  className={`
                    w-full text-left p-3 rounded-lg mb-1 transition-all
                    ${config === configInfo.current_config
                      ? 'bg-blue-50 border-2 border-blue-200'
                      : 'hover:bg-gray-50 border-2 border-transparent'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5">
                      {getConfigIcon(config)}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">
                          {getConfigLabel(config)}
                        </span>
                        {config === configInfo.current_config && (
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                            Active
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 mt-1">
                        {getConfigDescription(config)}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="p-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-600">
              <p className="flex items-center gap-1">
                <span className="font-medium">Note:</span>
                Changing mode will reload all entity data
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
