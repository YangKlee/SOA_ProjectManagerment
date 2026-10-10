export type Role = 1 | 2 | 3

export const ROLE_HOME: Record<Role, string> = {
  1: '/admin',
  2: '/lecture',
  3: '/student',
}

export const ROLE_LABEL: Record<Role, string> = {
  1: 'Quản trị viên',
  2: 'Giảng viên',
  3: 'Sinh viên',
}

/** Only the public identity fields used by the frontend are retained. */
export interface AuthUser {
  user_id: string
  first_name: string | null
  last_name: string | null
  role: Role
}

export interface LoginCredentials {
  identifier: string
  password: string
}

export interface AuthSession {
  access: string
  user: AuthUser
}
