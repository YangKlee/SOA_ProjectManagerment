import type { AcademicManagement } from '../useAcademicManagement'

export function AcademicSearch({ state, hasName }: { state: AcademicManagement; hasName: boolean }) {
  return <form role="search" aria-label={`Tìm ${state.config.singular}`} className="academic-search" onSubmit={(event) => { event.preventDefault(); state.search() }}>
    <label>Tìm kiếm theo {hasName ? 'mã hoặc tên' : 'mã'}<input type="search" value={state.query} onChange={(event) => state.setQuery(event.target.value)} placeholder={hasName ? 'Nhập mã hoặc tên…' : 'Nhập mã…'} /></label>
    <button type="submit">Search</button>
  </form>
}
