import { useAcademicManagement } from '../useAcademicManagement'
import { valueOf } from '../academic-config'
import { AcademicFormField } from '../components/AcademicFormField'
import { AcademicManagementView } from '../components/AcademicManagementView'

export function MajorPage({ logout }: { logout: () => void }) {
  const state = useAcademicManagement('majors', logout)
  const departments = state.departments.map((row) => ({ id: row.department_id, label: row.name }))
  return <AcademicManagementView state={state} searchFields={['major_id', 'name']} columns={[
    { key: 'major_id', label: 'Mã ngành' }, { key: 'name', label: 'Tên ngành' },
    { key: 'department_id', label: 'Khoa', render: (row) => {
      const id = valueOf(row, 'department_id')
      const name = state.departments.find((item) => item.department_id === id)?.name
      return name ? `${name} (${id})` : id || '—'
    } },
  ]}>
    <AcademicFormField state={state} name="major_id" />
    <AcademicFormField state={state} name="name" />
    <AcademicFormField state={state} name="department_id" options={departments} />
  </AcademicManagementView>
}
