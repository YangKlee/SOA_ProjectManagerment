import { apiClient } from '../../services/api-client'
import { ApiError } from '../../services/api-error'
import type { AuthSession, AuthUser, LoginCredentials } from './auth-types'

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === 'string'
}

function parseUser(user: unknown, message: string): AuthUser {
  if (!isObject(user) || typeof user.user_id !== 'string' || !user.user_id.trim()
    || !isNullableString(user.first_name) || !isNullableString(user.last_name)) {
    throw new ApiError(message, 'unknown')
  }

  if (user.role !== 1 && user.role !== 2 && user.role !== 3) {
    throw new ApiError('Tài khoản chưa được cấp vai trò phù hợp. Vui lòng liên hệ quản trị viên.', 'unknown')
  }

  return { user_id: user.user_id, first_name: user.first_name, last_name: user.last_name, role: user.role }
}

/** Treat the network DTO as untrusted; retain only safe identity fields. */
function parseSession(data: unknown): AuthSession {
  const message = 'Phản hồi đăng nhập không hợp lệ. Vui lòng thử lại sau.'
  if (!isObject(data) || typeof data.access !== 'string' || !data.access.trim()
    || data.token_type !== 'Bearer') throw new ApiError(message, 'unknown')
  return { access: data.access, user: parseUser(data.user, message) }
}

export async function currentUserRequest(signal?: AbortSignal): Promise<AuthUser> {
  const response = await apiClient.get<unknown>('/auth/me/', { signal })
  return parseUser(response.data, 'Phản hồi xác thực phiên không hợp lệ. Vui lòng đăng nhập lại.')
}

export async function loginRequest(credentials: LoginCredentials, signal?: AbortSignal): Promise<AuthSession> {
  const response = await apiClient.post<unknown>('/auth/login/', {
    identifier: credentials.identifier.trim(),
    password: credentials.password,
  }, { signal })

  return parseSession(response.data)
}
