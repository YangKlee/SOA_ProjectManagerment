import { MainLayout } from '../components/layout/MainLayout'
import { useAuth } from '../features/auth/auth-context'

export function RoleHomePage() {
  const { user, logout } = useAuth()
  return user ? <MainLayout key={`${user.role}:${user.user_id}`} user={user} logout={logout} /> : null
}
