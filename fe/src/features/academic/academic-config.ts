import type { AcademicRecord, Resource, Resources } from './academic-api'

export interface Field { key: string; label: string; type?: 'number' | 'department' | 'major' | 'sub-major'; required?: boolean; integer?: boolean }
export const CONFIG: Record<Resource, { singular: string; id: string; fields: Field[] }> = {
  departments: { singular: 'khoa', id: 'department_id', fields: [{ key: 'department_id', label: 'Mã khoa', required: true }, { key: 'name', label: 'Tên khoa', required: true }] },
  majors: { singular: 'ngành', id: 'major_id', fields: [{ key: 'major_id', label: 'Mã ngành', required: true }, { key: 'name', label: 'Tên ngành' }, { key: 'department_id', label: 'Khoa', type: 'department' }] },
  students: { singular: 'sinh viên', id: 'student_id', fields: [{ key: 'student_id', label: 'Mã sinh viên / UserID', required: true }, { key: 'major_id', label: 'Ngành', type: 'major', required: true }, { key: 'sub_major_id', label: 'Chuyên ngành', type: 'sub-major' }, { key: 'accumulated_credits', label: 'Tín chỉ tích lũy', type: 'number', required: true, integer: true }, { key: 'gpa', label: 'GPA', type: 'number', required: true }] },
  lecturers: { singular: 'giảng viên', id: 'lecturer_id', fields: [{ key: 'lecturer_id', label: 'Mã giảng viên / UserID', required: true }, { key: 'department_id', label: 'Khoa', type: 'department' }] },
}
export const valueOf = (row: AcademicRecord, key: string): string => String((row as unknown as Record<string, unknown>)[key] ?? '')
export const addressable = (resource: Resource, id: string) => resource === 'lecturers' || /^(0|[1-9]\d*)$/.test(id)

export function validate(resource: Resource, values: Record<string, string>): Record<string, string> {
  const errors: Record<string, string> = {}
  for (const field of CONFIG[resource].fields) {
    const value = values[field.key]?.trim() ?? ''
    if (field.required && !value) errors[field.key] = 'Vui lòng nhập hoặc chọn giá trị.'
    else if (field.type === 'number' && value && (!Number.isFinite(Number(value)) || (field.integer && !Number.isInteger(Number(value))))) errors[field.key] = field.integer ? 'Vui lòng nhập số nguyên.' : 'Vui lòng nhập số hợp lệ.'
    else if (value.length > 255 && field.key === CONFIG[resource].id) errors[field.key] = 'Mã không được dài quá 255 ký tự.'
  }
  const id = CONFIG[resource].id
  if (values[id]?.trim() && !addressable(resource, values[id].trim())) errors[id] = 'API hiện chỉ hỗ trợ mã số nguyên không âm, không có số 0 ở đầu.'
  return errors
}

// Construct explicit DTOs: never send table labels or unrelated form state.
export function toDTO<K extends Resource>(resource: K, values: Record<string, string>): Pick<Resources, Resource>[K] {
  const text = (key: string) => values[key]?.trim() ?? ''
  const optional = (key: string) => text(key) || null
  const dtos: Pick<Resources, Resource> = {
    departments: { department_id: text('department_id'), name: text('name') },
    majors: { major_id: text('major_id'), name: optional('name'), department_id: optional('department_id') },
    students: { student_id: text('student_id'), major_id: text('major_id'), sub_major_id: optional('sub_major_id'), accumulated_credits: Number(text('accumulated_credits')), gpa: Number(text('gpa')) },
    lecturers: { lecturer_id: text('lecturer_id'), department_id: optional('department_id') },
  }
  return dtos[resource]
}
