# Task: Revise dashboard menus by role

Status: Completed after user approval (`ok`).

## Objective
Replace the dashboard business menus with the exact role structure requested by the user.

## Scope
- Role 1: HỌC VỤ -> Quản lý khoa, Quản lý ngành, Quản lý sinh viên, Quản lý giảng viên; ĐỀ TÀI -> Quản lý đề tài, Quản lý đăng ký.
- Role 2: ĐỀ TÀI -> Quản lý đề tài.
- Role 3: standalone Đăng ký đề tài item, without an extra group heading.
- Remove former personal/messages/student academic/mentoring business entries from the sidebar.
- Preserve shared Tổng quan, profile identity, Đăng xuất and header account/notification controls.
- Adapt quick access cards and profile buttons to the new menus; profile actions must select an explicit profile item independently of the first business-menu entry.
- Update automated tests and frontend README.

## Constraints
- Before approval, write only .agents/task.md and .agents/plan.md.
- Preserve previous layout/styles, protected routes and authentication contracts.
- No dependency, configuration, infrastructure, database or backend changes.
- UI menu changes only; unavailable business pages remain explicit placeholders.
- Preserve all existing and concurrent changes outside this task.

## Acceptance criteria
- Each role displays only its requested business entries, with the requested group structure.
- Role 1 groups collapse independently; role 3 has a directly selectable registration item.
- Quick access cards match the current role; profile actions still open Thông tin cá nhân, not faculty/topic/registration screens.
- Menu selection/active states, mobile drawer, logout and protected routes continue working.
- Automated tests cover full role menus and absence of removed/unauthorized entries.
- npm run lint, npm run test, npm run build and scoped diff checks pass.

## Assumptions and risks
- Tổng quan and Đăng xuất remain shared utility controls, outside the requested business menu list.
- Account/profile remain accessible from the header and welcome action, without a personal sidebar group.
- Current MainLayout assumes the first menu item is profile; this dependency must be removed to prevent incorrect navigation after restructuring.
- Current tests depend on removed student menu entries and require intentional updates.
