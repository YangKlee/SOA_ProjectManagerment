import type { IconName } from './dashboard-menu'

const paths: Record<IconName, string> = {
  home: 'm3 10 9-7 9 7M5 9v12h5v-7h4v7h5V9',
  user: 'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0ZM4 21v-3a8 8 0 0 1 16 0v3Z',
  bell: 'M18 8a6 6 0 0 0-12 0c0 8-3 8-3 10h18c0-2-3-2-3-10M10 21h4',
  chart: 'M4 3v17h17M8 16v-5m5 5V6m5 10V9',
  book: 'M12 5v16M3 3h5l4 2 4-2h5v16h-5l-4 2-4-2H3Z',
  calendar: 'M4 5h16v16H4ZM4 10h16M8 3v4m8-4v4M8 14h1m3 0h1m3 0h1M8 17h1m3 0h1',
  file: 'M14 3H5v18h14V8ZM14 3v5h5M8 12h8M8 16h6',
  check: 'M9 3H5v18h14v-9M9 3v4h6V3ZM11 13l3 3 7-8',
  award: 'M17 8A5 5 0 1 1 7 8a5 5 0 0 1 10 0ZM8 12l-2 9 6-3 6 3-2-9',
  users: 'M14 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0ZM3 21v-3a7 7 0 0 1 14 0v3M17 4a3 3 0 0 1 0 6m2 4a6 6 0 0 1 3 7',
  menu: 'M4 6h16M4 12h12M4 18h16', close: 'm6 6 12 12M6 18 18 6',
  chevron: 'm6 9 6 6 6-6', logout: 'M9 3H4v18h5M9 12h12m-5-5 5 5-5 5', arrow: 'M4 12h16m-6-6 6 6-6 6',
}
export function DashboardIcon({ name }: { name: IconName }) {
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name]} /></svg>
}

