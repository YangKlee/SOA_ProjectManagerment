import axios from 'axios'
import { normalizeApiError } from './api-error'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

// Production defaults to a same-origin Gateway. localhost is development-only.
export const API_BASE_URL = configuredBaseUrl || (
  import.meta.env.DEV || import.meta.env.MODE === 'test' ? 'http://localhost:8000' : '/'
)
export const API_TIMEOUT_MS = 10_000

let accessToken: string | null = null

/** Set after login; clear on logout. Deliberately not persisted in browser storage. */
export function setAccessToken(token: string | null): void {
  accessToken = token?.trim() || null
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: { Accept: 'application/json' },
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) config.headers.set('Authorization', `Bearer ${accessToken}`)
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: unknown) => Promise.reject(normalizeApiError(error)),
)
