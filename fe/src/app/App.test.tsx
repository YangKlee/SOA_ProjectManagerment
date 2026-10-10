import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { Link, MemoryRouter, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { AuthProvider } from '../features/auth/AuthProvider'
import { apiClient, setAccessToken } from '../services/api-client'
import { App } from './App'

function RouteProbe() {
  const location = useLocation()
  return (
    <>
      <output data-testid="path">{location.pathname}</output>
      {['/login', '/admin', '/lecture', '/student', '/', '/missing'].map((path) => (
        <Link key={path} to={path}>Go {path}</Link>
      ))}
    </>
  )
}

function renderApp(path = '/login') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AuthProvider>
        <App />
        <RouteProbe />
      </AuthProvider>
    </MemoryRouter>,
  )
}

function fillForm(identifier = 'SV001', password = 'secret') {
  fireEvent.change(screen.getByLabelText('MSSV/UserID'), { target: { value: identifier } })
  fireEvent.change(screen.getByLabelText('Mật khẩu', { exact: true }), { target: { value: password } })
}

function submitForm() {
  fireEvent.submit(screen.getByRole('form', { name: 'Đăng nhập' }))
}

function responseForRole(role: number) {
  return {
    access: 'access-test-token', refresh: 'refresh-test-token', token_type: 'Bearer',
    user: { user_id: 'SV001', first_name: 'An', last_name: 'Nguyễn', role },
  }
}

const roles = [
  { role: 1, path: '/admin', title: 'Quản trị viên' },
  { role: 2, path: '/lecture', title: 'Giảng viên' },
  { role: 3, path: '/student', title: 'Sinh viên' },
]

