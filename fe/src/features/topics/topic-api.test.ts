import MockAdapter from 'axios-mock-adapter'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { apiClient, setAccessToken } from '../../services/api-client'
import { createTopic, getTopic, listTopics } from './topic-api'

const base = '/topics/api/v1/topics/'
const row = { topic_id: 'guid-1', name: 'SOA', description: null, major_name: null, avisor_name: 'An' }
let mock: MockAdapter
beforeEach(() => { mock = new MockAdapter(apiClient, { onNoMatch: 'throwException' }); setAccessToken('test-token') })
afterEach(() => { mock.restore(); setAccessToken(null) })
describe('Topic Gateway API', () => {
  it('loads published names and forwards the JWT and abort signal', async () => {
    mock.onGet(base).reply(200, [row])
    const signal = new AbortController().signal
    expect(await listTopics(signal)).toEqual([row])
    expect(mock.history.get[0].headers?.Authorization).toBe('Bearer test-token')
    expect(mock.history.get[0].signal).toBe(signal)
  })
  it('posts only the provided create DTO', async () => {
    const input = { topic_id: 'guid-1', name: 'SOA', description: '', advisor_id: 'GV1', major_id: '2' }
    mock.onPost(base).reply(201, row)
    await createTopic(input, new AbortController().signal)
    expect(JSON.parse(mock.history.post[0].data)).toEqual(input)
    expect(mock.history.post).toHaveLength(1)
  })
  it('encodes the topic ID when checking creation', async () => {
    mock.onGet(`${base}guid%201/`).reply(200, { ...row, topic_id: 'guid 1' })
    expect((await getTopic('guid 1', new AbortController().signal)).topic_id).toBe('guid 1')
  })
  it.each([{}, [null], [{ ...row, major_name: 1 }], [{ ...row, topic_id: '' }]])('rejects malformed list responses %#', async (data) => {
    mock.onGet(base).reply(200, data)
    await expect(listTopics(new AbortController().signal)).rejects.toThrow()
  })
  it('rejects a mismatched detail identity', async () => {
    mock.onGet(`${base}different/`).reply(200, row)
    await expect(getTopic('different', new AbortController().signal)).rejects.toThrow('Invalid topic identity')
  })
  it('does not send cancelled requests', async () => {
    const controller = new AbortController(); controller.abort()
    await expect(listTopics(controller.signal)).rejects.toMatchObject({ kind: 'cancelled' })
    expect(mock.history.get).toHaveLength(0)
  })
})
