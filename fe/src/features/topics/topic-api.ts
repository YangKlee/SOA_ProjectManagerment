import { apiClient } from '../../services/api-client'

export interface Topic {
  topic_id: string
  name: string
  description: string | null
  major_name: string | null
  // This spelling is part of the published topic-service response contract.
  avisor_name: string | null
}
export interface CreateTopic {
  topic_id: string
  name: string
  description: string
  major_id: string
  advisor_id: string
}

const path = '/topics/api/v1/topics/'
function topic(value: unknown): Topic {
  if (!value || typeof value !== 'object') throw new Error('Invalid topic response')
  const row = value as Record<string, unknown>
  if (typeof row.topic_id !== 'string' || !row.topic_id || typeof row.name !== 'string' ||
      !['description', 'major_name', 'avisor_name'].every(key => row[key] === null || typeof row[key] === 'string')) {
    throw new Error('Invalid topic response')
  }
  return row as unknown as Topic
}
export async function listTopics(signal: AbortSignal): Promise<Topic[]> {
  const { data } = await apiClient.get<unknown>(path, { signal })
  if (!Array.isArray(data)) throw new Error('Invalid topic list response')
  return data.map(topic)
}
export async function createTopic(input: CreateTopic, signal: AbortSignal): Promise<void> {
  await apiClient.post(path, input, { signal })
}
export async function getTopic(id: string, signal: AbortSignal): Promise<Topic> {
  const { data } = await apiClient.get<unknown>(`${path}${encodeURIComponent(id)}/`, { signal })
  const row = topic(data)
  if (row.topic_id !== id) throw new Error('Invalid topic identity')
  return row
}
