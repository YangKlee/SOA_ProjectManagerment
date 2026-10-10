import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, expect, it } from 'vitest'
import { apiClient } from '../../services/api-client'
import { deleteRecord, listRecords, saveRecord } from './academic-api'

let mock: MockAdapter
beforeEach(() => { mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' }) })
afterEach(() => mock.restore())

it('encodes lecturer identifiers as a single path segment', async () => {
  const id = 'GV #?'
  const path = '/academic/api/lecturers/GV%20%23%3F/'
  const dto = { lecturer_id: id, department_id: null }
  mock.onPatch(path).reply(200, dto)
  mock.onDelete(path).reply(204)
  const signal = new AbortController().signal
  await saveRecord('lecturers', dto, signal, id)
  await deleteRecord('lecturers', id, signal)
  expect(mock.history.patch[0].url).toBe(path)
  expect(mock.history.delete[0].url).toBe(path)
})

it('rejects malformed list responses and aborts reads before dispatch', async () => {
  mock.onGet('/academic/api/departments/').reply(200, { results: [] })
  await expect(listRecords('departments', new AbortController().signal)).rejects.toThrow('Invalid academic list response')
  const controller = new AbortController()
  controller.abort()
  await expect(listRecords('departments', controller.signal)).rejects.toMatchObject({ kind: 'cancelled' })
  expect(mock.history.get).toHaveLength(1)
})
