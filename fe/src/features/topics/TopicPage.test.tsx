import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient, setAccessToken } from '../../services/api-client'
import { AuthContext } from '../auth/auth-context'
import type { Role } from '../auth/auth-types'
import { TopicPage } from './TopicPage'

const base = '/topics/api/v1/topics/'
const guid = '68317f4b-7445-45bf-8cbb-0c3ba05c5a50'
const rows = [
  { topic_id: 'DT001', name: 'Quản lý đồ án', description: 'SOA', avisor_name: 'An Nguyễn', major_name: 'Phần mềm' },
  { topic_id: 'DT002', name: 'Hệ thống thư viện', description: null, avisor_name: null, major_name: null },
]
const lecturer = { lecturer_id: 'GV001', department_id: '1', user: { first_name: 'An', last_name: 'Nguyễn' } }
const logout = vi.fn()
let mock: MockAdapter
beforeEach(() => {
  logout.mockReset(); setAccessToken('test-token')
  vi.spyOn(crypto, 'randomUUID').mockReturnValue(guid)
  mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  mock.onGet(base).reply(200, rows)
  mock.onGet('/academic/api/majors/').reply(200, [
    { major_id: '2', name: 'Phần mềm', department_id: '1' },
    { major_id: 'CNTT', name: 'Mã chữ', department_id: '1' },
  ])
  mock.onGet('/academic/api/v1/lecturers/').reply(200, [lecturer, { lecturer_id: 'GV002', department_id: null, user: null }])
})
afterEach(() => { mock.restore(); setAccessToken(null); vi.restoreAllMocks() })
function renderPage(role: Role = 1) {
  return render(<AuthContext.Provider value={{ user: { user_id: 'test-user', first_name: null, last_name: null, role }, logout, login: vi.fn(), status: 'ready', restoreError: '', retryRestore: vi.fn() }}><TopicPage /></AuthContext.Provider>)
}
async function openForm() {
  const opener = screen.getByRole('button', { name: 'Tạo đề tài' })
  opener.focus(); fireEvent.click(opener)
  await waitFor(() => expect(within(screen.getByRole('dialog')).getByRole('button', { name: 'Tạo đề tài' })).toBeEnabled())
  return screen.getByRole('form', { name: 'Tạo đề tài' })
}
function fillForm() {
  fireEvent.change(screen.getByLabelText('Tên đề tài'), { target: { value: '  Đề tài mới  ' } })
  fireEvent.change(screen.getByLabelText('Mô tả đề tài'), { target: { value: 'Mô tả SOA' } })
  fireEvent.change(screen.getByLabelText('Giáo viên hướng dẫn'), { target: { value: 'GV001' } })
  fireEvent.change(screen.getByLabelText('Ngành', { exact: true }), { target: { value: '2' } })
}

