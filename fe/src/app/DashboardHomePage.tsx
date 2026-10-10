import { Link } from 'react-router-dom'
import { ROLE_LABEL } from '../features/auth/auth-types'
import { DASHBOARD_MENU, PROFILE_ITEM, dashboardPath } from '../components/layout/dashboard-menu'
import { DashboardIcon as Icon } from '../components/layout/DashboardIcon'
import { useDashboardLayout } from '../components/layout/dashboard-context'

export function DashboardHomePage() {
  const { user, onNavigate } = useDashboardLayout()
  const name = [user.first_name, user.last_name].filter(Boolean).join(' ') || user.user_id
  const shortcuts = DASHBOARD_MENU[user.role].flatMap((group) => group.items).slice(0, 3)
  return <>
            <section className="dash-welcome"><div><span className="dash-overline">CÙNG BẠN TRÊN HÀNH TRÌNH TỐT NGHIỆP</span><h2>Xin chào, {name}!</h2><p>Chào mừng bạn đến với cổng thông tin quản lý đồ án.<br />Truy cập các tiện ích và quản lý công việc của bạn tại đây.</p><Link to={dashboardPath(user.role, PROFILE_ITEM)} onClick={onNavigate}>Thông tin của tôi <Icon name="arrow" /></Link></div><div className="dash-welcome-art" aria-hidden="true"><Icon name="book" /><span>Ý tưởng hôm nay.<br />Thành quả ngày mai.</span></div></section>
            <section className="dash-shortcuts" aria-labelledby="shortcuts-title"><div className="dash-section-heading"><h2 id="shortcuts-title">Truy cập nhanh</h2><span>Tiện ích dành cho bạn</span></div><div className="dash-card-grid">{shortcuts.map((item, index) => <Link className="dash-shortcut" aria-label={`Mở ${item.label}`} key={item.id} to={dashboardPath(user.role, item)} onClick={onNavigate}><span className="dash-card-number">0{index + 1}</span><span className="dash-card-icon"><Icon name={item.icon} /></span><strong>{item.label}</strong><span className="dash-card-description">Truy cập phân hệ <Icon name="arrow" /></span></Link>)}</div></section>
            <div className="dash-bottom-grid"><section className="dash-surface"><div className="dash-section-heading"><h2>Thông báo</h2><Icon name="bell" /></div><div className="dash-empty"><span className="dash-empty-icon"><Icon name="bell" /></span><h3>Chưa có dữ liệu thông báo</h3><p>Chức năng thông báo đang được phát triển.</p></div></section><section className="dash-surface dash-account-summary"><div className="dash-section-heading"><h2>Thông tin tài khoản</h2><Icon name="user" /></div><dl><div><dt>Họ và tên</dt><dd>{name}</dd></div><div><dt>MSSV/UserID</dt><dd>{user.user_id}</dd></div><div><dt>Vai trò</dt><dd>{ROLE_LABEL[user.role]}</dd></div></dl></section></div>
          </>
}
