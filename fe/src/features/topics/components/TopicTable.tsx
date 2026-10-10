import type { Topic } from '../topic-api'

export function TopicTable({ rows, total }: { rows: Topic[]; total: number }) {
  return <>
    <p className="academic-count">Hiển thị {rows.length} / {total} đề tài</p>
    <div className="academic-table"><table aria-label="Danh sách đề tài">
      <thead><tr><th scope="col">Mã đề tài</th><th scope="col">Tên đề tài</th><th scope="col">Giáo viên hướng dẫn</th><th scope="col">Tên ngành</th></tr></thead>
      <tbody>{rows.map(row => <tr key={row.topic_id}>
        <td>{row.topic_id}</td><td>{row.name}</td><td>{row.avisor_name || '—'}</td><td>{row.major_name || '—'}</td>
      </tr>)}{rows.length === 0 && <tr><td colSpan={4}>Không có đề tài phù hợp.</td></tr>}</tbody>
    </table></div>
  </>
}
