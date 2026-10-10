import { useCallback, useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { setAccessToken } from '../../services/api-client'
import { ApiError, normalizeApiError } from '../../services/api-error'
import { currentUserRequest, loginRequest } from './auth-api'
import { AuthContext } from './auth-context'
import { clearSessionToken, readSessionToken, saveSessionToken } from './session-storage'
import type { AuthUser, LoginCredentials } from './auth-types'
import type { SessionStatus } from './auth-context'
import './session.css'

const storageWarning = 'Trình duyệt không cho phép lưu phiên. Bạn có thể cần đăng nhập lại khi tải lại trang.'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [initial] = useState(readSessionToken)
  const [user, setUser] = useState<AuthUser | null>(null)
  const [status, setStatus] = useState<SessionStatus>(initial.token ? 'restoring' : 'ready')
  const [restoreError, setRestoreError] = useState('')
  const [warning, setWarning] = useState(initial.unavailable ? storageWarning : '')
  const attempt = useRef(0)
  const restoration = useRef<AbortController | null>(null)
  const restoring = useRef(false)

  const logout = useCallback(() => {
    attempt.current += 1
    restoration.current?.abort(); restoring.current = false
    setAccessToken(null); setUser(null); setStatus('ready'); setRestoreError('')
    setWarning(clearSessionToken() ? '' : 'Không thể xóa phiên đã lưu. Hãy đóng tab sau khi đăng xuất.')
  }, [])

  const retryRestore = useCallback(async () => {
    if (restoring.current) return
    const currentAttempt = ++attempt.current
    const saved = readSessionToken()
    setWarning(saved.unavailable ? storageWarning : '')
    setAccessToken(null); setUser(null); setRestoreError('')
    if (!saved.token) { setStatus('ready'); return }
    restoring.current = true
    const controller = new AbortController()
    restoration.current = controller
    setStatus('restoring'); setAccessToken(saved.token)
    try {
      const profile = await currentUserRequest(controller.signal)
      if (controller.signal.aborted || currentAttempt !== attempt.current) return
      setUser(profile); setStatus('ready')
    } catch (cause) {
      if (controller.signal.aborted || currentAttempt !== attempt.current) return
      const failure = normalizeApiError(cause)
      if (failure.status === 401 || failure.status === 403 || failure.kind === 'unknown') { logout(); return }
      setAccessToken(null); setRestoreError(failure.message); setStatus('error')
    } finally {
      if (currentAttempt === attempt.current) restoring.current = false
    }
  }, [logout])

  useEffect(() => {
    let disposed = false
    if (initial.token) void Promise.resolve().then(() => { if (!disposed) return retryRestore() })
    return () => {
      disposed = true; attempt.current += 1
      restoration.current?.abort(); restoring.current = false
      // Leave tab storage intact for F5; logout explicitly clears persistence.
      setAccessToken(null)
    }
  }, [initial.token, retryRestore])

  const login = useCallback(async (credentials: LoginCredentials, signal?: AbortSignal) => {
    const currentAttempt = ++attempt.current
    restoration.current?.abort(); restoring.current = false
    clearSessionToken(); setAccessToken(null); setUser(null); setRestoreError(''); setStatus('ready')
    const session = await loginRequest(credentials, signal)
    if (signal?.aborted || currentAttempt !== attempt.current) throw new ApiError('Yêu cầu đã được hủy.', 'cancelled')
    setWarning(saveSessionToken(session.access) ? '' : storageWarning)
    setAccessToken(session.access); setUser(session.user)
  }, [])

  return <AuthContext.Provider value={{ user, login, logout, status, restoreError, retryRestore }}>
    {warning && <p className="session-warning" role="status">{warning}</p>}
    {children}
  </AuthContext.Provider>
}
