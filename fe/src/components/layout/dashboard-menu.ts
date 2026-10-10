import type { Role } from '../../features/auth/auth-types'

export type IconName = 'home' | 'user' | 'bell' | 'chart' | 'book' | 'calendar' | 'file' | 'check' | 'award' | 'users' | 'menu' | 'close' | 'chevron' | 'logout' | 'arrow'
export interface MenuItem { id: string; label: string; icon: IconName }
export interface MenuGroup { id: string; label: string | null; items: MenuItem[] }
export const HOME_ITEM: MenuItem = { id: 'home', label: 'Tổng quan', icon: 'home' }
export const PROFILE_ITEM: MenuItem = { id: 'profile', label: 'Thông tin cá nhân', icon: 'user' }
export const DASHBOARD_MENU: Record<Role, MenuGroup[]> = {
  1: [
    { id: 'academic', label: 'HỌC VỤ', items: [
      { id: 'faculties', label: 'Quản lý khoa', icon: 'book' },
      { id: 'majors', label: 'Quản lý ngành', icon: 'file' },
      { id: 'students', label: 'Quản lý sinh viên', icon: 'users' },
      { id: 'lecturers', label: 'Quản lý giảng viên', icon: 'user' },
    ] },
    { id: 'topics', label: 'ĐỀ TÀI', items: [
      { id: 'topics', label: 'Quản lý đề tài', icon: 'book' },
      { id: 'registrations', label: 'Quản lý đăng ký', icon: 'check' },
    ] },
  ],
  2: [{ id: 'topics', label: 'ĐỀ TÀI', items: [
    { id: 'topics', label: 'Quản lý đề tài', icon: 'book' },
  ] }],
  3: [{ id: 'registrations', label: null, items: [
    { id: 'registrations', label: 'Đăng ký đề tài', icon: 'check' },
  ] }],
}
