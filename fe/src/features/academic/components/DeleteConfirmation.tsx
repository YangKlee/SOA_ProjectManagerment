import { useEffect, useRef } from 'react'
import type { AcademicManagement } from '../useAcademicManagement'

export function DeleteConfirmation({ state }: { state: AcademicManagement }) {
  const panel = useRef<HTMLElement>(null)
  useEffect(() => { panel.current?.focus() }, [])
  return <section ref={panel} tabIndex={-1} className="academic-editor" aria-label="Xác nhận xóa">
    <h2>Xóa {state.config.singular} {state.deleting}?</h2><p>Dữ liệu có liên kết có thể bị từ chối xóa. Xác nhận để tiếp tục.</p>
    {(state.resource === 'students' || state.resource === 'lecturers') && <p>Thao tác này xóa cả hồ sơ và tài khoản đăng nhập liên quan.</p>}
    <div className="academic-actions"><button className="academic-danger" disabled={state.busy} onClick={() => void state.remove()}>{state.busy ? 'Đang xóa…' : 'Xác nhận xóa'}</button><button disabled={state.busy} onClick={state.cancelDelete}>Hủy</button></div>
  </section>
}
