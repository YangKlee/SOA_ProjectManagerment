import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { ROLE_HOME } from '../../features/auth/auth-types'
import { dashboardItems, HOME_ITEM } from './dashboard-menu'
import { DashboardHomePage } from '../../app/DashboardHomePage'
import { DashboardPlaceholderPage } from '../../app/DashboardPlaceholderPage'
import { DepartmentPage } from '../../features/academic/pages/DepartmentPage'
import type { AuthUser } from '../../features/auth/auth-types'
import { MainLayout } from './MainLayout'

vi.mock('../../features/academic/pages/DepartmentPage', () => ({ DepartmentPage: () => <section aria-label="Academic departments" /> }))
vi.mock('../../features/academic/pages/MajorPage', () => ({ MajorPage: () => <section aria-label="Academic majors" /> }))
vi.mock('../../features/academic/pages/StudentPage', () => ({ StudentPage: () => <section aria-label="Academic students" /> }))
vi.mock('../../features/academic/pages/LecturerPage', () => ({ LecturerPage: () => <section aria-label="Academic lecturers" /> }))

const user: AuthUser = { user_id: 'SV001', first_name: 'An', last_name: 'Nguyễn', role: 3 }
function renderLayout(overrides: Partial<AuthUser> = {}) {
  const logout = vi.fn()
  const currentUser = { ...user, ...overrides }
  const result = render(<MemoryRouter initialEntries={[ROLE_HOME[currentUser.role]]}>
    <Routes><Route path={ROLE_HOME[currentUser.role]} element={<MainLayout user={currentUser} logout={logout} />}>
      <Route index element={<DashboardHomePage />} />
      {dashboardItems(currentUser.role).filter(item => item !== HOME_ITEM).map(item =>
        <Route key={item.id} path={item.path} element={item.id === 'faculties' ? <DepartmentPage logout={logout} /> : <DashboardPlaceholderPage />} />)}
    </Route></Routes>
  </MemoryRouter>)
  return { ...result, logout }
}
function mockMobile() {
  let change: (() => void) | undefined
  const media = { matches: true, addEventListener: vi.fn((_event: string, listener: () => void) => { change = listener }), removeEventListener: vi.fn() }
  vi.stubGlobal('matchMedia', vi.fn(() => media))
  return { media, resize: (matches: boolean) => act(() => { media.matches = matches; change?.() }) }
}
afterEach(() => { vi.unstubAllGlobals() })

