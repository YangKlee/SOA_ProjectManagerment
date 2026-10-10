import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './auth-context'
import { ROLE_HOME } from './auth-types'
import type { Role } from './auth-types'

export function SessionRedirect() {
  const { user } = useAuth()
  return <Navigate to={user ? ROLE_HOME[user.role] : '/login'} replace />
}

export function GuestRoute() {
  const { user } = useAuth()
  return user ? <Navigate to={ROLE_HOME[user.role]} replace /> : <Outlet />
}

export function RoleRoute({ role }: { role: Role }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role]} replace />
  return <Outlet />
}
