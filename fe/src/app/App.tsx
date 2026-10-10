import { Route, Routes } from 'react-router-dom'
import { GuestRoute, RoleRoute, SessionRedirect } from '../features/auth/AuthRoutes'
import { LoginPage } from '../features/auth/LoginPage'
import { RoleHomePage } from './RoleHomePage'

export function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route element={<RoleRoute role={1} />}>
        <Route path="/admin" element={<RoleHomePage />} />
      </Route>
      <Route element={<RoleRoute role={2} />}>
        <Route path="/lecture" element={<RoleHomePage />} />
      </Route>
      <Route element={<RoleRoute role={3} />}>
        <Route path="/student" element={<RoleHomePage />} />
      </Route>
      <Route path="*" element={<SessionRedirect />} />
    </Routes>
  )
}
