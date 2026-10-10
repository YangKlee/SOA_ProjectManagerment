import { useOutletContext } from 'react-router-dom'
import type { AuthUser } from '../../features/auth/auth-types'
import type { MenuItem } from './dashboard-menu'

interface DashboardContext {
  user: AuthUser
  selected: MenuItem
  onNavigate: () => void
}

export const useDashboardLayout = () => useOutletContext<DashboardContext>()
