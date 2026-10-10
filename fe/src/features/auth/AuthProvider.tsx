import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { setAccessToken } from '../../services/api-client'
import { ApiError } from '../../services/api-error'
import { loginRequest } from './auth-api'
import { AuthContext } from './auth-context'
import type { AuthUser, LoginCredentials } from './auth-types'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const attempt = useRef(0)

  useEffect(() => () => {
    attempt.current += 1
    setAccessToken(null)
  }, [])

  async function login(credentials: LoginCredentials, signal?: AbortSignal) {
    const currentAttempt = ++attempt.current
    setAccessToken(null)
    setUser(null)
    const session = await loginRequest(credentials, signal)

    // A cancelled request or logout must not establish a late session.
    if (signal?.aborted || currentAttempt !== attempt.current) {
      throw new ApiError('Yêu cầu đã được hủy.', 'cancelled')
    }
    setAccessToken(session.access)
    setUser(session.user)
  }

  function logout() {
    attempt.current += 1
    setAccessToken(null)
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, login, logout }}>{children}</AuthContext.Provider>
}
