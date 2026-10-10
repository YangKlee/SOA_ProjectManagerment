import type { AcademicManagement } from '../useAcademicManagement'

export interface SelectOption { id: string; label: string | null }
export function AcademicFormField({ state, name, options }: { state: AcademicManagement; name: string; options?: SelectOption[] }) {
  const field = state.config.fields.find((item) => item.key === name)
  if (!field || !state.form) return null
  const value = state.form[name]
  const id = `academic-${name}`
  const error = state.errors[name]
  const common = { id, name, required: field.required, 'aria-invalid': !!error, 'aria-describedby': error ? `${id}-error` : undefined }
  return <div><label htmlFor={id}>{field.label}{field.required ? ' *' : ''}</label>
    {options ? <select {...common} value={value} onChange={(event) => state.changeField(name, event.target.value)}>
      <option value="">{field.required ? 'Chọn giá trị' : 'Không chọn'}</option>
      {value && !options.some((option) => option.id === value) && <option value={value}>{value} (không có trong danh sách)</option>}
      {options.map((option) => <option key={option.id} value={option.id}>{option.label ? `${option.label} (${option.id})` : option.id}</option>)}
    </select> : <input {...common} type={field.type === 'number' ? 'number' : 'text'} step={field.integer ? '1' : 'any'} maxLength={name === state.config.id ? 255 : undefined} disabled={state.editing !== undefined && name === state.config.id} value={value} onChange={(event) => state.changeField(name, event.target.value)} />}
    {error && <span id={`${id}-error`} className="academic-error">{error}</span>}
  </div>
}
