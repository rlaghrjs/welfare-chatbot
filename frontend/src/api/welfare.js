import { apiFetch, clearLocalInstallation } from '../api.ts'
import { responseCards, restoreMessages } from './policyMapper.js'
import { searchPayload } from './searchSettings.js'

const SESSION_KEY = 'welfareLastSession'
export const getCurrentSessionId = () => localStorage.getItem(SESSION_KEY)
export function setCurrentSessionId(id) {
  if (id) localStorage.setItem(SESSION_KEY, id)
  else localStorage.removeItem(SESSION_KEY)
}

export async function sendMessage(message) {
  const response = await apiFetch('/api/chat/message', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: getCurrentSessionId(), ...searchPayload() }),
  })
  const data = await response.json()
  setCurrentSessionId(data.session_id)
  return { sessionId: data.session_id, reply: data.answer, welfareList: responseCards(data) }
}

export async function getChatList() {
  const data = await (await apiFetch('/api/chat/sessions')).json()
  return data.map(session => ({
    id: session.session_id, title: session.title || '새 채팅', preview: '이전 대화 이어보기',
    date: new Date(session.updated_at || session.created_at).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' }),
  }))
}

export async function getSessionDetail(sessionId) {
  const data = await (await apiFetch(`/api/chat/session/${sessionId}`)).json()
  return { sessionId: data.session.session_id, messages: restoreMessages(data.messages) }
}

export async function deleteSession(sessionId) {
  await apiFetch(`/api/chat/session/${sessionId}`, { method: 'DELETE' })
  if (getCurrentSessionId() === sessionId) setCurrentSessionId(null)
}

export async function transcribeAudio(blob) {
  const form = new FormData()
  const extension = blob.type.includes('mp4') ? 'mp4' : blob.type.includes('ogg') ? 'ogg' : 'webm'
  form.append('file', blob, `recording.${extension}`)
  const data = await (await apiFetch('/api/stt/transcribe', { method: 'POST', body: form })).json()
  return data.text || ''
}

export async function deleteAppData() {
  await apiFetch('/api/installations/me', { method: 'DELETE' })
  clearLocalInstallation()
  for (const key of [SESSION_KEY, 'welfareProfile', 'ctpvNm', 'useWelfareProfile', 'showWelfareDebug']) localStorage.removeItem(key)
}
