import { useAcademicManagement } from '../useAcademicManagement'
import { AcademicFormField } from '../components/AcademicFormField'
import { AcademicManagementView } from '../components/AcademicManagementView'

export function DepartmentPage({ logout }: { logout: () => void }) {
  const state = useAcademicManagement('departments', logout)
  return <AcademicManagementView state={state} searchFields={['department_id', 'name']} columns={[
    { key: 'department_id', label: 'Mã khoa' }, { key: 'name', label: 'Tên khoa' },
  ]}>
    <AcademicFormField state={state} name="department_id" />
    <AcademicFormField state={state} name="name" />
  </AcademicManagementView>
}
