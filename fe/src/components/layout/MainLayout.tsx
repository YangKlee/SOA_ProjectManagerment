import { useEffect, useRef, useState } from 'react'
import { ROLE_LABEL } from '../../features/auth/auth-types'
import type { AuthUser } from '../../features/auth/auth-types'
import { DASHBOARD_MENU, HOME_ITEM, PROFILE_ITEM } from './dashboard-menu'
import type { IconName, MenuItem } from './dashboard-menu'
import './dashboard.css'
import { DepartmentPage } from '../../features/academic/pages/DepartmentPage'
import { MajorPage } from '../../features/academic/pages/MajorPage'
import { StudentPage } from '../../features/academic/pages/StudentPage'
import { LecturerPage } from '../../features/academic/pages/LecturerPage'

const academicPages = { faculties: DepartmentPage, majors: MajorPage, students: StudentPage, lecturers: LecturerPage }

const paths: Record<IconName, string> = {
  home: 'm3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9',
  user: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-3a8 8 0 0 1 16 0v3Z',
  bell: 'M18 8a6 6 0 0 0-12 0c0 8-3 8-3 10h18c0-2-3-2-3-10M10 21h4',
  chart: 'M4 3v17h17M8 16v-5m5 5V6m5 10V9',
  book: 'M12 5v16M3 3h5l4 2 4-2h5v16h-5l-4 2-4-2H3Z',
  calendar: 'M4 5h16v16H4ZM4 10h16M8 3v4m8-4v4M8 14h1m3 0h1m3 0h1M8 17h1m3 0h1',
  file: 'M14 3H5v18h14V8ZM14 3v5h5M8 12h8M8 16h6',
  check: 'M9 3H5v18h14v-9M9 3v4h6V3ZM11 13l3 3 7-8',
  award: 'M17 8A5 5 0 1 1 7 8a5 5 0 0 1 10 0ZM8 12l-2 9 6-3 6 3-2-9',
  users: 'M14 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0ZM3 21v-3a7 7 0 0 1 14 0v3M17 4a3 3 0 0 1 0 6m2 4a6 6 0 0 1 3 7',
  menu: 'M4 6h16M4 12h12M4 18h16', close: 'm6 6 12 12M6 18 18 6',
  chevron: 'm6 9 6 6 6-6', logout: 'M9 3H4v18h5M9 12h12m-5-5 5 5-5 5', arrow: 'M4 12h16m-6-6 6 6-6 6',
}
function Icon({ name }: { name: IconName }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
}

