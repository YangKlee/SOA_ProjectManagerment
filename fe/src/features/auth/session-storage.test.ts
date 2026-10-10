import { afterEach, expect, it, vi } from 'vitest'
import { clearSessionToken, readSessionToken, saveSessionToken, SESSION_TOKEN_KEY } from './session-storage'

afterEach(() => vi.restoreAllMocks())

it('persists only the access token in tab storage and clears it explicitly', () => {
  expect(readSessionToken()).toEqual({ token: null, unavailable: false })
  expect(saveSessionToken('access-test')).toBe(true)
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBe('access-test')
  expect(localStorage.length).toBe(0)
  expect(readSessionToken().token).toBe('access-test')
  expect(clearSessionToken()).toBe(true)
  expect(readSessionToken().token).toBeNull()
})

it.each(['', '   ', 'x'.repeat(16385)])('discards blank or oversized saved data %#', (token) => {
  sessionStorage.setItem(SESSION_TOKEN_KEY, token)
  expect(readSessionToken().token).toBeNull()
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBeNull()
})

it('handles denied reads and writes without throwing', () => {
  vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('denied') })
  expect(readSessionToken()).toEqual({ token: null, unavailable: true })
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('quota') })
  expect(saveSessionToken('access')).toBe(false)
})

it('writes an empty tombstone if removal alone fails and reports complete denial', () => {
  saveSessionToken('old-access')
  vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => { throw new Error('denied') })
  expect(clearSessionToken()).toBe(true)
  expect(sessionStorage.getItem(SESSION_TOKEN_KEY)).toBe('')
  expect(readSessionToken().token).toBeNull()
  vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('denied') })
  expect(clearSessionToken()).toBe(false)
})
