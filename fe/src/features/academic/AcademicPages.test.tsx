import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient, setAccessToken } from '../../services/api-client'
import { DepartmentPage } from './pages/DepartmentPage'
import { MajorPage } from './pages/MajorPage'
import { StudentPage } from './pages/StudentPage'
import { LecturerPage } from './pages/LecturerPage'

const pages = { departments: DepartmentPage, majors: MajorPage, students: StudentPage, lecturers: LecturerPage }
function TestPage({ resource, logout }: { resource: Resource; logout: () => void }) {
  const Page = pages[resource]
  return <Page logout={logout} />
}
import type { Resource } from './academic-api'

let mock: MockAdapter
const logout = vi.fn()
const user = { user_id: '3', last_name: 'Nguyen', first_name: 'An', email: 'an@example.com', phone: '0900000000', gender: null, date_of_birth: null, status: null, role: 3, created_at: null, updated_at: null }
const userInput = { last_name: null, first_name: null, email: 'new@example.com', phone: '0900000001', gender: null, date_of_birth: null, status: null, password: 'secret' }
const baseFor = (resource: string) => `/academic/api/${resource === 'students' || resource === 'lecturers' ? 'v1/' : ''}${resource}/`
const fixtures = {
  departments: [{ department_id: '1', name: 'Công nghệ thông tin' }],
  majors: [{ major_id: '2', name: 'Phần mềm', department_id: '1' }],
  students: [{ student_id: '3', major_id: '2', sub_major_id: null, accumulated_credits: 90, gpa: 3.4, user }],
  lecturers: [{ lecturer_id: 'GV001', department_id: '1', user: { ...user, user_id: 'GV001', role: 2 } }],
  'sub-majors': [{ sub_major_id: '4', name: 'Web', major_id: '2' }, { sub_major_id: '5', name: 'Khác', major_id: '9' }],
}
beforeEach(() => {
  logout.mockReset(); setAccessToken('test-token')
  mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  for (const [resource, records] of Object.entries(fixtures)) mock.onGet(baseFor(resource)).reply(200, records)
})
afterEach(() => { mock.restore(); setAccessToken(null) })
const fill = (label: string, value: string) => fireEvent.change(screen.getByLabelText(new RegExp(`^${label}`)), { target: { value } })
async function openPage(resource: Resource) {
  render(<TestPage resource={resource} logout={logout} />)
  await waitFor(() => expect(screen.getByRole('button', { name: /^Thêm / })).toBeEnabled())
}
const cases = [
  { resource: 'departments' as const, id: '1', label: 'Mã khoa', values: { 'Mã khoa': '10', 'Tên khoa': 'Khoa mới' }, dto: { department_id: '10', name: 'Khoa mới' } },
  { resource: 'majors' as const, id: '2', label: 'Mã ngành', values: { 'Mã ngành': '10', 'Tên ngành': 'Ngành mới', Khoa: '1' }, dto: { major_id: '10', name: 'Ngành mới', department_id: '1' } },
  { resource: 'students' as const, id: '3', label: 'Mã sinh viên', values: { 'Mã sinh viên': '10', Ngành: '2', 'Chuyên ngành': '4', 'Tín chỉ': '100', GPA: '3.5', 'Giới tính': '1', 'Trạng thái': '0' }, dto: { student_id: '10', major_id: '2', sub_major_id: '4', accumulated_credits: 100, gpa: 3.5, user: { ...userInput, gender: 1, status: 0 } } },
  { resource: 'lecturers' as const, id: 'GV001', label: 'Mã giảng viên', values: { 'Mã giảng viên': 'GV002', Khoa: '1', 'Giới tính': '0', 'Trạng thái': '1' }, dto: { lecturer_id: 'GV002', department_id: '1', user: { ...userInput, gender: 0, status: 1 } } },
]

