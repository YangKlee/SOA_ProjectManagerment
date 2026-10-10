import { useAuth } from './auth-context'

export function SessionRestoreScreen() {
  const { status, restoreError, retryRestore, logout } = useAuth()
  return <main className="session-screen" aria-label="Khôi phục phiên đăng nhập">
    <section><h1>Khôi phục phiên đăng nhập</h1>
      {status === 'restoring' ? <p role="status">Đang xác thực phiên đăng nhập…</p> : <>
        <p role="alert">{restoreError}</p>
        <div><button type="button" onClick={() => void retryRestore()}>Thử lại</button><button type="button" onClick={logout}>Về đăng nhập</button></div>
      </>}
    </section>
  </main>
}
