import { ReactNode } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { CubeIcon, ChartBarIcon, BuildingOfficeIcon } from '@heroicons/react/24/outline'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()
  
  const NavLink = ({ to, icon: Icon, children }: { to: string; icon: any; children: ReactNode }) => {
    const isActive = location.pathname === to || (to !== '/' && location.pathname.startsWith(to))
    return (
      <Link 
        to={to} 
        className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive 
            ? 'bg-primary-100 text-primary-700' 
            : 'text-gray-700 hover:text-primary-600 hover:bg-gray-100'
        }`}
      >
        <Icon className="h-5 w-5" />
        <span>{children}</span>
      </Link>
    )
  }
  
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center space-x-2">
              <CubeIcon className="h-8 w-8 text-primary-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-900">Entity Resolution</h1>
                <p className="text-xs text-gray-500">Data Steward Portal</p>
              </div>
            </Link>
            
            <nav className="flex items-center space-x-2">
              <NavLink to="/" icon={ChartBarIcon}>
                Dashboard
              </NavLink>
              <NavLink to="/entities" icon={BuildingOfficeIcon}>
                Entities
              </NavLink>
            </nav>
          </div>
        </div>
      </header>

      <main className="flex-1 bg-gray-50">
        {children}
      </main>

      <footer className="bg-white border-t border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <p className="text-sm text-gray-500 text-center">
            Entity Resolution System - Data Quality & Master Data Management
          </p>
        </div>
      </footer>
    </div>
  )
}
