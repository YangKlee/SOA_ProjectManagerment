import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { apiClient, setAccessToken } from '../../services/api-client'
import { currentUserRequest, loginRequest } from './auth-api'

const validResponse = {
  access: 'access-test-token', refresh: 'refresh-test-token', token_type: 'Bearer',
  user: { user_id: 'SV001', first_name: 'An', last_name: 'Nguyễn', role: 3 },
}

describe('Login API contract', () => {
  let mock: MockAdapter
  beforeEach(() => {
    setAccessToken(null)
    mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' })
  })
  afterEach(() => mock.restore())

  it('validates /me identity and discards private or unrelated profile fields', async () => {
    setAccessToken('saved-access')
    mock.onGet('/auth/me/').reply(200, { ...validResponse.user, email: 'private', password: 'private' })
    expect(await currentUserRequest()).toEqual(validResponse.user)
    expect(mock.history.get[0].headers?.Authorization).toBe('Bearer saved-access')
  })

  it.each([null, {}, { ...validResponse.user, role: 9 }, { ...validResponse.user, user_id: '' }])('rejects malformed current-user profile %#', async (data) => {
    mock.onGet('/auth/me/').reply(200, data)
    await expect(currentUserRequest()).rejects.toMatchObject({ kind: 'unknown' })
  })

  it('sends identifier and exact password to the Gateway and retains only safe session data', async () => {
    mock.onPost('/auth/login/').reply(200, validResponse)
    const session = await loginRequest({ identifier: '  SV001  ', password: ' mật khẩu ' })

    expect(JSON.parse(mock.history.post[0].data as string)).toEqual({ identifier: 'SV001', password: ' mật khẩu ' })
    expect(mock.history.post[0].headers?.Authorization).toBeUndefined()
    expect(session).toEqual({ access: validResponse.access, user: validResponse.user })
    expect(session).not.toHaveProperty('refresh')
  })

  it.each([
    null,
    {},
    { ...validResponse, access: '' },
    { ...validResponse, token_type: 'Other' },
    { ...validResponse, user: null },
    { ...validResponse, user: { ...validResponse.user, user_id: '' } },
    { ...validResponse, user: { ...validResponse.user, first_name: 123 } },
  ])('rejects malformed successful response %#', async (data) => {
    mock.onPost('/auth/login/').reply(200, data)
    await expect(loginRequest({ identifier: 'SV001', password: 'test' })).rejects.toMatchObject({ name: 'ApiError', kind: 'unknown' })
  })

  it.each([0, 4, '1', null])('rejects unsupported or incorrectly typed role %s', async (role) => {
    mock.onPost('/auth/login/').reply(200, { ...validResponse, user: { ...validResponse.user, role } })
    await expect(loginRequest({ identifier: 'SV001', password: 'test' })).rejects.toThrow('Tài khoản chưa được cấp vai trò phù hợp.')
  })
})
