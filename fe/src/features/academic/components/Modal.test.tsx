import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { Modal } from './Modal'

describe('Modal textarea keyboard support', () => {
  it('focuses a textarea and includes it at the end of the focus trap', () => {
    const close = vi.fn()
    render(<Modal title="Mô tả" busy={false} onClose={close}><label>Nội dung<textarea /></label></Modal>)
    const textarea = screen.getByRole('textbox', { name: 'Nội dung' })
    const closer = screen.getByRole('button', { name: 'Đóng popup' })
    expect(textarea).toHaveFocus()
    fireEvent.keyDown(textarea, { key: 'Tab' })
    expect(closer).toHaveFocus()
    fireEvent.keyDown(closer, { key: 'Tab', shiftKey: true })
    expect(textarea).toHaveFocus()
  })
})