describe('Shared dashboard layout', () => {
  it.each([
    { role: 1 as const, title: 'Quản trị viên', buttons: ['Tổng quan', 'HỌC VỤ', 'Quản lý khoa', 'Quản lý ngành', 'Quản lý sinh viên', 'Quản lý giảng viên', 'ĐỀ TÀI', 'Quản lý đề tài', 'Quản lý đăng ký'], shortcuts: ['Mở Quản lý khoa', 'Mở Quản lý ngành', 'Mở Quản lý sinh viên'] },
    { role: 2 as const, title: 'Giảng viên', buttons: ['Tổng quan', 'ĐỀ TÀI', 'Quản lý đề tài'], shortcuts: ['Mở Quản lý đề tài'] },
    { role: 3 as const, title: 'Sinh viên', buttons: ['Tổng quan', 'Đăng ký đề tài'], shortcuts: ['Mở Đăng ký đề tài'] },
  ])('renders identity and the exact menu belonging to $title', ({ role, title, buttons, shortcuts }) => {
    renderLayout({ role })
    expect(screen.getByRole('heading', { name: title, level: 1 })).toBeVisible()
    expect(screen.getByRole('heading', { name: 'Xin chào, An Nguyễn!' })).toBeVisible()
    expect(screen.getByRole('img', { name: 'Logo Trường Đại học Quy Nhơn' })).toHaveAttribute('src', '/img/logo.png')
    const nav = screen.getByRole('navigation', { name: 'Chức năng' })
    expect(Array.from(nav.querySelectorAll('a, button')).map((button) => button.textContent)).toEqual(buttons)
    const quickAccess = screen.getByRole('region', { name: 'Truy cập nhanh' })
    expect(within(quickAccess).getAllByRole('link').map((button) => button.getAttribute('aria-label'))).toEqual(shortcuts)
    expect(within(screen.getByRole('complementary', { name: 'Menu điều hướng' })).getByText(`${title} · SV001`)).toBeVisible()
    expect(screen.queryByText('Nguyễn Khánh Dương')).not.toBeInTheDocument()
    fireEvent.click(within(quickAccess).getByRole('link', { name: shortcuts[0] }))
    expect(screen.getByRole('heading', { name: shortcuts[0].replace('Mở ', ''), level: 1 })).toBeVisible()
    if (role === 1) expect(screen.getByRole('region', { name: 'Academic departments' })).toBeVisible()
    else expect(screen.getByText('Đang phát triển')).toBeVisible()
  })

  it.each([1, 2, 3] as const)('opens the profile independently of role %s business menu order', (role) => {
    renderLayout({ role })
    fireEvent.click(screen.getByRole('link', { name: 'Thông tin của tôi' }))
    expect(screen.getByRole('heading', { name: 'Thông tin cá nhân', level: 1 })).toBeVisible()
    fireEvent.click(screen.getByRole('link', { name: 'Về tổng quan' }))
    fireEvent.click(screen.getByRole('button', { name: 'Tài khoản' }))
    fireEvent.click(screen.getByRole('link', { name: 'Xem thông tin cá nhân' }))
    expect(screen.getByRole('heading', { name: 'Thông tin cá nhân', level: 1 })).toBeVisible()
    expect(screen.queryByRole('region', { name: 'Tài khoản' })).not.toBeInTheDocument()
    const nav = screen.getByRole('navigation', { name: 'Chức năng' })
    expect(within(nav).queryByRole('button', { name: 'Thông tin cá nhân' })).not.toBeInTheDocument()
  })

  it('falls back to the user ID when the name is unavailable', () => {
    renderLayout({ first_name: null, last_name: null })
    expect(screen.getByRole('heading', { name: 'Xin chào, SV001!' })).toBeVisible()
  })

  it('collapses the desktop sidebar and restores it', () => {
    renderLayout()
    fireEvent.click(screen.getByRole('button', { name: 'Đóng menu' }))
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mở menu' })).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(screen.getByRole('button', { name: 'Mở menu' }))
    expect(screen.getByRole('navigation')).toBeVisible()
  })

  it('collapses groups independently and preserves active selection', () => {
    renderLayout({ role: 1 })
    const group = screen.getByRole('button', { name: 'HỌC VỤ' })
    fireEvent.click(screen.getByRole('link', { name: 'Quản lý khoa' }))
    expect(screen.getByRole('link', { name: 'Quản lý khoa' })).toHaveAttribute('aria-current', 'page')
    expect(screen.getByRole('heading', { name: 'Quản lý khoa', level: 1 })).toBeVisible()
    expect(screen.getByRole('region', { name: 'Academic departments' })).toBeVisible()
    fireEvent.click(group)
    expect(group).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('link', { name: 'Quản lý khoa' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Quản lý đề tài' })).toBeVisible()
    expect(screen.getByRole('button', { name: 'ĐỀ TÀI' })).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(group)
    expect(screen.getByRole('link', { name: 'Quản lý khoa' })).toHaveAttribute('aria-current', 'page')
    fireEvent.click(screen.getByRole('button', { name: 'ĐỀ TÀI' }))
    expect(screen.queryByRole('link', { name: 'Quản lý đề tài' })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Quản lý khoa' })).toBeVisible()
    fireEvent.click(screen.getByRole('link', { name: 'Tổng quan' }))
    expect(screen.getByRole('link', { name: 'Tổng quan' })).toHaveAttribute('aria-current', 'page')
  })

  it('opens shortcuts, notifications and the account panel with dismissal', () => {
    renderLayout()
    fireEvent.click(screen.getByRole('link', { name: 'Mở Đăng ký đề tài' }))
    expect(screen.getByRole('heading', { name: 'Đăng ký đề tài', level: 1 })).toBeVisible()
    expect(screen.getByRole('link', { name: 'Đăng ký đề tài' })).toHaveAttribute('aria-current', 'page')
    fireEvent.click(screen.getByRole('button', { name: 'Thông báo' }))
    expect(screen.getByRole('region', { name: 'Thông báo' })).toBeVisible()
    expect(screen.getByText('Thông báo sẽ hiển thị khi chức năng được triển khai.')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Tài khoản' }))
    expect(screen.queryByRole('region', { name: 'Thông báo' })).not.toBeInTheDocument()
    expect(screen.getByRole('region', { name: 'Tài khoản' })).toBeVisible()
    fireEvent.keyDown(screen.getByRole('button', { name: 'Tài khoản' }), { key: 'Escape' })
    expect(screen.queryByRole('region', { name: 'Tài khoản' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tài khoản' })).toHaveFocus()
    fireEvent.click(screen.getByRole('button', { name: 'Tài khoản' }))
    fireEvent.click(screen.getByRole('link', { name: 'Xem thông tin cá nhân' }))
    expect(screen.getByRole('heading', { name: 'Thông tin cá nhân', level: 1 })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Thông báo' }))
    fireEvent.pointerDown(screen.getByRole('main'))
    expect(screen.queryByRole('region', { name: 'Thông báo' })).not.toBeInTheDocument()
  })

  it('invokes the existing logout action', () => {
    const { logout } = renderLayout()
    fireEvent.click(screen.getByRole('button', { name: 'Đăng xuất' }))
    expect(logout).toHaveBeenCalledOnce()
  })

  it('opens a mobile modal drawer, traps focus, dismisses and restores body scrolling', () => {
    mockMobile()
    const { unmount } = renderLayout()
    const opener = screen.getByRole('button', { name: 'Mở menu' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(opener)
    const drawer = screen.getByRole('dialog', { name: 'Menu điều hướng' })
    const closer = within(drawer).getByRole('button', { name: 'Đóng menu' })
    expect(closer).toHaveFocus()
    expect(document.body.style.overflow).toBe('hidden')
    expect(document.querySelector('.dash-workspace')).toHaveAttribute('inert')
    fireEvent.keyDown(closer, { key: 'Tab', shiftKey: true })
    expect(within(drawer).getByRole('button', { name: 'Đăng xuất' })).toHaveFocus()
    fireEvent.keyDown(document.activeElement!, { key: 'Tab' })
    expect(closer).toHaveFocus()
    fireEvent.keyDown(closer, { key: 'Escape' })
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(opener).toHaveFocus()
    expect(document.body.style.overflow).toBe('')
    fireEvent.click(opener)
    fireEvent.click(screen.getByRole('button', { name: 'Đóng menu điều hướng' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    fireEvent.click(opener)
    fireEvent.click(within(screen.getByRole('dialog')).getByRole('link', { name: 'Đăng ký đề tài' }))
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Đăng ký đề tài', level: 1 })).toBeVisible()
    fireEvent.click(opener)
    unmount()
    expect(document.body.style.overflow).toBe('')
  })

  it('adapts the sidebar when crossing the mobile breakpoint', () => {
    const { resize, media } = mockMobile()
    const { unmount } = renderLayout()
    resize(false)
    expect(screen.getByRole('navigation')).toBeVisible()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
    resize(true)
    expect(screen.queryByRole('navigation')).not.toBeInTheDocument()
    unmount()
    expect(media.removeEventListener).toHaveBeenCalledWith('change', expect.any(Function))
  })
})
