import type { ReactNode } from 'react'
import type { AcademicManagement } from '../useAcademicManagement'
import { AcademicSearch } from './AcademicSearch'
import { AcademicTable } from './AcademicTable'
import type { AcademicColumn } from './AcademicTable'
import { DeleteConfirmation } from './DeleteConfirmation'
import { Modal } from './Modal'
import '../academic.css'

export function AcademicManagementView({ state, columns, searchFields, children }: { state: AcademicManagement; columns: AcademicColumn[]; searchFields: string[]; children: ReactNode }) {
  const { singular } = state.config
  const title = `${state.editing === undefined ? 'Thêm' : 'Sửa'} ${singular}`
  return <section className="academic dash-surface" aria-label={`Danh sách ${singular}`}>
    <div className="academic-toolbar"><AcademicSearch state={state} hasName={searchFields.includes('name')} /><div className="academic-actions">
      <button type="button" disabled={state.loading || state.busy || state.form !== null || state.deleting !== null} onClick={() => void state.reload()}>Tải lại</button>
      <button className="academic-primary" type="button" disabled={!state.ready || state.busy} onClick={() => state.open()}>Thêm {singular}</button>
    </div></div>
    {(state.resource === 'departments' || state.resource === 'majors') && <p className="academic-hint">Mã phải là số nguyên không âm, không có số 0 ở đầu để có thể sửa hoặc xóa. Bản ghi có mã khác chỉ được hiển thị.</p>}
    {(state.resource === 'students' || state.resource === 'lecturers') && <p className="academic-hint">Tài khoản được tạo cùng hồ sơ. Mã là UserID đăng nhập và không thể đổi sau khi tạo.</p>}
    {state.notice && <p role="status" className="academic-success">{state.notice}</p>}
    {state.error && !state.form && <p role="alert" className="academic-error">{state.error}</p>}
    {state.form && <Modal title={title} busy={state.busy} onClose={state.closeForm}>
      <form aria-label={title} noValidate onSubmit={(event) => {
        event.preventDefault()
        const element = event.currentTarget
        void state.save().then((invalidField) => {
          if (invalidField) (element.elements.namedItem(invalidField) as HTMLElement | null)?.focus()
        })
      }}>
        {state.error && <p role="alert" className="academic-error">{state.error}</p>}
        <fieldset disabled={state.busy || !state.ready}><div className="academic-fields">{children}</div></fieldset>
        <div className="academic-actions"><button type="submit" className="academic-primary" disabled={state.busy || !state.ready}>{state.busy ? 'Đang lưu…' : 'Lưu'}</button><button type="button" disabled={state.busy} onClick={state.closeForm}>Hủy</button></div>
      </form>
    </Modal>}
    {state.deleting !== null && <DeleteConfirmation state={state} />}
    {state.loading ? <p role="status">Đang tải dữ liệu…</p> : state.ready && <AcademicTable state={state} columns={columns} searchFields={searchFields} />}
  </section>
}