describe('Login and role routes', () => {
  let mock: MockAdapter
  beforeEach(() => {
    setAccessToken(null)
    mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  })
  afterEach(() => {
    mock.restore()
    setAccessToken(null)
  })

  it('renders labeled credentials with password autocomplete and visibility control', () => {
    renderApp()
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeVisible()
    expect(screen.getByLabelText('MSSV/UserID')).toHaveAttribute('autocomplete', 'username')
    const password = screen.getByLabelText('Mật khẩu', { exact: true })
    expect(password).toHaveAttribute('type', 'password')
    expect(password).toHaveAttribute('autocomplete', 'current-password')
    fireEvent.click(screen.getByRole('button', { name: 'Hiện mật khẩu' }))
    expect(password).toHaveAttribute('type', 'text')
    fireEvent.click(screen.getByRole('button', { name: 'Ẩn mật khẩu' }))
    expect(password).toHaveAttribute('type', 'password')
  })

  it('validates empty fields and focuses the identifier without making a request', () => {
    renderApp()
    fillForm('   ', '')
    submitForm()
    expect(screen.getByText('Vui lòng nhập MSSV/UserID.')).toBeVisible()
    expect(screen.getByText('Vui lòng nhập mật khẩu.')).toBeVisible()
    expect(screen.getByLabelText('MSSV/UserID')).toHaveFocus()
    expect(mock.history.post).toHaveLength(0)
  })

  it('validates an empty password independently', () => {
    renderApp()
    fillForm('SV001', '')
    submitForm()
    expect(screen.getByLabelText('Mật khẩu', { exact: true })).toHaveFocus()
    expect(screen.getByLabelText('Mật khẩu', { exact: true })).toHaveAttribute('aria-invalid', 'true')
    expect(mock.history.post).toHaveLength(0)
  })

  it.each(roles)('routes role $role to $path and attaches its token to subsequent API requests', async ({ role, path, title }) => {
    mock.onPost('/auth/login/').reply(200, responseForRole(role))
    mock.onGet('/auth/me/').reply(200, {})
    renderApp()
    fillForm('  SV001  ', ' secret ')
    submitForm()
    expect(await screen.findByRole('heading', { name: title })).toBeVisible()
    expect(screen.getByRole('navigation', { name: 'Chức năng' })).toBeVisible()
    expect(screen.getByRole('button', { name: 'Tổng quan' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByTestId('path')).toHaveTextContent(path)
    expect(JSON.parse(mock.history.post[0].data as string)).toEqual({ identifier: 'SV001', password: ' secret ' })
    expect(mock.history.post).toHaveLength(1)
    await apiClient.get('/auth/me/')
    expect(mock.history.get[0].headers?.Authorization).toBe('Bearer access-test-token')
    expect(localStorage.getItem('access')).toBeNull()
    expect(sessionStorage.getItem('access')).toBeNull()
  })

  it('locks submission while pending and submits only once', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onPost('/auth/login/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
    renderApp()
    fillForm()
    submitForm()
    submitForm()
    expect(screen.getByRole('button', { name: 'Đang đăng nhập…' })).toBeDisabled()
    expect(screen.getByLabelText('MSSV/UserID')).toBeDisabled()
    await waitFor(() => expect(mock.history.post).toHaveLength(1))
    await act(async () => complete([200, responseForRole(3)]))
    expect(await screen.findByRole('heading', { name: 'Sinh viên' })).toBeVisible()
  })

  it.each([
    { status: 401, message: 'MSSV/UserID hoặc mật khẩu không đúng.' },
    { status: 400, message: 'Thông tin đăng nhập không hợp lệ. Vui lòng kiểm tra lại.' },
    { status: 403, message: 'Bạn không có quyền thực hiện thao tác này.' },
    { status: 500, message: 'Không thể xử lý yêu cầu. Vui lòng thử lại sau.' },
  ])('shows safe feedback for HTTP $status and leaves the user unauthenticated', async ({ status, message }) => {
    mock.onPost('/auth/login/').reply(status, { detail: 'private server details' })
    mock.onGet('/probe/').reply(200, {})
    renderApp()
    fillForm()
    submitForm()
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(screen.getByRole('button', { name: 'Đăng nhập' })).toBeEnabled()
    expect(screen.getByTestId('path')).toHaveTextContent('/login')
    await apiClient.get('/probe/')
    expect(mock.history.get[0].headers?.Authorization).toBeUndefined()
  })

  it.each(['network', 'timeout'])('shows a retryable error on %s failure', async (kind) => {
    const handler = mock.onPost('/auth/login/')
    if (kind === 'network') handler.networkError()
    else handler.timeout()
    renderApp()
    fillForm()
    submitForm()
    expect(await screen.findByRole('alert')).toHaveTextContent(kind === 'network' ? 'Không thể kết nối' : 'quá thời gian chờ')
    expect(screen.getByTestId('path')).toHaveTextContent('/login')
  })

  it.each([
    { data: responseForRole(8), message: 'Tài khoản chưa được cấp vai trò phù hợp.' },
    { data: { ...responseForRole(1), access: null }, message: 'Phản hồi đăng nhập không hợp lệ.' },
  ])('does not grant a session for invalid successful responses %#', async ({ data, message }) => {
    mock.onPost('/auth/login/').reply(200, data)
    mock.onGet('/probe/').reply(200, {})
    renderApp()
    fillForm()
    submitForm()
    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    fireEvent.click(screen.getByRole('link', { name: 'Go /admin' }))
    await waitFor(() => expect(screen.getByTestId('path')).toHaveTextContent('/login'))
    await apiClient.get('/probe/')
    expect(mock.history.get[0].headers?.Authorization).toBeUndefined()
  })

  it.each(['/admin', '/lecture', '/student', '/', '/missing'])('redirects an unauthenticated visit to %s back to login', async (path) => {
    renderApp(path)
    expect(await screen.findByRole('heading', { name: 'Đăng nhập' })).toBeVisible()
    expect(screen.getByTestId('path')).toHaveTextContent('/login')
    expect(mock.history.get).toHaveLength(0)
  })

  it.each(roles)('keeps authenticated role $role on its own home when navigating to other roles/login', async ({ role, path }) => {
    mock.onPost('/auth/login/').reply(200, responseForRole(role))
    renderApp()
    fillForm()
    submitForm()
    await waitFor(() => expect(screen.getByTestId('path')).toHaveTextContent(path))
    for (const target of ['/login', '/admin', '/lecture', '/student', '/', '/missing']) {
      fireEvent.click(screen.getByRole('link', { name: `Go ${target}` }))
      await waitFor(() => expect(screen.getByTestId('path').textContent).toBe(path))
    }
  })

  it('clears user and Bearer token on logout and protects the previous home', async () => {
    mock.onPost('/auth/login/').reply(200, responseForRole(3))
    mock.onGet('/probe/').reply(200, {})
    renderApp()
    fillForm()
    submitForm()
    fireEvent.click(await screen.findByRole('button', { name: 'Đăng xuất' }))
    expect(await screen.findByRole('heading', { name: 'Đăng nhập' })).toBeVisible()
    await apiClient.get('/probe/')
    expect(mock.history.get[0].headers?.Authorization).toBeUndefined()
    fireEvent.click(screen.getByRole('link', { name: 'Go /student' }))
    await waitFor(() => expect(screen.getByTestId('path')).toHaveTextContent('/login'))
  })

  it('cancels login if the form is unmounted before a response arrives', async () => {
    let complete!: (response: [number, unknown]) => void
    mock.onPost('/auth/login/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
    mock.onGet('/probe/').reply(200, {})
    renderApp()
    fillForm()
    submitForm()
    await waitFor(() => expect(mock.history.post).toHaveLength(1))
    fireEvent.click(screen.getByRole('link', { name: 'Go /admin' }))
    await act(async () => complete([200, responseForRole(1)]))
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeVisible()
    expect(screen.getByTestId('path')).toHaveTextContent('/login')
    await apiClient.get('/probe/')
    expect(mock.history.get[0].headers?.Authorization).toBeUndefined()
  })
})

