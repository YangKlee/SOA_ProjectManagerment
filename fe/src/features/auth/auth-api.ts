import { apiClient } from '../../services/api-client'
import { ApiError } from '../../services/api-error'
import type { AuthSession, LoginCredentials } from './auth-types'

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === 'string'
}

/** Treat the network DTO as untrusted; never establish a session from partial data. */
function parseSession(data: unknown): AuthSession {
  const invalidResponse = () => new ApiError('Phản hồi đăng nhập không hợp lệ. Vui lòng thử lại sau.', 'unknown')

  if (!isObject(data) || typeof data.access !== 'string' || !data.access.trim()
    || data.token_type !== 'Bearer' || !isObject(data.user)) {
    throw invalidResponse()
  }

  const user = data.user
  if (typeof user.user_id !== 'string' || !user.user_id.trim()
    || !isNullableString(user.first_name) || !isNullableString(user.last_name)) {
    throw invalidResponse()
  }

  if (user.role !== 1 && user.role !== 2 && user.role !== 3) {
    throw new ApiError('Tài khoản chưa được cấp vai trò phù hợp. Vui lòng liên hệ quản trị viên.', 'unknown')
  }

  // Do not retain refresh tokens or fields unrelated to the current frontend.
  return {
    access: data.access,
    user: {
      user_id: user.user_id,
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
    },
  }
}

export async function loginRequest(credentials: LoginCredentials, signal?: AbortSignal): Promise<AuthSession> {
  const response = await apiClient.post<unknown>('/auth/login/', {
    identifier: credentials.identifier.trim(),
    password: credentials.password,
  }, { signal })

  return parseSession(response.data)
}
