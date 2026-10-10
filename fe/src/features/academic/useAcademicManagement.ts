import { useCallback, useEffect, useRef, useState } from 'react'
import { normalizeApiError } from '../../services/api-error'
import { deleteRecord, listRecords, saveRecord } from './academic-api'
import type { AcademicRecord, Department, Major, Resource, SubMajor } from './academic-api'
import { CONFIG, toDTO, validate, valueOf } from './academic-config'

export function useAcademicManagement(resource: Resource, logout: () => void) {
  const config = CONFIG[resource]
  const [rows, setRows] = useState<AcademicRecord[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [majors, setMajors] = useState<Major[]>([])
  const [subMajors, setSubMajors] = useState<SubMajor[]>([])
  const [loading, setLoading] = useState(true)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [query, setQuery] = useState('')
  const [appliedQuery, setAppliedQuery] = useState('')
  const [form, setForm] = useState<Record<string, string> | null>(null)
  const [editing, setEditing] = useState<string | undefined>()
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [deleting, setDeleting] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const locked = useRef(false)
  const loadRequest = useRef<AbortController | null>(null)
  const mutation = useRef<AbortController | null>(null)

  const showError = useCallback((cause: unknown) => {
    const failure = normalizeApiError(cause)
    if (failure.kind === 'cancelled') return
    if (failure.status === 401) { logout(); return }
    const details = failure.details as { code?: string } | undefined
    setError(details?.code === 'operation_incomplete' ? 'Chưa xác định được kết quả thao tác. Tải lại và kiểm tra hồ sơ, tài khoản trước khi thử lại.' : failure.status === 409 ? 'Mã, email, số điện thoại bị trùng hoặc bản ghi còn liên kết. Vui lòng kiểm tra dữ liệu.' : failure.message)
    if (failure.status === 400 && failure.details && typeof failure.details === 'object') {
      const fields: Record<string, string> = {}
      const flat = Object.entries(failure.details).flatMap(([key, value]) => key === 'user' && value && typeof value === 'object' && !Array.isArray(value) ? Object.entries(value).map(([child, error]) => [`user.${child}`, error] as const) : [[key, value] as const])
      for (const [key, value] of flat) {
        if (!config.fields.some((field) => field.key === key)) continue
        if (typeof value === 'string') fields[key] = value
        else if (Array.isArray(value)) fields[key] = value.filter((item): item is string => typeof item === 'string').join(' ')
      }
      setErrors(fields)
    }
  }, [config, logout])

  const load = useCallback(async () => {
    loadRequest.current?.abort()
    const controller = new AbortController()
    loadRequest.current = controller
    setLoading(true); setReady(false); setError('')
    try {
      const [records, faculties, courses, specializations] = await Promise.all([
        listRecords(resource, controller.signal),
        resource === 'majors' || resource === 'lecturers' ? listRecords('departments', controller.signal) : Promise.resolve([]),
        resource === 'students' ? listRecords('majors', controller.signal) : Promise.resolve([]),
        resource === 'students' ? listRecords('sub-majors', controller.signal) : Promise.resolve([]),
      ])
      if (controller.signal.aborted) return
      setRows(records); setDepartments(faculties); setMajors(courses); setSubMajors(specializations); setReady(true)
    } catch (cause) { if (!controller.signal.aborted) showError(cause) }
    finally { if (!controller.signal.aborted) setLoading(false) }
  }, [resource, showError])

  useEffect(() => {
    let disposed = false
    void Promise.resolve().then(() => { if (!disposed) return load() })
    return () => { disposed = true; loadRequest.current?.abort(); mutation.current?.abort() }
  }, [load])

  function open(row?: AcademicRecord) {
    setForm(Object.fromEntries(config.fields.map((field) => [field.key, row ? valueOf(row, field.key) : ''])))
    setEditing(row ? valueOf(row, config.id) : undefined)
    setDeleting(null); setErrors({}); setError(''); setNotice('')
  }
  async function mutate(remove: boolean) {
    if (locked.current) return
    if (!remove && form) {
      const invalid = validate(resource, form, editing !== undefined)
      setErrors(invalid)
      if (Object.keys(invalid).length) {
        return Object.keys(invalid)[0]
      }
    }
    locked.current = true; setBusy(true); setError(''); setNotice(''); setErrors({})
    const controller = new AbortController()
    mutation.current = controller
    try {
      if (remove && deleting !== null) await deleteRecord(resource, deleting, controller.signal)
      else if (form) await saveRecord(resource, toDTO(resource, form), controller.signal, editing)
      if (controller.signal.aborted) return
      setNotice(remove ? 'Đã xóa dữ liệu.' : 'Đã lưu dữ liệu.')
      await load()
      if (!controller.signal.aborted) { setForm(null); setDeleting(null) }
    } catch (cause) { if (!controller.signal.aborted) showError(cause) }
    finally { locked.current = false; if (!controller.signal.aborted) setBusy(false) }
  }

  function closeForm() {
    if (locked.current) return
    setForm(null); setErrors({}); setError('')
  }
  function requestDelete(row: AcademicRecord) {
    setDeleting(valueOf(row, config.id)); setForm(null); setError(''); setNotice('')
  }
  function cancelDelete() { if (!locked.current) { setDeleting(null); setError('') } }
  function changeField(key: string, value: string) {
    setForm((previous) => previous && { ...previous, [key]: value, ...(key === 'major_id' ? { sub_major_id: '' } : {}) })
  }
  return { resource, config, rows, departments, majors, subMajors, loading, ready, error, notice,
    query, setQuery, appliedQuery, search: () => setAppliedQuery(query.trim().toLocaleLowerCase('vi')),
    form, editing, errors, deleting, busy, open, closeForm, requestDelete, cancelDelete,
    changeField, save: () => mutate(false), remove: () => mutate(true), reload: load }
}
export type AcademicManagement = ReturnType<typeof useAcademicManagement>
