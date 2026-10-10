import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, expect, it } from 'vitest'
import { apiClient, setAccessToken } from '../../services/api-client'
import { AuthProvider } from './AuthProvider'
import { useAuth } from './auth-context'
import { SESSION_TOKEN_KEY } from './session-storage'

const profile = { user_id: 'OLD', first_name: null, last_name: null, role: 1 }
let mock: MockAdapter
beforeEach(() => {
  setAccessToken(null)
  mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  sessionStorage.setItem(SESSION_TOKEN_KEY, 'old-token')
})
afterEach(() => { mock.restore(); setAccessToken(null) })

function Probe() {
  const { user, status, logout, login, retryRestore } = useAuth()
  return <>
    <output data-testid="identity">{user?.user_id ?? 'none'} {status}</output>
    <button onClick={logout}>Logout</button>
    <button onClick={() => void login({ identifier: 'NEW', password: 'secret' }).catch(() => {})}>New login</button>
    <button onClick={() => void retryRestore()}>Retry</button>
  </>
}

it('ignores a late restore after logout and does not restore its Bearer or persistence', async () => {
  let complete!: (value: [number, unknown]) => void
  mock.onGet('/auth/me/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
  mock.onGet('/probe/').reply(200, {})
  render(<AuthProvider><Probe /></AuthProvider>)
  await waitFor(() => expect(mock.history.get).toHaveLength(1))
  fireEvent.click(screen.getByText('Logout'))
  expect(mock.history.get[0].signal?.aborted).toBe(true)
  await act(async () => complete([200, profile]))
  expect(screen.getByTestId('identity')).toHaveTextContent('none ready')
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBeNull()
  await apiClient.get('/probe/')
  expect(mock.history.get.at(-1)?.headers?.Authorization).toBeUndefined()
})

it('allows a new login to supersede pending restoration without stale overwrites', async () => {
  let complete!: (value: [number, unknown]) => void
  mock.onGet('/auth/me/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
  mock.onPost('/auth/login/').reply(200, { access: 'new-token', token_type: 'Bearer', user: { ...profile, user_id: 'NEW', role: 3 } })
  render(<AuthProvider><Probe /></AuthProvider>)
  await waitFor(() => expect(mock.history.get).toHaveLength(1))
  fireEvent.click(screen.getByText('New login'))
  await waitFor(() => expect(screen.getByTestId('identity')).toHaveTextContent('NEW ready'))
  await act(async () => complete([200, profile]))
  expect(screen.getByTestId('identity')).toHaveTextContent('NEW ready')
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBe('new-token')
  expect(mock.history.get[0].signal?.aborted).toBe(true)
})

it('cancels unmounted restoration while keeping the saved token for the next mount', async () => {
  let complete!: (value: [number, unknown]) => void
  mock.onGet('/auth/me/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
  mock.onGet('/probe/').reply(200, {})
  const view = render(<AuthProvider><Probe /></AuthProvider>)
  await waitFor(() => expect(mock.history.get).toHaveLength(1))
  view.unmount()
  expect(mock.history.get[0].signal?.aborted).toBe(true)
  await act(async () => complete([200, profile]))
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBe('old-token')
  await apiClient.get('/probe/')
  expect(mock.history.get.at(-1)?.headers?.Authorization).toBeUndefined()
})

it('does not dispatch duplicate restoration requests while pending', async () => {
  let complete!: (value: [number, unknown]) => void
  mock.onGet('/auth/me/').reply(() => new Promise<[number, unknown]>((resolve) => { complete = resolve }))
  render(<AuthProvider><Probe /></AuthProvider>)
  await waitFor(() => expect(mock.history.get).toHaveLength(1))
  fireEvent.click(screen.getByText('Retry')); fireEvent.click(screen.getByText('Retry'))
  expect(mock.history.get).toHaveLength(1)
  await act(async () => complete([200, profile]))
  expect(screen.getByTestId('identity')).toHaveTextContent('OLD ready')
})