export function MainLayout({ user, logout }: { user: AuthUser; logout: () => void }) {
  const [mobile, setMobile] = useState(() => window.matchMedia?.('(max-width: 800px)').matches ?? false)
  const [sidebarOpen, setSidebarOpen] = useState(!mobile)
  const [collapsedGroups, setCollapsedGroups] = useState<string[]>([])
  const [selected, setSelected] = useState<MenuItem>(HOME_ITEM)
  const [panel, setPanel] = useState<'notifications' | 'account' | null>(null)
  const sidebar = useRef<HTMLElement>(null)
  const toggle = useRef<HTMLButtonElement>(null)
  const headerActions = useRef<HTMLDivElement>(null)
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.user_id
  const groups = DASHBOARD_MENU[user.role]
  const SelectedAcademicPage = user.role === 1 && selected.id in academicPages ? academicPages[selected.id as keyof typeof academicPages] : null
  const shortcuts = groups.flatMap((group) => group.items).slice(0, 3)

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
  function select(item: MenuItem) {
    setSelected(item); setPanel(null)
    if (mobile) closeDrawer()
  }
  function menuButton(item: MenuItem) {
    return <button key={item.id} type="button" className={`dash-menu-item ${selected.id === item.id ? 'is-active' : ''}`} aria-current={selected.id === item.id ? 'page' : undefined} onClick={() => select(item)}><Icon name={item.icon} /><span>{item.label}</span>{selected.id === item.id && <span className="dash-active-dot" />}</button>
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
          <section id="dash-account" className="dash-popover" aria-label="Tài khoản" hidden={panel !== 'account'}><h2>{name}</h2><p>{ROLE_LABEL[user.role]} · {user.user_id}</p><button type="button" onClick={() => select(PROFILE_ITEM)}>Xem thông tin cá nhân <Icon name="arrow" /></button></section>
        </div>
      </header>
      {mobile && sidebarOpen && <button className="dash-backdrop" type="button" aria-label="Đóng menu điều hướng" onClick={closeDrawer} tabIndex={-1} />}
      <aside ref={sidebar} id="dashboard-sidebar" className="dash-sidebar" hidden={!sidebarOpen} role={mobile ? 'dialog' : undefined} aria-modal={mobile ? true : undefined} aria-label="Menu điều hướng" onKeyDown={(event) => {
        if (!mobile || event.key !== 'Tab') return
        const controls = Array.from(sidebar.current?.querySelectorAll<HTMLButtonElement>('button') ?? []).filter((button) => !button.closest('[hidden]'))
        const first = controls[0], last = controls.at(-1)
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus() }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus() }
      }}>
        {mobile && <button className="dash-drawer-close" type="button" aria-label="Đóng menu" onClick={closeDrawer}><Icon name="close" /></button>}
        <div className="dash-university"><span className="dash-qnu">QNU<span>QUY NHON UNIVERSITY</span></span><span>CỔNG THÔNG TIN ĐỒ ÁN</span></div>
        <div className="dash-profile"><span className="dash-avatar"><Icon name="user" /></span><strong>{name}</strong><span>{ROLE_LABEL[user.role]} · {user.user_id}</span></div>
        <nav aria-label="Chức năng">{menuButton(HOME_ITEM)}{groups.map((group) => <div className="dash-menu-group" key={group.id}>
          {group.label !== null && <button className="dash-group-toggle" type="button" aria-expanded={!collapsedGroups.includes(group.id)} aria-controls={`menu-${group.id}`} onClick={() => setCollapsedGroups((current) => current.includes(group.id) ? current.filter((id) => id !== group.id) : [...current, group.id])}>{group.label}<Icon name="chevron" /></button>}
          <div id={`menu-${group.id}`} hidden={group.label !== null && collapsedGroups.includes(group.id)}>{group.items.map(menuButton)}</div>
        </div>)}</nav>
        <div className="dash-sidebar-bottom"><button type="button" className="dash-menu-item" onClick={logout}><Icon name="logout" /><span>Đăng xuất</span></button><small>Hệ thống quản lý đồ án tốt nghiệp</small></div>
      </aside>
      <div className="dash-workspace" inert={mobile && sidebarOpen}>
        <main id="dashboard-content" className="dash-main" tabIndex={-1}>
          <div className="dash-breadcrumb">Cổng thông tin <span>/</span> {ROLE_LABEL[user.role]} <span>/</span> <strong>{selected.label}</strong></div>
          <div className="dash-page-heading"><div><p className="dash-overline">KHÔNG GIAN LÀM VIỆC</p><h1>{selected.id === 'home' ? ROLE_LABEL[user.role] : selected.label}</h1></div><span className="dash-role-badge"><span />{ROLE_LABEL[user.role]}</span></div>
          {selected.id === 'home' ? <>
            <section className="dash-welcome"><div><span className="dash-overline">CÙNG BẠN TRÊN HÀNH TRÌNH TỐT NGHIỆP</span><h2>Xin chào, {name}!</h2><p>Chào mừng bạn đến với cổng thông tin quản lý đồ án.<br />Truy cập các tiện ích và quản lý công việc của bạn tại đây.</p><button type="button" onClick={() => select(PROFILE_ITEM)}>Thông tin của tôi <Icon name="arrow" /></button></div><div className="dash-welcome-art" aria-hidden="true"><Icon name="book" /><span>Ý tưởng hôm nay.<br />Thành quả ngày mai.</span></div></section>
            <section className="dash-shortcuts" aria-labelledby="shortcuts-title"><div className="dash-section-heading"><h2 id="shortcuts-title">Truy cập nhanh</h2><span>Tiện ích dành cho bạn</span></div><div className="dash-card-grid">{shortcuts.map((item, index) => <button className="dash-shortcut" type="button" aria-label={`Mở ${item.label}`} key={item.id} onClick={() => select(item)}><span className="dash-card-number">0{index + 1}</span><span className="dash-card-icon"><Icon name={item.icon} /></span><strong>{item.label}</strong><span className="dash-card-description">Truy cập phân hệ <Icon name="arrow" /></span></button>)}</div></section>
            <div className="dash-bottom-grid"><section className="dash-surface"><div className="dash-section-heading"><h2>Thông báo</h2><Icon name="bell" /></div><div className="dash-empty"><span className="dash-empty-icon"><Icon name="bell" /></span><h3>Chưa có dữ liệu thông báo</h3><p>Chức năng thông báo đang được phát triển.</p></div></section><section className="dash-surface dash-account-summary"><div className="dash-section-heading"><h2>Thông tin tài khoản</h2><Icon name="user" /></div><dl><div><dt>Họ và tên</dt><dd>{name}</dd></div><div><dt>MSSV/UserID</dt><dd>{user.user_id}</dd></div><div><dt>Vai trò</dt><dd>{ROLE_LABEL[user.role]}</dd></div></dl></section></div>
          </> : SelectedAcademicPage ? <SelectedAcademicPage key={selected.id} logout={logout} /> : <section className="dash-surface dash-placeholder"><span className="dash-empty-icon"><Icon name={selected.icon} /></span><span className="dash-development-badge">Đang phát triển</span><h2>{selected.label}</h2><p>Chức năng này đang được phát triển. Dữ liệu sẽ hiển thị khi phân hệ được triển khai.</p><button type="button" onClick={() => select(HOME_ITEM)}>Về tổng quan <Icon name="arrow" /></button></section>}
        </main>
        <footer className="dash-footer"><span>TRƯỜNG ĐẠI HỌC QUY NHƠN</span><span>Hệ thống quản lý đồ án tốt nghiệp</span></footer>
      </div>
    </div>
  )
}
