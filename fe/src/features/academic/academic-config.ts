import type { AcademicRecord, Resource, WriteResources } from './academic-api'

export interface Field { key: string; label: string; type?: 'number' | 'department' | 'major' | 'sub-major' | 'email' | 'date' | 'password'; required?: boolean; integer?: boolean }
export const CONFIG: Record<Resource, { singular: string; id: string; fields: Field[] }> = {
  departments: { singular: 'khoa', id: 'department_id', fields: [{ key: 'department_id', label: 'Mã khoa', required: true }, { key: 'name', label: 'Tên khoa', required: true }] },
  majors: { singular: 'ngành', id: 'major_id', fields: [{ key: 'major_id', label: 'Mã ngành', required: true }, { key: 'name', label: 'Tên ngành' }, { key: 'department_id', label: 'Khoa', type: 'department' }] },
  students: { singular: 'sinh viên', id: 'student_id', fields: [{ key: 'student_id', label: 'Mã sinh viên / UserID', required: true }, { key: 'major_id', label: 'Ngành', type: 'major', required: true }, { key: 'sub_major_id', label: 'Chuyên ngành', type: 'sub-major' }, { key: 'accumulated_credits', label: 'Tín chỉ tích lũy', type: 'number', required: true, integer: true }, { key: 'gpa', label: 'GPA', type: 'number', required: true }] },
  lecturers: { singular: 'giảng viên', id: 'lecturer_id', fields: [{ key: 'lecturer_id', label: 'Mã giảng viên / UserID', required: true }, { key: 'department_id', label: 'Khoa', type: 'department' }] },
}
export const USER_FIELDS: Field[] = [
  { key: 'user.last_name', label: 'Họ' }, { key: 'user.first_name', label: 'Tên' },
  { key: 'user.gender', label: 'Giới tính', type: 'number', integer: true },
  { key: 'user.date_of_birth', label: 'Ngày sinh', type: 'date' },
  { key: 'user.email', label: 'Email', type: 'email', required: true },
  { key: 'user.phone', label: 'Số điện thoại', required: true },
  { key: 'user.status', label: 'Trạng thái', type: 'number', integer: true },
  { key: 'user.password', label: 'Mật khẩu', type: 'password', required: true },
]
CONFIG.students.fields.push(...USER_FIELDS)
CONFIG.lecturers.fields.push(...USER_FIELDS)
export const valueOf = (row: AcademicRecord, key: string): string => {
  if (key === 'name' && 'user' in row) return [row.user?.last_name, row.user?.first_name].filter(Boolean).join(' ')
  if (key.startsWith('user.')) return 'user' in row && row.user ? String((row.user as unknown as Record<string, unknown>)[key.slice(5)] ?? '') : ''
  return String((row as unknown as Record<string, unknown>)[key] ?? '')
}
export function addressable(resource: Resource, id: string) {
  if (resource !== 'lecturers' && resource !== 'students') return /^(0|[1-9]\d*)$/.test(id)
  return !!id && !id.includes('/') && !id.includes('\\') && id !== '.' && id !== '..' &&
    !Array.from(id).some((char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127)
}

export function validate(resource: Resource, values: Record<string, string>, editing = false): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const field of CONFIG[resource].fields) {
    const value = values[field.key]?.trim() ?? ''
    if (field.required && !(editing && field.type === 'password') && !value) errors[field.key] = 'Vui lòng nhập hoặc chọn giá trị.'
    else if (field.type === 'number' && value && (!Number.isFinite(Number(value)) || (field.integer && !Number.isSafeInteger(Number(value))))) errors[field.key] = field.integer ? 'Vui lòng nhập số nguyên.' : 'Vui lòng nhập số hợp lệ.'
    else if (value.length > 255 && field.key === CONFIG[resource].id) errors[field.key] = 'Mã không được dài quá 255 ký tự.'
  }
  const id = CONFIG[resource].id
  if (values[id]?.trim() && !addressable(resource, values[id].trim())) errors[id] = resource === 'students' || resource === 'lecturers' ? 'Mã không được chứa ký tự điều khiển, dấu phân cách đường dẫn hoặc chỉ là dấu chấm.' : 'API hiện chỉ hỗ trợ mã số nguyên không âm, không có số 0 ở đầu.'
  return errors
}

// Construct explicit DTOs: never send table labels or unrelated form state.
export function toDTO<K extends Resource>(resource: K, values: Record<string, string>): WriteResources[K] {
  const text = (key: string) => values[key]?.trim() ?? ''
  const optional = (key: string) => text(key) || null
  const user = { last_name: optional('user.last_name'), first_name: optional('user.first_name'), gender: text('user.gender') ? Number(text('user.gender')) : null, date_of_birth: optional('user.date_of_birth'), email: text('user.email'), phone: text('user.phone'), status: text('user.status') ? Number(text('user.status')) : null, ...(values['user.password'] ? { password: values['user.password'] } : {}) }
  const dtos: WriteResources = {
    departments: { department_id: text('department_id'), name: text('name') },
    majors: { major_id: text('major_id'), name: optional('name'), department_id: optional('department_id') },
    students: { student_id: text('student_id'), major_id: text('major_id'), sub_major_id: optional('sub_major_id'), accumulated_credits: Number(text('accumulated_credits')), gpa: Number(text('gpa')), user },
    lecturers: { lecturer_id: text('lecturer_id'), department_id: optional('department_id'), user },
  }
  return dtos[resource]
}
