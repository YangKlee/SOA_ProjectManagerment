import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from './auth-context'
import { ROLE_HOME } from './auth-types'
import type { Role } from './auth-types'
import { SessionRestoreScreen } from './SessionRestoreScreen'
import { allowedReturnPath } from '../../components/layout/dashboard-menu'

export function SessionRedirect() {
  const { user, status } = useAuth()
  if (status !== 'ready') return <SessionRestoreScreen />
  return <Navigate to={user ? ROLE_HOME[user.role] : '/login'} replace />
}

export function GuestRoute() {
  const { user, status } = useAuth()
  const location = useLocation()
  if (status !== 'ready') return <SessionRestoreScreen />
  const from: unknown = location.state && typeof location.state === 'object' ? location.state.from : undefined
  return user ? <Navigate to={allowedReturnPath(from, user.role)} replace /> : <Outlet />
}

export function RoleRoute({ role }: { role: Role }) {
  const { user, status } = useAuth()
  const location = useLocation()
  if (status !== 'ready') return <SessionRestoreScreen />
  if (!user) return <Navigate to="/login" state={{ from: location.pathname + location.search + location.hash }} replace />
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />
  return <Outlet />
}
