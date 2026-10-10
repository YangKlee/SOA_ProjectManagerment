import axios from 'axios'
import { normalizeApiError } from './api-error'

const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()

// Development uses Vite's Gateway proxy; production needs same-origin API routing.
export const API_BASE_URL = configuredBaseUrl || '/'
export const API_TIMEOUT_MS = 10_000

let accessToken: string | null = null

/** In-memory request token; AuthProvider handles tab persistence and restoration. */
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
