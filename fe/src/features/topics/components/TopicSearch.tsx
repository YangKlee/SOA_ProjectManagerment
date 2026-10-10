export function TopicSearch({ query, onChange, onSearch }: { query: string; onChange: (value: string) => void; onSearch: () => void }) {
  return <form role="search" aria-label="Tìm đề tài" className="academic-search" onSubmit={event => { event.preventDefault(); onSearch() }}>
    <label>Tìm kiếm theo mã hoặc tên<input type="search" value={query} onChange={event => onChange(event.target.value)} placeholder="Nhập mã hoặc tên…" /></label>
    <button type="submit">Search</button>
  </form>
}
