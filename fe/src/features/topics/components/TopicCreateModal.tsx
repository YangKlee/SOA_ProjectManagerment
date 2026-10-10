import { Modal } from '../../academic/components/Modal'
import { numericMajor } from '../useTopics'
import type { TopicField, TopicState } from '../useTopics'

export function TopicCreateModal({ state }: { state: TopicState }) {
  if (!state.draft) return null
  const error = (key: TopicField) => state.errors[key] && <span id={`topic-${key}-error`} className="academic-error">{state.errors[key]}</span>
  const accessibility = (key: TopicField) => ({ 'aria-invalid': !!state.errors[key], 'aria-describedby': state.errors[key] ? `topic-${key}-error` : undefined })
  return <Modal title="Tạo đề tài" busy={state.busy} onClose={state.close}>
    <form aria-label="Tạo đề tài" noValidate onSubmit={event => {
      event.preventDefault()
      const form = event.currentTarget
      void state.save().then(key => { if (key) (form.elements.namedItem(key) as HTMLElement | null)?.focus() })
    }}>
      <p className="academic-hint">Mã đề tài được sinh tự động khi tạo.</p>
      {state.formError && <p role="alert" className="academic-error">{state.formError}</p>}
      {state.optionsLoading && <p role="status">Đang tải ngành và giảng viên…</p>}
      {state.optionsError && <p role="alert" className="academic-error">{state.optionsError}</p>}
      {!state.optionsReady && !state.optionsLoading && <button type="button" onClick={() => void state.loadOptions()}>Tải lại lựa chọn</button>}
      {state.optionsReady && (!state.lecturers.length || !state.majors.some(row => numericMajor(row.major_id))) && <p role="alert">Chưa có giảng viên hoặc ngành có mã số hợp lệ. Vui lòng bổ sung dữ liệu học vụ.</p>}
      <fieldset disabled={state.busy || state.uncertain}>
        <div className="academic-fields">
          <div><label htmlFor="topic-name">Tên đề tài</label><input id="topic-name" name="name" required value={state.draft.name} onChange={event => state.change('name', event.target.value)} {...accessibility('name')} />{error('name')}</div>
          <div><label htmlFor="topic-advisor">Giáo viên hướng dẫn</label><select id="topic-advisor" name="advisor_id" required disabled={!state.optionsReady} value={state.draft.advisor_id} onChange={event => state.change('advisor_id', event.target.value)} {...accessibility('advisor_id')}>
            <option value="">Chọn giáo viên hướng dẫn</option>
            {state.lecturers.map(row => {
              const name = [row.user?.first_name, row.user?.last_name].filter(Boolean).join(' ')
              return <option key={row.lecturer_id} value={row.lecturer_id}>{name ? `${name} (${row.lecturer_id})` : row.lecturer_id}</option>
            })}
          </select>{error('advisor_id')}</div>
          <div><label htmlFor="topic-major">Ngành</label><select id="topic-major" name="major_id" required disabled={!state.optionsReady} value={state.draft.major_id} onChange={event => state.change('major_id', event.target.value)} {...accessibility('major_id')}>
            <option value="">Chọn ngành</option>
            {state.majors.map(row => <option key={row.major_id} value={row.major_id} disabled={!numericMajor(row.major_id)}>{row.name ? `${row.name} (${row.major_id})` : row.major_id}{!numericMajor(row.major_id) ? ' — Mã ngành chưa được hỗ trợ' : ''}</option>)}
          </select>{error('major_id')}</div>
          <div className="topic-description"><label htmlFor="topic-description">Mô tả đề tài</label><textarea id="topic-description" name="description" rows={5} value={state.draft.description} onChange={event => state.change('description', event.target.value)} {...accessibility('description')} />{error('description')}</div>
        </div>
      </fieldset>
      <div className="academic-actions">
        {state.uncertain ? <button type="button" className="academic-primary" disabled={state.busy} onClick={() => void state.checkResult()}>{state.busy ? 'Đang kiểm tra…' : 'Kiểm tra kết quả'}</button>
          : <button type="submit" className="academic-primary" disabled={state.busy || !state.optionsReady}>{state.busy ? 'Đang lưu…' : 'Tạo đề tài'}</button>}
        <button type="button" disabled={state.busy} onClick={state.close}>Hủy</button>
      </div>
    </form>
  </Modal>
}
