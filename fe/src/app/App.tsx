import { Route, Routes } from 'react-router-dom'
import { GuestRoute, RoleRoute, SessionRedirect } from '../features/auth/AuthRoutes'
import { LoginPage } from '../features/auth/LoginPage'
import { RoleHomePage } from './RoleHomePage'
import { ROLE_HOME } from '../features/auth/auth-types'
import { HOME_ITEM, dashboardItems, ACADEMIC_PAGE_IDS } from '../components/layout/dashboard-menu'
import { DashboardHomePage } from './DashboardHomePage'
import { DashboardPlaceholderPage } from './DashboardPlaceholderPage'
import { AcademicRoutePage } from './AcademicRoutePage'
import { NotFoundPage } from './NotFoundPage'

export function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      {([1, 2, 3] as const).map((role) => <Route key={role} element={<RoleRoute role={role} />}>
        <Route path={ROLE_HOME[role]} element={<RoleHomePage />}>
          <Route index element={<DashboardHomePage />} />
          {dashboardItems(role).filter((item) => item !== HOME_ITEM).map((item) => {
            const academicId = role === 1 ? ACADEMIC_PAGE_IDS.find((id) => id === item.id) : undefined
            return <Route key={item.id} path={item.path} element={academicId
              ? <AcademicRoutePage id={academicId} /> : <DashboardPlaceholderPage />} />
          })}
          <Route path="*" element={<NotFoundPage withinLayout />} />
        </Route>
      </Route>)}
      <Route path="/" element={<SessionRedirect />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
