import axios from 'axios'

export type ApiErrorKind = 'http' | 'network' | 'timeout' | 'cancelled' | 'unknown'

/** Consistent failure shape; response data is available for field-level validation. */
export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | undefined
  readonly details: unknown

  constructor(message: string, kind: ApiErrorKind, status?: number, details?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
    this.details = details
  }
}

export function normalizeApiError(error: unknown): ApiError {
  if (error instanceof ApiError) return error
  if (axios.isCancel(error)) return new ApiError('Yêu cầu đã được hủy.', 'cancelled')

  if (axios.isAxiosError(error)) {
    if (error.code === 'ECONNABORTED' || error.code === 'ETIMEDOUT') {
      return new ApiError('Yêu cầu quá thời gian chờ. Vui lòng thử lại.', 'timeout')
    }

    if (error.response) {
      const messages: Record<number, string> = {
        400: 'Dữ liệu gửi lên không hợp lệ.',
        401: 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn.',
        403: 'Bạn không có quyền thực hiện thao tác này.',
        404: 'Không tìm thấy dữ liệu yêu cầu.',
        422: 'Dữ liệu gửi lên không hợp lệ.',
        429: 'Có quá nhiều yêu cầu. Vui lòng thử lại sau.',
      }

      return new ApiError(
        messages[error.response.status] ?? 'Không thể xử lý yêu cầu. Vui lòng thử lại sau.',
        'http',
        error.response.status,
        error.response.data,
      )
    }

    return new ApiError('Không thể kết nối đến máy chủ. Vui lòng kiểm tra mạng.', 'network')
  }

  return new ApiError('Đã xảy ra lỗi không mong muốn.', 'unknown')
}