describe('Academic management', () => {
  it.each(cases)('creates, edits and deletes $resource through the gateway', async ({ resource, id, label, values, dto }) => {
    const base = baseFor(resource)
    mock.onPost(base).reply(201, dto)
    mock.onPatch(`${base}${id}/`).reply(200, fixtures[resource][0])
    mock.onDelete(`${base}${id}/`).reply(204)
    await openPage(resource)
    const add = screen.getByRole('button', { name: /^Thêm / })
    add.focus(); fireEvent.click(add)
    for (const [key, value] of Object.entries(values)) fill(key, value)
    if (resource === 'students' || resource === 'lecturers') { fill('Email', userInput.email); fill('Số điện thoại', userInput.phone); fill('Mật khẩu', userInput.password) }
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    expect(await screen.findByText('Đã lưu dữ liệu.')).toBeVisible()
    await waitFor(() => expect(screen.getByRole('button', { name: `Sửa ${id}` })).toBeEnabled())
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(add).toHaveFocus()
    expect(JSON.parse(mock.history.post[0].data)).toEqual(dto)
    expect(mock.history.post[0].headers?.Authorization).toBe('Bearer test-token')
    fireEvent.click(screen.getByRole('button', { name: `Sửa ${id}` }))
    expect(screen.getByLabelText(label, { exact: false })).toBeDisabled()
    if (resource === 'departments') fill('Tên khoa', 'Tên sửa')
    if (resource === 'majors' || resource === 'lecturers') fill('Khoa', '')
    if (resource === 'students') fill('GPA', '3.8')
    fireEvent.click(screen.getByRole('button', { name: 'Lưu' }))
    await waitFor(() => expect(mock.history.patch).toHaveLength(1))
    await waitFor(() => expect(screen.queryByRole('form')).not.toBeInTheDocument())
    await waitFor(() => expect(screen.getByRole('button', { name: `Xóa ${id}` })).toBeEnabled())
    if (resource === 'majors' || resource === 'lecturers') expect(JSON.parse(mock.history.patch[0].data).department_id).toBeNull()
    const remaining = { ...fixtures[resource][0] }
    expect(JSON.parse(mock.history.patch[0].data)[Object.keys(remaining)[0]]).toBe(id)
    fireEvent.click(screen.getByRole('button', { name: `Xóa ${id}` }))
    expect(mock.history.delete).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(mock.history.delete).toHaveLength(0)
    fireEvent.click(screen.getByRole('button', { name: `Xóa ${id}` }))
    mock.onGet(base).reply(200, [])
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận xóa' }))
    expect(await screen.findByText('Chưa có dữ liệu.')).toBeVisible()
    expect(mock.history.delete).toHaveLength(1)
  })

  it('searches records locally and reloads after a list failure', async () => {
    mock.onGet('/academic/api/departments/').reply(503)
    await openFailed('departments')
    mock.onGet('/academic/api/departments/').reply(200, fixtures.departments)
    fireEvent.click(screen.getByRole('button', { name: 'Tải lại' }))
    expect(await screen.findByText('Công nghệ thông tin')).toBeVisible()
    fill('Tìm kiếm', 'missing')
    expect(screen.getByText('Công nghệ thông tin')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByText('Không tìm thấy kết quả phù hợp.')).toBeVisible()
    fill('Tìm kiếm', 'CÔNG NGHỆ')
    expect(screen.getByText('Không tìm thấy kết quả phù hợp.')).toBeVisible()
    fireEvent.submit(screen.getByRole('search'))
    expect(screen.getByText('Công nghệ thông tin')).toBeVisible()
  })

  it.each(['students', 'lecturers'] as const)('prefills identity fields and omits unchanged password on %s', async (resource) => {
    const id = resource === 'students' ? '3' : 'GV001'
    mock.onPatch(`${baseFor(resource)}${id}/`).reply(200, fixtures[resource][0])
    await openPage(resource)
    fireEvent.click(screen.getByRole('button', { name: `Sửa ${id}` }))
    expect(screen.getByLabelText(/^Họ$/)).toHaveValue('Nguyen')
    expect(screen.getByLabelText(/^Tên$/)).toHaveValue('An')
    expect(screen.getByLabelText(/^Email/)).toHaveValue(user.email)
    expect(screen.getByRole('combobox', { name: 'Giới tính' })).toHaveValue('')
    expect(screen.getByRole('combobox', { name: 'Trạng thái' })).toHaveValue('')
    const password = screen.getByLabelText(/^Mật khẩu/)
    expect(password).toHaveValue('')
    expect(password).not.toBeRequired()
    fill('Tên$', 'Binh')
    fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(mock.history.patch).toHaveLength(1))
    const payload = JSON.parse(mock.history.patch[0].data)
    expect(payload.user.first_name).toBe('Binh')
    expect(payload.user.gender).toBeNull()
    expect(payload.user.status).toBeNull()
    expect(payload.user).not.toHaveProperty('password')
    for (const key of ['user_id', 'role', 'created_at', 'updated_at']) expect(payload.user).not.toHaveProperty(key)
  })

  it.each([
    { resource: 'students' as const, gender: 0, status: 0 },
    { resource: 'students' as const, gender: 1, status: 1 },
    { resource: 'lecturers' as const, gender: 0, status: 1 },
    { resource: 'lecturers' as const, gender: 1, status: 0 },
  ])('prefills and saves gender/status selects for $resource ($gender/$status)', async ({ resource, gender, status }) => {
    const id = resource === 'students' ? '3' : 'GV001'
    const row = { ...fixtures[resource][0], user: { ...fixtures[resource][0].user, gender, status } }
    mock.onGet(baseFor(resource)).reply(200, [row])
    mock.onPatch(`${baseFor(resource)}${id}/`).reply(200, row)
    await openPage(resource)
    fireEvent.click(screen.getByRole('button', { name: `Sửa ${id}` }))
    const genderSelect = screen.getByRole('combobox', { name: 'Giới tính' })
    const statusSelect = screen.getByRole('combobox', { name: 'Trạng thái' })
    expect(genderSelect).toHaveValue(String(gender))
    expect(statusSelect).toHaveValue(String(status))
    expect(within(genderSelect).getByRole('option', { name: 'Nam' })).toHaveValue('1')
    expect(within(genderSelect).getByRole('option', { name: 'Nữ' })).toHaveValue('0')
    expect(within(statusSelect).getByRole('option', { name: 'Hoạt động' })).toHaveValue('1')
    expect(within(statusSelect).getByRole('option', { name: 'Khóa' })).toHaveValue('0')
    fireEvent.change(genderSelect, { target: { value: String(1 - gender) } })
    fireEvent.change(statusSelect, { target: { value: String(1 - status) } })
    fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(mock.history.patch).toHaveLength(1))
    const payload = JSON.parse(mock.history.patch[0].data)
    expect(payload.user.gender).toBe(1 - gender)
    expect(payload.user.status).toBe(1 - status)
  })

  it('preserves unexpected legacy select values and permits clearing to null', async () => {
    const row = { ...fixtures.lecturers[0], user: { ...fixtures.lecturers[0].user, gender: 7, status: 9 } }
    mock.onGet(baseFor('lecturers')).reply(200, [row])
    mock.onPatch('/academic/api/v1/lecturers/GV001/').reply(200, row)
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Sửa GV001' }))
    expect(screen.getByRole('combobox', { name: 'Giới tính' })).toHaveValue('7')
    expect(screen.getByRole('combobox', { name: 'Trạng thái' })).toHaveValue('9')
    fill('Giới tính', '')
    fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(mock.history.patch).toHaveLength(1))
    const payload = JSON.parse(mock.history.patch[0].data)
    expect(payload.user.gender).toBeNull()
    expect(payload.user.status).toBe(9)
  })

  it.each(['students', 'lecturers'] as const)('searches %s by full name only after Search', async (resource) => {
    await openPage(resource)
    fill('Tìm kiếm', 'missing')
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.queryByRole('cell', { name: 'Nguyen An' })).not.toBeInTheDocument()
    fill('Tìm kiếm', 'NGUYEN AN')
    expect(screen.queryByRole('cell', { name: 'Nguyen An' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByRole('cell', { name: 'Nguyen An' })).toBeVisible()
  })

  it('supports string student IDs and sends an optional new password exactly', async () => {
    const row = { ...fixtures.students[0], student_id: 'SV001' }
    mock.onGet('/academic/api/v1/students/').reply(200, [row])
    mock.onPatch('/academic/api/v1/students/SV001/').reply(200, row)
    await openPage('students')
    expect(screen.getByRole('button', { name: 'Xóa SV001' })).toBeEnabled()
    fireEvent.click(screen.getByRole('button', { name: 'Sửa SV001' }))
    fill('Mật khẩu', '  new password  ')
    fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(mock.history.patch).toHaveLength(1))
    expect(JSON.parse(mock.history.patch[0].data).user.password).toBe('  new password  ')
  })

  it.each([409, 503])('preserves records and explains composite deletion failure %s', async (status) => {
    mock.onDelete('/academic/api/v1/lecturers/GV001/').reply(status, { code: status === 503 ? 'operation_incomplete' : 'conflict' })
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa GV001' }))
    expect(screen.getByText(/xóa cả hồ sơ và tài khoản/)).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận xóa' }))
    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(status === 503 ? 'kiểm tra hồ sơ' : 'bản ghi còn liên kết')
    expect(screen.getByRole('cell', { name: 'GV001' })).toBeVisible()
    expect(mock.history.delete).toHaveLength(1)
  })

  it('shows nested user validation errors without exposing unrelated fields', async () => {
    mock.onPatch('/academic/api/v1/lecturers/GV001/').reply(400, { user: { email: ['Email không hợp lệ.'], secret: 'hidden' } })
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Sửa GV001' }))
    fireEvent.submit(screen.getByRole('form'))
    expect(await screen.findByText('Email không hợp lệ.')).toBeVisible()
    expect(screen.queryByText('hidden')).not.toBeInTheDocument()
  })

  it.each(['departments', 'majors'] as const)('disables unsupported detail IDs for %s', async (resource) => {
    const idKey = { departments: 'department_id', majors: 'major_id', students: 'student_id' }[resource]
    mock.onGet(baseFor(resource)).reply(200, [{ ...fixtures[resource][0], [idKey]: 'A01' }])
    await openPage(resource)
    expect(screen.getByRole('button', { name: 'Sửa A01' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Xóa A01' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: /^Thêm / }))
    const form = screen.getByRole('form')
    fireEvent.change(within(form).getAllByRole('textbox')[0], { target: { value: '001' } })
    fireEvent.submit(form)
    expect(screen.getByText('API hiện chỉ hỗ trợ mã số nguyên không âm, không có số 0 ở đầu.')).toBeVisible()
    expect(mock.history.post).toHaveLength(0)
  })

  it('validates required fields and integer credits, filters and clears dependent specialization', async () => {
    mock.onGet('/academic/api/majors/').reply(200, [...fixtures.majors, { major_id: '9', name: 'Ngành khác', department_id: null }])
    await openPage('students')
    fireEvent.click(screen.getByRole('button', { name: /^Thêm / }))
    fireEvent.submit(screen.getByRole('form'))
    expect(screen.getByLabelText(/Mã sinh viên/)).toHaveFocus()
    expect(screen.getAllByText('Vui lòng nhập hoặc chọn giá trị.')).toHaveLength(7)
    fill('Mã sinh viên', '10'); fill('Ngành', '2'); fill('Chuyên ngành', '4'); fill('Tín chỉ', '1.5'); fill('GPA', '3')
    expect(screen.queryByRole('option', { name: 'Khác (5)' })).not.toBeInTheDocument()
    fireEvent.submit(screen.getByRole('form'))
    expect(screen.getByText('Vui lòng nhập số nguyên.')).toBeVisible()
    fill('Ngành', '9')
    expect(screen.getByLabelText('Chuyên ngành')).toHaveValue('')
    expect(screen.queryByRole('option', { name: 'Web (4)' })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Khác (5)' })).toBeVisible()
    expect(mock.history.post).toHaveLength(0)
  })

  it('keeps values and shows field errors for a rejected write', async () => {
    mock.onPost('/academic/api/departments/').reply(400, { department_id: ['Mã đã tồn tại.'], private: 'secret' })
    await openPage('departments')
    fireEvent.click(screen.getByRole('button', { name: /^Thêm / }))
    fill('Mã khoa', '10'); fill('Tên khoa', 'Test')
    fireEvent.submit(screen.getByRole('form'))
    expect(await screen.findByText('Mã đã tồn tại.')).toBeVisible()
    expect(within(screen.getByRole('dialog')).getByRole('alert')).toBeVisible()
    expect(screen.getByLabelText(/Mã khoa/)).toHaveValue('10')
    expect(screen.queryByText('secret')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Lưu' })).toBeEnabled()
  })

  it.each([403, 404, 500])('handles HTTP %s during deletion without removing records', async (status) => {
    mock.onDelete('/academic/api/v1/lecturers/GV001/').reply(status, { detail: 'private details' })
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Xóa GV001' }))
    fireEvent.click(screen.getByRole('button', { name: 'Xác nhận xóa' }))
    expect(await screen.findByRole('alert')).toBeVisible()
    expect(screen.getByRole('cell', { name: 'GV001' })).toBeVisible()
    expect(screen.queryByText('private details')).not.toBeInTheDocument()
    expect(logout).not.toHaveBeenCalled()
    expect(mock.history.delete).toHaveLength(1)
  })

  it.each(['network', 'timeout', '401'] as const)('handles %s while loading', async (kind) => {
    const handler = mock.onGet('/academic/api/departments/')
    if (kind === 'network') handler.networkError()
    else if (kind === 'timeout') handler.timeout()
    else handler.reply(401)
    render(<TestPage resource="departments" logout={logout} />)
    if (kind === '401') await waitFor(() => expect(logout).toHaveBeenCalledOnce())
    else expect(await screen.findByRole('alert')).toHaveTextContent(kind === 'network' ? 'Không thể kết nối' : 'quá thời gian chờ')
  })

  it('prevents duplicate writes and aborts pending mutations on unmount', async () => {
    let complete!: (value: [number, unknown]) => void
    mock.onPost('/academic/api/departments/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
    const view = render(<TestPage resource="departments" logout={logout} />)
    await waitFor(() => expect(screen.getByRole('button', { name: /^Thêm / })).toBeEnabled())
    fireEvent.click(screen.getByRole('button', { name: /^Thêm / }))
    fill('Mã khoa', '10'); fill('Tên khoa', 'New')
    fireEvent.submit(screen.getByRole('form')); fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(mock.history.post).toHaveLength(1))
    expect(screen.getByRole('button', { name: 'Đang lưu…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Đóng popup' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeDisabled()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.getByRole('dialog')).toBeVisible()
    view.unmount()
    expect(mock.history.post[0].signal?.aborted).toBe(true)
    await act(async () => complete([201, {}]))
    expect(mock.history.get).toHaveLength(1)
    expect(logout).not.toHaveBeenCalled()
  })

  it('logs out on an expired write and preserves the unsaved form until navigation', async () => {
    mock.onPatch('/academic/api/v1/lecturers/GV001/').reply(401)
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Sửa GV001' }))
    fireEvent.submit(screen.getByRole('form'))
    await waitFor(() => expect(logout).toHaveBeenCalledOnce())
    expect(screen.getByLabelText(/Mã giảng viên/)).toHaveValue('GV001')
    expect(mock.history.patch).toHaveLength(1)
  })

  it('distinguishes a successful save from a failed refresh', async () => {
    mock.onPatch('/academic/api/v1/lecturers/GV001/').reply(200, fixtures.lecturers[0])
    await openPage('lecturers')
    fireEvent.click(screen.getByRole('button', { name: 'Sửa GV001' }))
    mock.onGet('/academic/api/v1/lecturers/').reply(503)
    fireEvent.submit(screen.getByRole('form'))
    expect(await screen.findByText('Đã lưu dữ liệu.')).toBeVisible()
    expect(await screen.findByRole('alert')).toBeVisible()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tải lại' })).toBeEnabled()
    expect(mock.history.patch).toHaveLength(1)
  })

  it('aborts pending reads and ignores late responses on navigation', async () => {
    let complete!: (value: [number, unknown]) => void
    mock.onGet('/academic/api/departments/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
    const view = render(<TestPage key="departments" resource="departments" logout={logout} />)
    await waitFor(() => expect(mock.history.get).toHaveLength(1))
    view.rerender(<TestPage key="lecturers" resource="lecturers" logout={logout} />)
    expect(mock.history.get[0].signal?.aborted).toBe(true)
    await act(async () => complete([401, {}]))
    expect(logout).not.toHaveBeenCalled()
  })

  it.each(cases)('opens and dismisses the $resource popup with focus management', async ({ resource, id, label }) => {
    await openPage(resource)
    const opener = screen.getByRole('button', { name: /^Thêm / })
    opener.focus()
    fireEvent.click(opener)
    const dialog = screen.getByRole('dialog')
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(screen.getByLabelText(label, { exact: false })).toHaveFocus()
    expect(document.body.style.overflow).toBe('hidden')
    expect(document.querySelector('.dash-surface')?.parentElement).toHaveAttribute('inert')
    const close = within(dialog).getByRole('button', { name: 'Đóng popup' })
    const cancel = within(dialog).getByRole('button', { name: 'Hủy' })
    close.focus()
    fireEvent.keyDown(close, { key: 'Tab', shiftKey: true })
    expect(cancel).toHaveFocus()
    fireEvent.keyDown(cancel, { key: 'Tab' })
    expect(close).toHaveFocus()
    fireEvent.keyDown(dialog, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(opener).toHaveFocus()
    expect(document.body.style.overflow).toBe('')
    expect(document.querySelector('.dash-surface')?.parentElement).not.toHaveAttribute('inert')
    fireEvent.click(opener)
    fireEvent.click(screen.getByRole('button', { name: 'Đóng popup' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    const edit = screen.getByRole('button', { name: `Sửa ${id}` })
    edit.focus(); fireEvent.click(edit)
    expect(screen.getByRole('dialog')).toHaveAccessibleName(/^Sửa /)
    expect(screen.getByLabelText(label, { exact: false })).toHaveValue(id)
    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(edit).toHaveFocus()
    expect(mock.history.post).toHaveLength(0)
    expect(mock.history.patch).toHaveLength(0)
  })

  it.each([
    { resource: 'departments' as const, match: 'CÔNG NGHỆ', id: '1', excluded: 'not a department' },
    { resource: 'majors' as const, match: 'PHẦN MỀM', id: '2', excluded: 'Công nghệ thông tin' },
    { resource: 'students' as const, match: '3', id: '3', excluded: '90' },
    { resource: 'lecturers' as const, match: 'gv001', id: 'GV001', excluded: 'Công nghệ thông tin' },
  ])('searches only available code/name fields on $resource after submit', async ({ resource, match, id, excluded }) => {
    await openPage(resource)
    fill('Tìm kiếm', match)
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByRole('cell', { name: id })).toBeVisible()
    fill('Tìm kiếm', excluded)
    expect(screen.getByRole('cell', { name: id })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByText('Không tìm thấy kết quả phù hợp.')).toBeVisible()
    fill('Tìm kiếm', '')
    expect(screen.getByText('Không tìm thấy kết quả phù hợp.')).toBeVisible()
    fireEvent.submit(screen.getByRole('search'))
    expect(screen.getByRole('cell', { name: id })).toBeVisible()
    fill('Tìm kiếm', id)
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.getByRole('cell', { name: id })).toBeVisible()
  })
})

async function openFailed(resource: Resource) {
  render(<TestPage resource={resource} logout={logout} />)
  expect(await screen.findByRole('alert')).toBeVisible()
  expect(screen.getByRole('button', { name: /^Thêm / })).toBeDisabled()
}
