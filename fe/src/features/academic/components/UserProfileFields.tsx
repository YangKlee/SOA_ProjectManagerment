import { USER_FIELDS } from '../academic-config'
import type { AcademicManagement } from '../useAcademicManagement'
import { AcademicFormField } from './AcademicFormField'
import type { SelectOption } from './AcademicFormField'

const OPTIONS: Record<string, SelectOption[]> = {
  'user.gender': [{ id: '1', label: 'Nam' }, { id: '0', label: 'Nữ' }],
  'user.status': [{ id: '1', label: 'Hoạt động' }, { id: '0', label: 'Khóa' }],
}

export function UserProfileFields({ state }: { state: AcademicManagement }) {
  return <>{USER_FIELDS.map((field) => <AcademicFormField key={field.key} state={state} name={field.key} options={OPTIONS[field.key]} showOptionIds={false} />)}</>
}
