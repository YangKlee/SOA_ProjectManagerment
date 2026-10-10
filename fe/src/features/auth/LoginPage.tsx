import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../services/api-error'
import { useAuth } from './auth-context'
import { QNU_BRANDING } from '../../components/layout/dashboard-menu'
import './login.css'

function loginErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'MSSV/UserID hoặc mật khẩu không đúng.'
    if (error.status === 400 || error.status === 422) return 'Thông tin đăng nhập không hợp lệ. Vui lòng kiểm tra lại.'
    return error.message
  }
  return 'Không thể đăng nhập. Vui lòng thử lại sau.'
}

export function LoginPage() {
  const { login } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [errors, setErrors] = useState<{ identifier?: string; password?: string }>({})
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const pending = useRef(false)
  const request = useRef<AbortController | null>(null)
  const identifierInput = useRef<HTMLInputElement>(null)
  const passwordInput = useRef<HTMLInputElement>(null)

  useEffect(() => () => request.current?.abort(), [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (pending.current) return

    const nextErrors = {
      identifier: identifier.trim() ? undefined : 'Vui lòng nhập MSSV/UserID.',
      password: password.length ? undefined : 'Vui lòng nhập mật khẩu.',
    }
    setErrors(nextErrors)
    setErrorMessage('')
    if (nextErrors.identifier || nextErrors.password) {
      if (nextErrors.identifier) identifierInput.current?.focus()
      else passwordInput.current?.focus()
      return
    }

    pending.current = true
    setIsSubmitting(true)
    const controller = new AbortController()
    request.current = controller

    try {
      await login({ identifier, password }, controller.signal)
    } catch (error: unknown) {
      if (!controller.signal.aborted) setErrorMessage(loginErrorMessage(error))
    } finally {
      pending.current = false
      if (!controller.signal.aborted) setIsSubmitting(false)
    }
  }

  return (
    <main className="login-layout">
      <div className="login-banner">
        <img src={QNU_BRANDING.banner} alt="Khuôn viên Trường Đại học Quy Nhơn" />
      </div>

      <section className="login-panel" aria-labelledby="login-title">
        <header className="login-university">
          <img src={QNU_BRANDING.logo} alt="Logo Trường Đại học Quy Nhơn" width="100" height="100" />
          <p>TRƯỜNG ĐẠI HỌC QUY NHƠN</p>
          <h1>CỔNG THÔNG TIN ĐÀO TẠO</h1>
        </header>
        <div className="login-form-container">
          <h2 id="login-title">Đăng nhập</h2>
          <p className="login-description">Quản lý đồ án tốt nghiệp</p>

          <form onSubmit={handleSubmit} noValidate aria-label="Đăng nhập" aria-busy={isSubmitting}>
            <div className="form-field">
              <label className="login-sr-only" htmlFor="identifier">MSSV/UserID</label>
              <input
                ref={identifierInput}
                id="identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="Tên đăng nhập"
                value={identifier}
                onChange={(event) => { setIdentifier(event.target.value); setErrors((current) => ({ ...current, identifier: undefined })); setErrorMessage('') }}
                disabled={isSubmitting}
                required
                aria-invalid={Boolean(errors.identifier)}
                aria-describedby={errors.identifier ? 'identifier-error' : undefined}
              />
              {errors.identifier && <p className="field-error" id="identifier-error">{errors.identifier}</p>}
            </div>

            <div className="form-field">
              <label className="login-sr-only" htmlFor="password">Mật khẩu</label>
              <div className="password-control">
                <input
                  ref={passwordInput}
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Mật khẩu"
                  value={password}
                  onChange={(event) => { setPassword(event.target.value); setErrors((current) => ({ ...current, password: undefined })); setErrorMessage('') }}
                  disabled={isSubmitting}
                  required
                  aria-invalid={Boolean(errors.password)}
                  aria-describedby={errors.password ? 'password-error' : undefined}
                />
                <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)} disabled={isSubmitting} aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={showPassword}>
                  {showPassword ? 'Ẩn' : 'Hiện'}
                </button>
              </div>
              {errors.password && <p className="field-error" id="password-error">{errors.password}</p>}
            </div>

            {errorMessage && <div className="login-error" role="alert">{errorMessage}</div>}

            <button className="login-submit" type="submit" disabled={isSubmitting}>
              {isSubmitting ? <><span className="loading-spinner" aria-hidden="true" />Đang đăng nhập…</> : 'Đăng nhập'}
            </button>
            <p className="submit-status" role="status">{isSubmitting ? 'Đang xác thực tài khoản, vui lòng chờ.' : ''}</p>
          </form>

          <div className="login-secondary">
            <button className="login-google" type="button" disabled aria-describedby="login-unavailable">
              <span className="google-mark" aria-hidden="true">G</span> Đăng nhập với Google
            </button>
            <button className="login-forgot" type="button" disabled aria-describedby="login-unavailable">Sinh viên quên mật khẩu</button>
            <p id="login-unavailable">Hai chức năng này chưa khả dụng. Cần hỗ trợ tài khoản, vui lòng liên hệ phòng đào tạo.</p>
          </div>
        </div>
        <p className="login-footer">© {new Date().getFullYear()} Trường Đại học Quy Nhơn | Hệ thống quản lý đồ án tốt nghiệp</p>
      </section>
    </main>
  )
}
