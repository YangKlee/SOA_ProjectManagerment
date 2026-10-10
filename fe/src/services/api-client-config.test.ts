import { afterEach, describe, expect, it, vi } from 'vitest'

afterEach(() => {
  vi.unstubAllEnvs()
  vi.resetModules()
})

describe('Axios API base URL', () => {
  it.each([undefined, '', '   ', '/'])('defaults to same-origin / for %s', async (value) => {
    vi.stubEnv('VITE_API_BASE_URL', value)
    vi.resetModules()
    const { API_BASE_URL, apiClient } = await import('./api-client')
    expect(API_BASE_URL).toBe('/')
    expect(apiClient.getUri({ url: '/auth/login/' })).toBe('/auth/login/')
  })

  it('honors an explicit API URL override', async () => {
    vi.stubEnv('VITE_API_BASE_URL', ' https://gateway.example.com ')
    vi.resetModules()
    const { API_BASE_URL, apiClient } = await import('./api-client')
    expect(API_BASE_URL).toBe('https://gateway.example.com')
    expect(apiClient.getUri({ url: '/auth/login/' })).toBe('https://gateway.example.com/auth/login/')
  })
})
