import { useCallback, useEffect, useRef, useState } from 'react'
import { normalizeApiError } from '../../services/api-error'
import { listRecords } from '../academic/academic-api'
import type { Lecturer, Major } from '../academic/academic-api'
import { createTopic, getTopic, listTopics } from './topic-api'
import type { CreateTopic, Topic } from './topic-api'

export type TopicField = 'name' | 'description' | 'advisor_id' | 'major_id'
export const numericMajor = (id: string) => /^[0-9]+$/.test(id)

export function useTopics(canCreate: boolean, logout: () => void) {
  const [rows, setRows] = useState<Topic[]>([])
  const [loading, setLoading] = useState(true)
  const [listError, setListError] = useState('')
  const [query, setQuery] = useState('')
  const [appliedQuery, setAppliedQuery] = useState('')
  const [draft, setDraft] = useState<CreateTopic | null>(null)
  const [majors, setMajors] = useState<Major[]>([])
  const [lecturers, setLecturers] = useState<Lecturer[]>([])
  const [optionsReady, setOptionsReady] = useState(false)
  const [optionsLoading, setOptionsLoading] = useState(false)
  const [optionsError, setOptionsError] = useState('')
  const [formError, setFormError] = useState('')
  const [errors, setErrors] = useState<Partial<Record<TopicField, string>>>({})
  const [busy, setBusy] = useState(false)
  const [uncertain, setUncertain] = useState(false)
  const [notice, setNotice] = useState('')
  const locked = useRef(false)
  const loadRequest = useRef<AbortController | null>(null)
  const optionsRequest = useRef<AbortController | null>(null)
  const mutation = useRef<AbortController | null>(null)

  const failureMessage = useCallback((cause: unknown) => {
    const failure = normalizeApiError(cause)
    if (failure.kind === 'cancelled') return ''
    if (failure.status === 401) { logout(); return '' }
    if (failure.status === 503) return 'Dịch vụ tạm thời không khả dụng. Vui lòng thử lại sau.'
    if (failure.status === 409) return 'Mã đề tài đã tồn tại hoặc dữ liệu còn liên kết. Vui lòng kiểm tra kết quả.'
    return failure.message
  }, [logout])

  const reload = useCallback(async () => {
    loadRequest.current?.abort()
    const controller = new AbortController()
    loadRequest.current = controller
    setLoading(true); setListError('')
    try {
      const result = await listTopics(controller.signal)
      if (!controller.signal.aborted) setRows(result)
    } catch (cause) {
      if (!controller.signal.aborted) setListError(failureMessage(cause))
    } finally { if (!controller.signal.aborted) setLoading(false) }
  }, [failureMessage])

  useEffect(() => {
    let disposed = false
    void Promise.resolve().then(() => { if (!disposed) return reload() })
    return () => {
      disposed = true
      loadRequest.current?.abort(); optionsRequest.current?.abort(); mutation.current?.abort()
    }
  }, [reload])

  async function loadOptions() {
    optionsRequest.current?.abort()
    const controller = new AbortController()
    optionsRequest.current = controller
    setOptionsReady(false); setOptionsLoading(true); setOptionsError('')
    try {
      const [courses, advisors] = await Promise.all([
        listRecords('majors', controller.signal), listRecords('lecturers', controller.signal),
      ])
      if (controller.signal.aborted) return
      setMajors(courses); setLecturers(advisors); setOptionsReady(true)
    } catch (cause) {
      if (!controller.signal.aborted) setOptionsError(failureMessage(cause))
    } finally { if (!controller.signal.aborted) setOptionsLoading(false) }
  }

  function open() {
    if (!canCreate || locked.current || draft) return
    try {
      const id = crypto.randomUUID()
      setDraft({ topic_id: id, name: '', description: '', advisor_id: '', major_id: '' })
      setErrors({}); setFormError(''); setUncertain(false); setNotice('')
      void loadOptions()
    } catch {
      setListError('Không thể sinh mã đề tài. Vui lòng sử dụng HTTPS hoặc localhost.')
    }
  }
  function close() {
    if (locked.current) return
    optionsRequest.current?.abort()
    setDraft(null); setErrors({}); setFormError(''); setUncertain(false)
  }
  function change(key: TopicField, value: string) {
    if (locked.current || uncertain) return
    setDraft(previous => previous && { ...previous, [key]: value })
    setErrors(previous => ({ ...previous, [key]: undefined }))
  }
  async function saved() {
    setDraft(null); setUncertain(false); setFormError(''); setErrors({})
    setNotice('Đã tạo đề tài.')
    await reload()
  }
  async function save(): Promise<TopicField | undefined> {
    if (!canCreate || !draft || locked.current || !optionsReady || uncertain) return
    const invalid: Partial<Record<TopicField, string>> = {}
    if (!draft.name.trim()) invalid.name = 'Vui lòng nhập tên đề tài.'
    if (!lecturers.some(row => row.lecturer_id === draft.advisor_id)) invalid.advisor_id = 'Vui lòng chọn giáo viên hướng dẫn.'
    if (!majors.some(row => row.major_id === draft.major_id) || !numericMajor(draft.major_id)) invalid.major_id = 'Vui lòng chọn ngành có mã số hợp lệ.'
    setErrors(invalid)
    const first = Object.keys(invalid)[0] as TopicField | undefined
    if (first) return first
    locked.current = true; setBusy(true); setFormError('')
    const controller = new AbortController()
    mutation.current = controller
    try {
      await createTopic({ ...draft, name: draft.name.trim() }, controller.signal)
      if (!controller.signal.aborted) await saved()
    } catch (cause) {
      if (controller.signal.aborted) return
      const failure = normalizeApiError(cause)
      const ambiguous = failure.kind === 'network' || failure.kind === 'timeout' || failure.kind === 'unknown' || failure.status === 409 || (failure.status ?? 0) >= 500
      setUncertain(ambiguous)
      setFormError(ambiguous ? `${failureMessage(cause)} Chưa xác định kết quả tạo. Hãy kiểm tra kết quả trước khi gửi lại.` : failureMessage(cause))
      if (failure.status === 400 && failure.details && typeof failure.details === 'object') {
        const fields = failure.details as Record<string, unknown>
        const next: Partial<Record<TopicField, string>> = {}
        for (const key of ['name', 'description', 'advisor_id', 'major_id'] as const) {
          if (key in fields) next[key] = 'Giá trị không hợp lệ. Vui lòng kiểm tra lại.'
        }
        setErrors(next)
        return Object.keys(next)[0] as TopicField | undefined
      }
    } finally { locked.current = false; if (!controller.signal.aborted) setBusy(false) }
  }
  async function checkResult() {
    if (!canCreate || !draft || !uncertain || locked.current) return
    locked.current = true; setBusy(true); setFormError('')
    const controller = new AbortController()
    mutation.current = controller
    try {
      await getTopic(draft.topic_id, controller.signal)
      if (!controller.signal.aborted) await saved()
    } catch (cause) {
      if (controller.signal.aborted) return
      if (normalizeApiError(cause).status === 404) {
        setUncertain(false)
        setFormError('Chưa tìm thấy đề tài với mã này. Bạn có thể kiểm tra dữ liệu và gửi lại với cùng mã.')
      } else setFormError(failureMessage(cause))
    } finally { locked.current = false; if (!controller.signal.aborted) setBusy(false) }
  }
  const normalized = appliedQuery.toLocaleLowerCase('vi')
  const visibleRows = rows.filter(row => [row.topic_id, row.name].some(value => value.toLocaleLowerCase('vi').includes(normalized)))
  return { rows: visibleRows, total: rows.length, loading, listError, query, setQuery,
    search: () => setAppliedQuery(query.trim()), reload, draft, majors, lecturers,
    optionsReady, optionsLoading, optionsError, loadOptions, formError, errors, busy,
    uncertain, notice, open, close, change, save, checkResult }
}
export type TopicState = ReturnType<typeof useTopics>
