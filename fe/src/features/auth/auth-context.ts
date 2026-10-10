import { createContext, useContext } from 'react'
import type { AuthUser, LoginCredentials } from './auth-types'

interface AuthContextValue {
  user: AuthUser | null
  login: (credentials: LoginCredentials, signal?: AbortSignal) => Promise<void>
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
