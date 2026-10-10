import { ROLE_HOME } from '../../features/auth/auth-types'
import type { Role } from '../../features/auth/auth-types'

export const QNU_BRANDING = { logo: '/img/logo.png', banner: '/img/banner_QNU.jpg' } as const

export type IconName = 'home' | 'user' | 'bell' | 'chart' | 'book' | 'calendar' | 'file' | 'check' | 'award' | 'users' | 'menu' | 'close' | 'chevron' | 'logout' | 'arrow'
export interface MenuItem { id: string; path: string; label: string; icon: IconName }
export interface MenuGroup { id: string; label: string | null; items: MenuItem[] }
export const HOME_ITEM: MenuItem = { id: 'home', path: '', label: 'Tổng quan', icon: 'home' }
export const PROFILE_ITEM: MenuItem = { id: 'profile', path: 'profile', label: 'Thông tin cá nhân', icon: 'user' }
export const DASHBOARD_MENU: Record<Role, MenuGroup[]> = {
  1: [
    { id: 'academic', label: 'HỌC VỤ', items: [
      { id: 'faculties', path: 'departments', label: 'Quản lý khoa', icon: 'book' },
      { id: 'majors', path: 'majors', label: 'Quản lý ngành', icon: 'file' },
      { id: 'students', path: 'students', label: 'Quản lý sinh viên', icon: 'users' },
      { id: 'lecturers', path: 'lecturers', label: 'Quản lý giảng viên', icon: 'user' },
    ] },
    { id: 'topics', label: 'ĐỀ TÀI', items: [
      { id: 'topics', path: 'topics', label: 'Quản lý đề tài', icon: 'book' },
      { id: 'registrations', path: 'registrations', label: 'Quản lý đăng ký', icon: 'check' },
    ] },
  ],
  2: [{ id: 'topics', label: 'ĐỀ TÀI', items: [
    { id: 'topics', path: 'topics', label: 'Quản lý đề tài', icon: 'book' },
  ] }],
  3: [{ id: 'registrations', label: null, items: [
    { id: 'registrations', path: 'registrations', label: 'Đăng ký đề tài', icon: 'check' },
  ] }],
}

export const NOT_FOUND_ITEM: MenuItem = { id: 'not-found', path: '*', label: 'Không tìm thấy trang', icon: 'file' }
export const dashboardItems = (role: Role) => [HOME_ITEM, PROFILE_ITEM, ...DASHBOARD_MENU[role].flatMap((group) => group.items)]
export const dashboardPath = (role: Role, item: MenuItem) => `${ROLE_HOME[role]}${item.path ? `/${item.path}` : ''}`
export function dashboardItem(role: Role, pathname: string): MenuItem {
  const path = pathname.replace(/\/+$/, '')
  return dashboardItems(role).find((item) => dashboardPath(role, item) === path) ?? NOT_FOUND_ITEM
}

/** Only known routes for the authenticated role may be a login return destination. */
export function allowedReturnPath(value: unknown, role: Role): string {
  if (typeof value !== 'string' || !value.startsWith('/') || value.startsWith('//') ||
      value.includes('\\') || Array.from(value).some((char) => char.charCodeAt(0) < 32 || char.charCodeAt(0) === 127)) return ROLE_HOME[role]
  try {
    const url = new URL(value, 'https://frontend.invalid')
    if (url.origin !== 'https://frontend.invalid' || dashboardItem(role, url.pathname) === NOT_FOUND_ITEM) return ROLE_HOME[role]
    return url.pathname + url.search + url.hash
  } catch { return ROLE_HOME[role] }
}

export const ACADEMIC_PAGE_IDS = ['faculties', 'majors', 'students', 'lecturers'] as const
