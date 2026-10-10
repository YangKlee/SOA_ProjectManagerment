import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ApiError } from '../../services/api-error'
import { useAuth } from './auth-context'
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
      <section className="login-story" aria-labelledby="story-title">
        <a className="brand login-brand" href="/login" aria-label="Quản lý đồ án tốt nghiệp">
          <span className="brand-mark" aria-hidden="true">ĐA</span>
          <span>Quản lý đồ án<span className="brand-caption">TỐT NGHIỆP</span></span>
        </a>
        <div className="story-content">
          <p className="eyebrow">HỌC TẬP · NGHIÊN CỨU · PHÁT TRIỂN</p>
          <h1 id="story-title">Ý tưởng của bạn.<br /><span>Khởi đầu từ đây.</span></h1>
          <p>Kết nối với giảng viên, khám phá đề tài và theo dõi hành trình đồ án tốt nghiệp của bạn.</p>
          <div className="story-illustration" aria-hidden="true">
            <div className="illustration-orbit" />
            <div className="illustration-paper">
              <span className="paper-caption">ĐỒ ÁN TỐT NGHIỆP</span>
              <span className="paper-heading">Từ ý tưởng<br />đến thành quả.</span>
              <span className="paper-line" /><span className="paper-line short" />
              <span className="paper-seal">ĐA</span>
            </div>
            <span className="illustration-note">Mỗi hành trình đều bắt đầu<br />bằng một bước nhỏ.</span>
          </div>
        </div>
        <p className="story-footer">Không gian chung cho hành trình đồ án của bạn.</p>
      </section>

      <section className="login-panel" aria-labelledby="login-title">
        <div className="login-form-container">
          <p className="eyebrow">CHÀO MỪNG TRỞ LẠI</p>
          <h2 id="login-title">Đăng nhập</h2>
          <p className="login-description">Sử dụng tài khoản được nhà trường cung cấp để tiếp tục.</p>

          <form onSubmit={handleSubmit} noValidate aria-label="Đăng nhập" aria-busy={isSubmitting}>
            <div className="form-field">
              <label htmlFor="identifier">MSSV/UserID</label>
              <input
                ref={identifierInput}
                id="identifier"
                name="identifier"
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                placeholder="Nhập MSSV hoặc UserID"
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
              <label htmlFor="password">Mật khẩu</label>
              <div className="password-control">
                <input
                  ref={passwordInput}
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  placeholder="Nhập mật khẩu"
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
              {isSubmitting ? <><span className="loading-spinner" aria-hidden="true" />Đang đăng nhập…</> : <>Đăng nhập <span aria-hidden="true">→</span></>}
            </button>
            <p className="submit-status" role="status">{isSubmitting ? 'Đang xác thực tài khoản, vui lòng chờ.' : ''}</p>
          </form>

          <p className="login-help">Cần hỗ trợ tài khoản? <span>Vui lòng liên hệ phòng đào tạo.</span></p>
        </div>
        <p className="login-footer">Hệ thống quản lý đồ án tốt nghiệp</p>
      </section>
    </main>
  )
}
