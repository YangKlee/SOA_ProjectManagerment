import { useEffect, useRef, useState } from 'react'
import { ROLE_LABEL } from '../../features/auth/auth-types'
import type { AuthUser } from '../../features/auth/auth-types'
import { DASHBOARD_MENU, HOME_ITEM, PROFILE_ITEM, QNU_BRANDING, dashboardItem, dashboardPath } from './dashboard-menu'
import type { MenuItem } from './dashboard-menu'
import { NavLink, Link, Outlet, useLocation } from 'react-router-dom'
import { DashboardIcon as Icon } from './DashboardIcon'
import './dashboard.css'

export function MainLayout({ user, logout }: { user: AuthUser; logout: () => void }) {
  const [mobile, setMobile] = useState(() => window.matchMedia?.('(max-width: 800px)').matches ?? false)
  const [sidebarOpen, setSidebarOpen] = useState(!mobile)
  const [collapsedGroups, setCollapsedGroups] = useState<string[]>([])
  const location = useLocation()
  const selected = dashboardItem(user.role, location.pathname)
  const [panel, setPanel] = useState<'notifications' | 'account' | null>(null)
  const sidebar = useRef<HTMLElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const headerActions = useRef<HTMLDivElement>(null)
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.user_id
  const groups = DASHBOARD_MENU[user.role]

  useEffect(() => {
    const media = window.matchMedia?.('(max-width: 800px)')
    if (!media) return
    const update = () => { setMobile(media.matches); setSidebarOpen(!media.matches) }
    media.addEventListener('change', update)
    return () => media.removeEventListener('change', update)
  }, [])
  useEffect(() => {
    if (!mobile || !sidebarOpen) return
    sidebar.current?.querySelector<HTMLButtonElement>('button')?.focus()
    const previous = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => { document.body.style.overflow = previous }
  }, [mobile, sidebarOpen])
  useEffect(() => {
    if (!panel) return
    function dismiss(event: PointerEvent) {
      if (!headerActions.current?.contains(event.target as Node)) setPanel(null)
    }
    document.addEventListener('pointerdown', dismiss)
    return () => document.removeEventListener('pointerdown', dismiss)
  }, [panel])

  function closeDrawer() { setSidebarOpen(false); toggle.current?.focus() }
  function onNavigate() {
    setPanel(null)
    if (mobile) closeDrawer()
  }
  function menuLink(item: MenuItem) {
    return <NavLink key={item.id} to={dashboardPath(user.role, item)} end className={`dash-menu-item ${selected.id === item.id ? 'is-active' : ''}`} aria-current={selected.id === item.id ? 'page' : undefined} onClick={onNavigate}><Icon name={item.icon} /><span>{item.label}</span>{selected.id === item.id && <span className="dash-active-dot" />}</NavLink>
  }

  return (
    <div className={`dashboard ${sidebarOpen ? 'sidebar-open' : ''}`} onKeyDown={(event) => {
      if (event.key === 'Escape') {
        if (panel) { setPanel(null); headerActions.current?.querySelector<HTMLButtonElement>(`[aria-controls="dash-${panel}"]`)?.focus() }
        else if (mobile && sidebarOpen) closeDrawer()
      }
    }}>
      <a className="dash-skip" href="#dashboard-content" inert={mobile && sidebarOpen}>Đến nội dung chính</a>
      <header className="dash-header" inert={mobile && sidebarOpen}>
        <button ref={toggle} className="dash-icon-button" type="button" aria-label={sidebarOpen ? 'Đóng menu' : 'Mở menu'} aria-expanded={sidebarOpen} aria-controls="dashboard-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}><Icon name="menu" /></button>
        <span className="dash-school">TRƯỜNG ĐẠI HỌC QUY NHƠN</span>
        <div ref={headerActions} className="dash-header-actions">
          <button className="dash-icon-button" type="button" aria-label="Thông báo" aria-expanded={panel === 'notifications'} aria-controls="dash-notifications" onClick={() => setPanel(panel === 'notifications' ? null : 'notifications')}><Icon name="bell" /></button>
          <button className="dash-icon-button dash-account" type="button" aria-label="Tài khoản" aria-expanded={panel === 'account'} aria-controls="dash-account" onClick={() => setPanel(panel === 'account' ? null : 'account')}><Icon name="user" /></button>
          <section id="dash-notifications" className="dash-popover" aria-label="Thông báo" hidden={panel !== 'notifications'}><h2>Thông báo</h2><p>Thông báo sẽ hiển thị khi chức năng được triển khai.</p></section>
          <section id="dash-account" className="dash-popover" aria-label="Tài khoản" hidden={panel !== 'account'}><h2>{name}</h2><p>{ROLE_LABEL[user.role]} · {user.user_id}</p><Link to={dashboardPath(user.role, PROFILE_ITEM)} onClick={onNavigate}>Xem thông tin cá nhân <Icon name="arrow" /></Link></section>
        </div>
      </header>
      {mobile && sidebarOpen && <button className="dash-backdrop" type="button" aria-label="Đóng menu điều hướng" onClick={closeDrawer} tabIndex={-1} />}
      <aside ref={sidebar} id="dashboard-sidebar" className="dash-sidebar" hidden={!sidebarOpen} role={mobile ? 'dialog' : undefined} aria-modal={mobile ? true : undefined} aria-label="Menu điều hướng" onKeyDown={(event) => {
        if (!mobile || event.key !== 'Tab') return
        const controls = Array.from(sidebar.current?.querySelectorAll<HTMLElement>('button, a[href]') ?? []).filter((button) => !button.closest('[hidden]'))
        const first = controls[0], last = controls.at(-1)
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
      }}>
        {mobile && <button className="dash-drawer-close" type="button" aria-label="Đóng menu" onClick={closeDrawer}><Icon name="close" /></button>}
        <div className="dash-university"><img className="dash-qnu-logo" src={QNU_BRANDING.logo} alt="Logo Trường Đại học Quy Nhơn" width="80" height="80" /><span>CỔNG THÔNG TIN ĐỒ ÁN</span></div>
        <div className="dash-profile"><span className="dash-avatar"><Icon name="user" /></span><strong>{name}</strong><span>{ROLE_LABEL[user.role]} · {user.user_id}</span></div>
        <nav aria-label="Chức năng">{menuLink(HOME_ITEM)}{groups.map((group) => <div className="dash-menu-group" key={group.id}>
          {group.label !== null && <button className="dash-group-toggle" type="button" aria-expanded={!collapsedGroups.includes(group.id)} aria-controls={`menu-${group.id}`} onClick={() => setCollapsedGroups((current) => current.includes(group.id) ? current.filter((id) => id !== group.id) : [...current, group.id])}>{group.label}<Icon name="chevron" /></button>}
          <div id={`menu-${group.id}`} hidden={group.label !== null && collapsedGroups.includes(group.id)}>{group.items.map(menuLink)}</div>
        </div>)}</nav>
        <div className="dash-sidebar-bottom"><button type="button" className="dash-menu-item" onClick={logout}><Icon name="logout" /><span>Đăng xuất</span></button><small>Hệ thống quản lý đồ án tốt nghiệp</small></div>
      </aside>
      <div className="dash-workspace" inert={mobile && sidebarOpen}>
        <main id="dashboard-content" className="dash-main" tabIndex={-1}>
          <div className="dash-breadcrumb">Cổng thông tin <span>/</span> {ROLE_LABEL[user.role]} <span>/</span> <strong>{selected.label}</strong></div>
          <div className="dash-page-heading"><div><p className="dash-overline">KHÔNG GIAN LÀM VIỆC</p><h1>{selected.id === 'home' ? ROLE_LABEL[user.role] : selected.label}</h1></div><span className="dash-role-badge"><span />{ROLE_LABEL[user.role]}</span></div>
          <Outlet context={{ user, selected, onNavigate }} />
        </main>
        <footer className="dash-footer"><span>TRƯỜNG ĐẠI HỌC QUY NHƠN</span><span>Hệ thống quản lý đồ án tốt nghiệp</span></footer>
      </div>
    </div>
  )
}
