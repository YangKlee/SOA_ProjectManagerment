import { apiClient } from '../../services/api-client'

export interface Department { department_id: string; name: string }
export interface Major { major_id: string; name: string | null; department_id: string | null }
export interface SubMajor { sub_major_id: string; name: string | null; major_id: string | null }
export interface Student { student_id: string; major_id: string; sub_major_id: string | null; accumulated_credits: number; gpa: number }
export interface Lecturer { lecturer_id: string; department_id: string | null }
export interface Resources { departments: Department; majors: Major; students: Student; lecturers: Lecturer; 'sub-majors': SubMajor }
export type Resource = Exclude<keyof Resources, 'sub-majors'>
export type AcademicRecord = Department | Major | Student | Lecturer

const path = (resource: keyof Resources, id?: string) => `/academic/api/${resource}/${id === undefined ? '' : `${encodeURIComponent(id)}/`}`
export async function listRecords<K extends keyof Resources>(resource: K, signal: AbortSignal): Promise<Resources[K][]> {
  const { data } = await apiClient.get<Resources[K][]>(path(resource), { signal })
  if (!Array.isArray(data)) throw new Error('Invalid academic list response')
  return data
}
export async function saveRecord<K extends Resource>(resource: K, data: Resources[K], signal: AbortSignal, id?: string): Promise<void> {
  if (id === undefined) await apiClient.post(path(resource), data, { signal })
  else await apiClient.patch(path(resource, id), data, { signal })
}
export async function deleteRecord(resource: Resource, id: string, signal: AbortSignal): Promise<void> {
  await apiClient.delete(path(resource, id), { signal })
}
