import axios from 'axios'
import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { apiClient, API_TIMEOUT_MS, setAccessToken } from './api-client'
import { ApiError, normalizeApiError } from './api-error'

describe('Gateway Axios client', () => {
  let mock: MockAdapter

  beforeEach(() => {
    setAccessToken(null)
    mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  })

  afterEach(() => {
    mock.restore()
    setAccessToken(null)
  })

  it('returns a typed response and uses JSON with a bounded timeout', async () => {
    mock.onGet('/auth/health/').reply(200, { status: 'ok' })

    const response = await apiClient.get<{ status: string }>('/auth/health/')

    expect(response.data.status).toBe('ok')
    expect(response.status).toBe(200)
    expect(mock.history.get[0].timeout).toBe(API_TIMEOUT_MS)
    expect(mock.history.get[0].headers?.Accept).toBe('application/json')
    expect(apiClient.defaults.baseURL).toBeTruthy()
  })

  it('attaches a Bearer token and removes it for later requests after logout', async () => {
    mock.onGet('/auth/me/').reply(200, {})
    setAccessToken('example-test-token')
    await apiClient.get('/auth/me/')
    expect(mock.history.get[0].headers?.Authorization).toBe('Bearer example-test-token')

    setAccessToken(null)
    await apiClient.get('/auth/me/')
    expect(mock.history.get[1].headers?.Authorization).toBeUndefined()
  })

  it('preserves validation details and does not retry a failed write', async () => {
    const details = { title: ['This field is required.'] }
    mock.onPost('/example/').reply(400, details)

    await expect(apiClient.post('/example/', {})).rejects.toMatchObject({
      name: 'ApiError', kind: 'http', status: 400, details,
    })
    expect(mock.history.post).toHaveLength(1)
  })

  it.each([401, 403])('preserves authorization failure %s without retrying', async (status) => {
    mock.onGet('/auth/me/').reply(status)
    await expect(apiClient.get('/auth/me/')).rejects.toMatchObject({ kind: 'http', status })
    expect(mock.history.get).toHaveLength(1)
  })

  it('uses a safe message for server failures while retaining response details', async () => {
    mock.onGet('/example/').reply(500, { detail: 'private implementation detail' })
    await expect(apiClient.get('/example/')).rejects.toMatchObject({
      status: 500,
      message: 'Không thể xử lý yêu cầu. Vui lòng thử lại sau.',
    })
  })

  it('normalizes network failures', async () => {
    mock.onGet('/example/').networkError()
    await expect(apiClient.get('/example/')).rejects.toMatchObject({ kind: 'network', status: undefined })
  })

  it('normalizes timeouts', async () => {
    mock.onGet('/example/').timeout()
    await expect(apiClient.get('/example/')).rejects.toMatchObject({ kind: 'timeout' })
  })

  it('preserves cancellation when a request is aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(apiClient.get('/example/', { signal: controller.signal })).rejects.toMatchObject({ kind: 'cancelled' })
    expect(mock.history.get).toHaveLength(0)
  })

  it('does not expose unexpected exception messages', () => {
    const normalized = normalizeApiError(new Error('sensitive internals'))
    expect(normalized).toBeInstanceOf(ApiError)
    expect(normalized.kind).toBe('unknown')
    expect(normalized.message).not.toContain('sensitive')
    expect(normalizeApiError(normalized)).toBe(normalized)
    expect(normalizeApiError(new axios.CanceledError()).kind).toBe('cancelled')
  })
})