describe('Topic list and creation', () => {
  it('shows exactly four business columns and nullable names', async () => {
    renderPage()
    const table = await screen.findByRole('table', { name: 'Danh sách đề tài' })
    expect(within(table).getAllByRole('columnheader').map(cell => cell.textContent)).toEqual(['Mã đề tài', 'Tên đề tài', 'Giáo viên hướng dẫn', 'Tên ngành'])
    expect(within(table).getByText('An Nguyễn')).toBeVisible()
    expect(within(table).getByText('Phần mềm')).toBeVisible()
    expect(within(table).getAllByText('—')).toHaveLength(2)
    expect(mock.history.get.map(request => request.url)).toEqual([base])
  })
  it('searches by code or name only when Search is submitted', async () => {
    renderPage(); await screen.findByRole('table')
    const input = screen.getByRole('searchbox')
    fireEvent.change(input, { target: { value: '  dt001  ' } })
    expect(screen.getByText('DT002')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Search' }))
    expect(screen.queryByText('DT002')).not.toBeInTheDocument()
    fireEvent.change(input, { target: { value: 'THƯ VIỆN' } })
    expect(screen.getByText('DT001')).toBeVisible()
    fireEvent.submit(screen.getByRole('search'))
    expect(screen.getByText('DT002')).toBeVisible()
    expect(screen.queryByText('DT001')).not.toBeInTheDocument()
    fireEvent.change(input, { target: { value: 'no match' } }); fireEvent.submit(screen.getByRole('search'))
    expect(screen.getByText('Không có đề tài phù hợp.')).toBeVisible()
    expect(mock.history.get).toHaveLength(1)
  })
  it('creates a GUID topic with selected reference IDs and refreshes the list', async () => {
    renderPage(); await screen.findByRole('table')
    const form = await openForm()
    expect(screen.getByLabelText('Tên đề tài')).toHaveFocus()
    expect(screen.getByRole('option', { name: 'An Nguyễn (GV001)' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'GV002' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: /Mã chữ/ })).toBeDisabled()
    expect(screen.queryByRole('textbox', { name: 'Mã đề tài' })).not.toBeInTheDocument()
    fillForm()
    mock.onPost(base).reply(201, { ...rows[0], topic_id: guid })
    mock.onGet(base).reply(200, [...rows, { ...rows[0], topic_id: guid, name: 'Đề tài mới' }])
    fireEvent.submit(form)
    expect(await screen.findByText('Đã tạo đề tài.')).toBeVisible()
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(await screen.findByText(guid)).toBeVisible()
    expect(JSON.parse(mock.history.post[0].data)).toEqual({ topic_id: guid, name: 'Đề tài mới', description: 'Mô tả SOA', advisor_id: 'GV001', major_id: '2' })
    expect(mock.history.post[0].headers?.Authorization).toBe('Bearer test-token')
    expect(crypto.randomUUID).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: 'Tạo đề tài' })).toHaveFocus()
  })
  it('validates missing name and references before any POST', async () => {
    renderPage(); const form = await openForm()
    fireEvent.submit(form)
    expect(await screen.findByText('Vui lòng nhập tên đề tài.')).toBeVisible()
    expect(screen.getByText('Vui lòng chọn giáo viên hướng dẫn.')).toBeVisible()
    expect(screen.getByText('Vui lòng chọn ngành có mã số hợp lệ.')).toBeVisible()
    expect(screen.getByLabelText('Tên đề tài')).toHaveFocus()
    expect(mock.history.post).toHaveLength(0)
  })
  it('prevents duplicate submit and closing while a write is pending', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onPost(base).reply(() => new Promise<[number, unknown]>(resolve => { complete = resolve }))
    renderPage(); const form = await openForm(); fillForm()
    fireEvent.submit(form); fireEvent.submit(form)
    await waitFor(() => expect(mock.history.post).toHaveLength(1))
    expect(screen.getByRole('button', { name: 'Đang lưu…' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Hủy' })).toBeDisabled()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.getByRole('dialog')).toBeVisible()
    await act(async () => complete([201, rows[0]]))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })
  it.each([400, 403])('retains the form and GUID after HTTP %s without automatic retry', async status => {
    mock.onPost(base).reply(status, { name: ['invalid'], detail: 'private details' })
    renderPage(); const form = await openForm(); fillForm(); fireEvent.submit(form)
    expect(await screen.findByRole('alert')).toBeVisible()
    expect(screen.getByLabelText('Tên đề tài')).toHaveValue('  Đề tài mới  ')
    expect(screen.queryByText('private details')).not.toBeInTheDocument()
    expect(mock.history.post).toHaveLength(1)
    mock.onPost(base).reply(201, rows[0]); fireEvent.submit(form)
    await waitFor(() => expect(mock.history.post).toHaveLength(2))
    expect(JSON.parse(mock.history.post[1].data).topic_id).toBe(guid)
    expect(crypto.randomUUID).toHaveBeenCalledTimes(1)
  })
  it.each(['network', 'timeout', 409, 503] as const)('checks an ambiguous %s result before allowing another create', async failure => {
    const handler = mock.onPost(base)
    if (failure === 'network') handler.networkError()
    else if (failure === 'timeout') handler.timeout()
    else handler.reply(failure)
    renderPage(); const form = await openForm(); fillForm(); fireEvent.submit(form)
    const check = await screen.findByRole('button', { name: 'Kiểm tra kết quả' })
    expect(screen.getByLabelText('Tên đề tài')).toBeDisabled()
    fireEvent.submit(form)
    expect(mock.history.post).toHaveLength(1)
    mock.onGet(`${base}${guid}/`).reply(200, { ...rows[0], topic_id: guid })
    fireEvent.click(check)
    expect(await screen.findByText('Đã tạo đề tài.')).toBeVisible()
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(mock.history.post).toHaveLength(1)
  })
  it('allows explicit retry with the same GUID only after a result check returns 404', async () => {
    mock.onPost(base).timeout()
    renderPage(); const form = await openForm(); fillForm(); fireEvent.submit(form)
    mock.onGet(`${base}${guid}/`).reply(404)
    fireEvent.click(await screen.findByRole('button', { name: 'Kiểm tra kết quả' }))
    expect(await screen.findByText(/Chưa tìm thấy đề tài với mã này/)).toBeVisible()
    expect(screen.getByLabelText('Tên đề tài')).toBeEnabled()
    mock.onPost(base).reply(201, rows[0]); fireEvent.submit(form)
    await waitFor(() => expect(mock.history.post).toHaveLength(2))
    expect(JSON.parse(mock.history.post[1].data).topic_id).toBe(guid)
  })
  it('keeps an uncertain draft blocked when result checking also fails', async () => {
    mock.onPost(base).networkError()
    renderPage(); const form = await openForm(); fillForm(); fireEvent.submit(form)
    mock.onGet(`${base}${guid}/`).reply(503)
    fireEvent.click(await screen.findByRole('button', { name: 'Kiểm tra kết quả' }))
    expect(await screen.findByText(/Dịch vụ tạm thời/)).toBeVisible()
    expect(screen.getByLabelText('Tên đề tài')).toBeDisabled()
    expect(mock.history.post).toHaveLength(1)
  })
  it('keeps a successful write successful if refreshing the list fails', async () => {
    renderPage(); await screen.findByRole('table')
    const form = await openForm(); fillForm()
    mock.onPost(base).reply(201, rows[0]); mock.onGet(base).reply(503)
    fireEvent.submit(form)
    expect(await screen.findByText('Đã tạo đề tài.')).toBeVisible()
    expect(await screen.findByRole('alert')).toHaveTextContent('Dịch vụ tạm thời')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(mock.history.post).toHaveLength(1)
  })
  it.each(['list', 'options', 'create'] as const)('logs out on 401 from %s', async source => {
    if (source === 'list') mock.onGet(base).reply(401)
    if (source === 'options') mock.onGet('/academic/api/v1/lecturers/').reply(401)
    if (source === 'create') mock.onPost(base).reply(401)
    renderPage()
    if (source === 'options') fireEvent.click(screen.getByRole('button', { name: 'Tạo đề tài' }))
    if (source === 'create') { const form = await openForm(); fillForm(); fireEvent.submit(form) }
    await waitFor(() => expect(logout).toHaveBeenCalledOnce())
  })
  it.each(['network', 503] as const)('offers list retry after %s', async failure => {
    if (failure === 'network') mock.onGet(base).networkError()
    else mock.onGet(base).reply(failure)
    renderPage(); expect(await screen.findByRole('alert')).toBeVisible()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    mock.onGet(base).reply(200, rows)
    fireEvent.click(screen.getByRole('button', { name: 'Tải lại' }))
    expect(await screen.findByRole('table')).toBeVisible()
  })
  it('disables creation until reference options load and offers retry', async () => {
    mock.onGet('/academic/api/majors/').reply(503)
    renderPage(); fireEvent.click(screen.getByRole('button', { name: 'Tạo đề tài' }))
    expect(await screen.findByRole('button', { name: 'Tải lại lựa chọn' })).toBeVisible()
    expect(within(screen.getByRole('dialog')).getByRole('button', { name: 'Tạo đề tài' })).toBeDisabled()
    fireEvent.change(screen.getByLabelText('Tên đề tài'), { target: { value: 'Giữ bản nháp' } })
    mock.onGet('/academic/api/majors/').reply(200, [{ major_id: '2', name: 'Phần mềm' }])
    fireEvent.click(screen.getByRole('button', { name: 'Tải lại lựa chọn' }))
    await waitFor(() => expect(screen.getByLabelText('Ngành', { exact: true })).toBeEnabled())
    expect(screen.getByLabelText('Tên đề tài')).toHaveValue('Giữ bản nháp')
  })
  it('shows missing reference choices without sending a write', async () => {
    mock.onGet('/academic/api/majors/').reply(200, [])
    renderPage(); const form = await openForm(); fireEvent.submit(form)
    expect(screen.getByText(/Chưa có giảng viên hoặc ngành/)).toBeVisible()
    expect(mock.history.post).toHaveLength(0)
  })
  it('renders a searchable read-only list for lecturers without reference requests', async () => {
    renderPage(2); await screen.findByRole('table')
    expect(screen.queryByRole('button', { name: 'Tạo đề tài' })).not.toBeInTheDocument()
    expect(mock.history.get.map(request => request.url)).toEqual([base])
  })
  it('aborts pending reference requests when the popup closes', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onGet('/academic/api/majors/').reply(() => new Promise<[number, unknown]>(resolve => { complete = resolve }))
    renderPage(); fireEvent.click(screen.getByRole('button', { name: 'Tạo đề tài' }))
    await waitFor(() => expect(mock.history.get.some(request => request.url === '/academic/api/majors/')).toBe(true))
    const request = mock.history.get.find(request => request.url === '/academic/api/majors/')!
    fireEvent.click(screen.getByRole('button', { name: 'Hủy' }))
    expect(request.signal?.aborted).toBe(true)
    await act(async () => complete([401, {}]))
    expect(logout).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })
  it('aborts a pending POST on unmount and ignores a late 401', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onPost(base).reply(() => new Promise<[number, unknown]>(resolve => { complete = resolve }))
    const view = renderPage(); const form = await openForm(); fillForm(); fireEvent.submit(form)
    await waitFor(() => expect(mock.history.post).toHaveLength(1))
    view.unmount()
    expect(mock.history.post[0].signal?.aborted).toBe(true)
    await act(async () => complete([401, {}]))
    expect(logout).not.toHaveBeenCalled()
  })
  it('aborts pending list loading on unmount', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onGet(base).reply(() => new Promise<[number, unknown]>(resolve => { complete = resolve }))
    const view = renderPage()
    await waitFor(() => expect(mock.history.get).toHaveLength(1))
    view.unmount(); expect(mock.history.get[0].signal?.aborted).toBe(true)
    await act(async () => complete([401, {}]))
    expect(logout).not.toHaveBeenCalled()
  })
  it('closes on Escape and restores focus to the opener', async () => {
    renderPage(); await openForm()
    fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tạo đề tài' })).toHaveFocus()
  })

  it('shows safe feedback if GUID generation is unavailable', async () => {
    vi.mocked(crypto.randomUUID).mockImplementation(() => { throw new Error('insecure context') })
    renderPage(); await screen.findByRole('table')
    fireEvent.click(screen.getByRole('button', { name: 'Tạo đề tài' }))
    expect(screen.getByRole('alert')).toHaveTextContent('HTTPS hoặc localhost')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(mock.history.post).toHaveLength(0)
  })

  it('shows a permission error for forbidden topic reads without logging out', async () => {
    mock.onGet(base).reply(403, { detail: 'private data' })
    renderPage(2)
    expect(await screen.findByRole('alert')).toHaveTextContent('Bạn không có quyền')
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
    expect(screen.queryByText('private data')).not.toBeInTheDocument()
    expect(logout).not.toHaveBeenCalled()
  })
})
