import type { AcademicManagement } from '../useAcademicManagement'

export interface SelectOption { id: string; label: string | null }
export function AcademicFormField({ state, name, options, showOptionIds = true }: { state: AcademicManagement; name: string; options?: SelectOption[]; showOptionIds?: boolean }) {
  const field = state.config.fields.find((item) => item.key === name)
  if (!field || !state.form) return null
  const value = state.form[name]
  const id = `academic-${name}`
  const error = state.errors[name]
  const required = field.required && !(field.type === 'password' && state.editing !== undefined)
  const common = { id, name, required, 'aria-invalid': !!error, 'aria-describedby': error ? `${id}-error` : undefined }
  return <div><label htmlFor={id}>{field.label}{required ? ' *' : ''}{field.type === 'password' && state.editing !== undefined ? ' (để trống để giữ nguyên)' : ''}</label>
    {options ? <select {...common} value={value} onChange={(event) => state.changeField(name, event.target.value)}>
      <option value="">{field.required ? 'Chọn giá trị' : 'Không chọn'}</option>
      {value && !options.some((option) => option.id === value) && <option value={value}>{value} (không có trong danh sách)</option>}
      {options.map((option) => <option key={option.id} value={option.id}>{option.label ? showOptionIds ? `${option.label} (${option.id})` : option.label : option.id}</option>)}
    </select> : <input {...common} type={['number', 'email', 'date', 'password'].includes(field.type ?? '') ? field.type : 'text'} autoComplete={field.type === 'password' ? 'new-password' : undefined} step={field.integer ? '1' : 'any'} maxLength={name === state.config.id ? 255 : undefined} disabled={state.editing !== undefined && name === state.config.id} value={value} onChange={(event) => state.changeField(name, event.target.value)} />}
    {error && <span id={`${id}-error`} className="academic-error">{error}</span>}
  </div>
}
