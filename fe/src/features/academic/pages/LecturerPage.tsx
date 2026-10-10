import { useAcademicManagement } from '../useAcademicManagement'
import { valueOf } from '../academic-config'
import { AcademicFormField } from '../components/AcademicFormField'
import { AcademicManagementView } from '../components/AcademicManagementView'
import { UserProfileFields } from '../components/UserProfileFields'

export function LecturerPage({ logout }: { logout: () => void }) {
  const state = useAcademicManagement('lecturers', logout)
  const departments = state.departments.map((row) => ({ id: row.department_id, label: row.name }))
  return <AcademicManagementView state={state} searchFields={['lecturer_id', 'name']} columns={[
    { key: 'name', label: 'Họ tên' }, { key: 'user.email', label: 'Email' },
    { key: 'lecturer_id', label: 'Mã giảng viên / UserID' },
    { key: 'department_id', label: 'Khoa', render: (row) => {
      const id = valueOf(row, 'department_id')
      const name = state.departments.find((item) => item.department_id === id)?.name
      return name ? `${name} (${id})` : id || '—'
    } },
  ]}>
    <AcademicFormField state={state} name="lecturer_id" />
    <AcademicFormField state={state} name="department_id" options={departments} />
    <UserProfileFields state={state} />
  </AcademicManagementView>
}
