import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { createPortal } from 'react-dom'

export function Modal({ title, busy, onClose, children }: { title: string; busy: boolean; onClose: () => void; children: ReactNode }) {
  const titleId = useId()
  const overlay = useRef<HTMLDivElement>(null)
  const dialog = useRef<HTMLElement>(null)

  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null
    const previousOverflow = document.body.style.overflow
    const siblings = Array.from(document.body.children).filter((node) => node !== overlay.current)
    const previousInert = siblings.map((node) => node.hasAttribute('inert'))
    siblings.forEach((node) => node.setAttribute('inert', ''))
    document.body.style.overflow = 'hidden'
    const firstInput = dialog.current?.querySelector<HTMLElement>('input:not(:disabled), select:not(:disabled), textarea:not(:disabled)')
    ;(firstInput ?? dialog.current)?.focus()
    return () => {
      document.body.style.overflow = previousOverflow
      siblings.forEach((node, index) => { if (!previousInert[index]) node.removeAttribute('inert') })
      if (opener?.isConnected && !opener.matches(':disabled')) opener.focus()
      else document.querySelector<HTMLElement>('main[tabindex]')?.focus()
    }
  }, [])

  return createPortal(<div ref={overlay} className="academic academic-modal-backdrop">
    <section ref={dialog} className="academic-modal" role="dialog" aria-modal="true" aria-labelledby={titleId} aria-busy={busy} tabIndex={-1} onKeyDown={(event) => {
      if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (!busy) onClose() }
      if (event.key !== 'Tab') return
      const controls = Array.from(dialog.current?.querySelectorAll<HTMLButtonElement | HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>('button, input, select, textarea') ?? []).filter((control) => !control.disabled && !control.closest('fieldset:disabled'))
      const first = controls[0], last = controls.at(-1)
      if (!first) { event.preventDefault(); dialog.current?.focus() }
      else if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) { event.preventDefault(); last?.focus() }
      else if (!event.shiftKey && (document.activeElement === last || document.activeElement === dialog.current)) { event.preventDefault(); first.focus() }
    }}>
      <div className="academic-modal-heading"><h2 id={titleId}>{title}</h2><button type="button" aria-label="Đóng popup" disabled={busy} onClick={onClose}>×</button></div>
      {children}
    </section>
  </div>, document.body)
}
