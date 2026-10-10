import { useAuth } from '../features/auth/auth-context'
import { ROLE_LABEL } from '../features/auth/auth-types'

export function RoleHomePage() {
  const { user, logout } = useAuth()
  if (!user) return null
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.user_id

  return (
    <div className="shell">
      <header className="header">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">ĐA</span>
          <span>Quản lý đồ án<span className="brand-caption">TỐT NGHIỆP</span></span>
        </div>
        <button className="logout-button" type="button" onClick={logout}>Đăng xuất</button>
      </header>
      <main className="role-home">
        <p className="eyebrow">KHÔNG GIAN LÀM VIỆC</p>
        <h1>{ROLE_LABEL[user.role]}</h1>
        <p>Xin chào, <strong>{name}</strong>.</p>
        <p className="account-id">MSSV/UserID: {user.user_id}</p>
        <aside className="notice" aria-label="Trạng thái phân hệ">
          <span className="notice-dot" aria-hidden="true" />
          <p>Bạn đã đăng nhập thành công. Các chức năng của phân hệ đang được phát triển.</p>
        </aside>
      </main>
      <footer>Hệ thống quản lý đồ án tốt nghiệp</footer>
    </div>
  )
}
