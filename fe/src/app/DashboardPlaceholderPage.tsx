import { Link } from 'react-router-dom'
import { HOME_ITEM, dashboardPath } from '../components/layout/dashboard-menu'
import { DashboardIcon as Icon } from '../components/layout/DashboardIcon'
import { useDashboardLayout } from '../components/layout/dashboard-context'

export function DashboardPlaceholderPage() {
  const { user, selected, onNavigate } = useDashboardLayout()
  return <section className="dash-surface dash-placeholder"><span className="dash-empty-icon"><Icon name={selected.icon} /></span><span className="dash-development-badge">Đang phát triển</span><h2>{selected.label}</h2><p>Chức năng này đang được phát triển. Dữ liệu sẽ hiển thị khi phân hệ được triển khai.</p><Link to={dashboardPath(user.role, HOME_ITEM)} onClick={onNavigate}>Về tổng quan <Icon name="arrow" /></Link></section>
}
