import { useAuth } from '../features/auth/auth-context'
import { DepartmentPage } from '../features/academic/pages/DepartmentPage'
import { MajorPage } from '../features/academic/pages/MajorPage'
import { StudentPage } from '../features/academic/pages/StudentPage'
import { LecturerPage } from '../features/academic/pages/LecturerPage'

import { ACADEMIC_PAGE_IDS } from '../components/layout/dashboard-menu'
type AcademicPageId = typeof ACADEMIC_PAGE_IDS[number]
const pages = { faculties: DepartmentPage, majors: MajorPage, students: StudentPage, lecturers: LecturerPage }

export function AcademicRoutePage({ id }: { id: AcademicPageId }) {
  const { logout } = useAuth()
  const Page = pages[id]
  return <Page key={id} logout={logout} />
}
