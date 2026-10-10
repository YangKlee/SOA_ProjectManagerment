import { useAcademicManagement } from '../useAcademicManagement'
import { valueOf } from '../academic-config'
import { AcademicFormField } from '../components/AcademicFormField'
import { AcademicManagementView } from '../components/AcademicManagementView'

export function StudentPage({ logout }: { logout: () => void }) {
  const state = useAcademicManagement('students', logout)
  const majors = state.majors.map((row) => ({ id: row.major_id, label: row.name }))
  const subMajors = state.subMajors.filter((row) => row.major_id === state.form?.major_id).map((row) => ({ id: row.sub_major_id, label: row.name }))
  return <AcademicManagementView state={state} searchFields={['student_id']} columns={[
    { key: 'student_id', label: 'Mã sinh viên / UserID' },
    { key: 'major_id', label: 'Ngành', render: (row) => {
      const id = valueOf(row, 'major_id')
      const name = state.majors.find((item) => item.major_id === id)?.name
      return name ? `${name} (${id})` : id || '—'
    } },
    { key: 'sub_major_id', label: 'Chuyên ngành', render: (row) => {
      const id = valueOf(row, 'sub_major_id')
      const name = state.subMajors.find((item) => item.sub_major_id === id)?.name
      return name ? `${name} (${id})` : id || '—'
    } },
    { key: 'accumulated_credits', label: 'Tín chỉ tích lũy' }, { key: 'gpa', label: 'GPA' },
  ]}>
    <AcademicFormField state={state} name="student_id" />
    <AcademicFormField state={state} name="major_id" options={majors} />
    <AcademicFormField state={state} name="sub_major_id" options={subMajors} />
    <AcademicFormField state={state} name="accumulated_credits" />
    <AcademicFormField state={state} name="gpa" />
  </AcademicManagementView>
}
