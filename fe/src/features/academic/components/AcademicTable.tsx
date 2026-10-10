import type { ReactNode } from 'react'
import type { AcademicRecord } from '../academic-api'
import { addressable, valueOf } from '../academic-config'
import type { AcademicManagement } from '../useAcademicManagement'

export interface AcademicColumn { key: string; label: string; render?: (row: AcademicRecord) => ReactNode }
export function AcademicTable({ state, columns, searchFields }: { state: AcademicManagement; columns: AcademicColumn[]; searchFields: string[] }) {
  const filtered = state.rows.filter((row) => searchFields.some((key) => valueOf(row, key).toLocaleLowerCase('vi').includes(state.appliedQuery)))
  return <><p className="academic-count">{filtered.length} / {state.rows.length} bản ghi</p><div className="academic-table"><table>
    <caption>Danh sách {state.config.singular}</caption><thead><tr>{columns.map((column) => <th scope="col" key={column.key}>{column.label}</th>)}<th scope="col">Thao tác</th></tr></thead>
    <tbody>{filtered.map((row) => {
      const id = valueOf(row, state.config.id)
      const disabled = state.busy || !addressable(state.resource, id)
      return <tr key={id}>{columns.map((column) => <td key={column.key}>{column.render ? column.render(row) : valueOf(row, column.key) || '—'}</td>)}<td><div className="academic-actions">
        <button disabled={disabled} aria-label={`Sửa ${id}`} onClick={() => state.open(row)}>Sửa</button><button disabled={disabled} aria-label={`Xóa ${id}`} onClick={() => state.requestDelete(row)}>Xóa</button>
      </div></td></tr>
    })}</tbody>
  </table></div>{!filtered.length && <p>{state.rows.length ? 'Không tìm thấy kết quả phù hợp.' : 'Chưa có dữ liệu.'}</p>}</>
}
