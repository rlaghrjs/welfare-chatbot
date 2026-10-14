import test, { beforeEach } from 'node:test'
import assert from 'node:assert/strict'
import { responseCards, restoreMessages, safePolicyLink, toWelfareCard } from '../src/api/policyMapper.js'
import { apiFetch, clearLocalInstallation } from '../src/api.ts'
import { sendMessage, getChatList, getSessionDetail, deleteSession, transcribeAudio, getCurrentSessionId } from '../src/api/welfare.js'
import { searchPayload } from '../src/api/searchSettings.js'

const storage = new Map()
globalThis.localStorage = {
  getItem: key => storage.get(key) ?? null,
  setItem: (key, value) => storage.set(key, String(value)),
  removeItem: key => storage.delete(key),
}
let calls
let respond
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
beforeEach(() => {
  storage.clear(); clearLocalInstallation(); calls = []
  respond = () => json([])
  globalThis.fetch = async (url, options = {}) => {
    calls.push({ url, options })
    if (url.endsWith('/api/installations')) return json({ installation_id: JSON.parse(options.body).installation_id }, 201)
    return respond(url, options)
  }
})

test('both central and local result groups use the original card design fields', () => {
  const cards = responseCards({ results: {
    central: { policies: [{ serv_id: 'same', serv_nm: '월세', intrs_thema_array: '040' }] },
    local: { policies: [{ serv_id: 'same', serv_nm: '의료', intrs_thema_nm_array: '신체건강' }] },
  } })
  assert.equal(cards.length, 2)
  assert.equal(cards[0].tag, '주거'); assert.equal(cards[1].tag, '신체건강')
  assert.notEqual(cards[0].id, cards[1].id)
  assert.deepEqual(responseCards({}), [])
})

test('multi-turn restoration attaches both card groups to the correct answer even with identical timestamps', () => {
  const row = (role, content, message_type = 'text', message_metadata = null) => ({ role, content, message_type, message_metadata, created_at: '2026-09-29T00:00:00' })
  const card = (id, title) => row('assistant', null, 'welfare_cards', { title, policies: [{ serv_id: id, serv_nm: id }] })
  const rows = [row('user', '첫 질문'), row('assistant', '첫 답변'), card('A','중앙 복지제도'), card('B','지자체 복지제도'), row('user','두번째'), row('assistant','두번째 답변'), card('C','중앙 복지제도')]
  const restored = restoreMessages(rows)
  assert.equal(restored.length, 4)
  assert.deepEqual(restored[1].welfareList.map(c => c.title), ['A','B'])
  assert.deepEqual(restored[3].welfareList.map(c => c.title), ['C'])
})

test('missing summaries do not show undefined and unsafe links are not clickable', () => {
  assert.deepEqual(toWelfareCard({}).items, [])
  assert.equal(safePolicyLink('javascript:alert(1)'), null)
  assert.equal(safePolicyLink('data:text/html,hello'), null)
  assert.equal(safePolicyLink('https://example.com/policy'), 'https://example.com/policy')
})

test('registration is shared and every private request includes the persisted bearer token', async () => {
  await Promise.all([getChatList(), getChatList()])
  assert.equal(calls.filter(c => c.url.endsWith('/api/installations')).length, 1)
  const saved = JSON.parse(storage.get('welfareInstallation'))
  assert.ok(saved.secret.length >= 43)
  for (const request of calls.filter(c => c.url.endsWith('/api/chat/sessions'))) {
    assert.equal(request.options.headers.get('Authorization'), `Bearer ${saved.installation_id}.${saved.secret}`)
  }
})

test('first message creates chat through new endpoint and follow-up reuses returned ID', async () => {
  respond = () => json({ session_id: 'session-1', answer: '답변', results: {} })
  await sendMessage('첫 질문'); await sendMessage('다음 질문')
  const messages = calls.filter(c => c.url.endsWith('/api/chat/message'))
  assert.equal(messages.length, 2)
  assert.equal(JSON.parse(messages[0].options.body).session_id, null)
  assert.equal(JSON.parse(messages[1].options.body).session_id, 'session-1')
  assert.equal(getCurrentSessionId(), 'session-1')
  assert.equal(calls.some(c => /\/session$|\/end$/.test(c.url)), false)
})

test('HTTP failure surfaces backend error and does not replace current session', async () => {
  storage.set('welfareLastSession', 'existing')
  respond = () => json({ detail: '복지 API 요청 실패' }, 502)
  await assert.rejects(sendMessage('질문'), { message: '복지 API 요청 실패', status: 502 })
  assert.equal(getCurrentSessionId(), 'existing')
})

test('history list works without session status and detail restores ordered cards', async () => {
  respond = url => url.endsWith('/sessions') ? json([{session_id:'one', title:'기록', created_at:'2026-09-29T00:00:00Z'}]) : json({session:{session_id:'one'}, messages:[{role:'assistant',message_type:'text',content:'답변'}]})
  assert.equal((await getChatList())[0].preview, '이전 대화 이어보기')
  assert.equal((await getSessionDetail('one')).messages[0].text, '답변')
})

test('deleting a different chat does not clear active chat; deleting active chat does', async () => {
  storage.set('welfareLastSession','active')
  respond = () => new Response(null, {status:204})
  await deleteSession('other'); assert.equal(getCurrentSessionId(), 'active')
  await deleteSession('active'); assert.equal(getCurrentSessionId(), null)
  assert.equal(calls.at(-1).options.method, 'DELETE')
})

test('profile search keeps age zero and can be disabled without losing settings', () => {
  storage.set('welfareProfile', JSON.stringify({age:0,lifeArray:'001'}))
  storage.set('useWelfareProfile','true'); storage.set('ctpvNm','서울특별시')
  assert.deepEqual(searchPayload(), {ctpvNm:'서울특별시',useProfile:true,profile:{age:0,lifeArray:'001'}})
  storage.set('useWelfareProfile','false')
  assert.equal(searchPayload().profile, null)
})

test('transcription uses same authenticated API and retains recorded media format', async () => {
  respond = () => json({text:'음성 질문'})
  assert.equal(await transcribeAudio(new Blob(['test'],{type:'audio/mp4'})), '음성 질문')
  assert.ok(calls.at(-1).url.endsWith('/api/stt/transcribe'))
  assert.equal(calls.at(-1).options.body.get('file').name, 'recording.mp4')
  assert.equal(calls.at(-1).options.headers.has('Authorization'), true)
})

test('expired auth is reported rather than silently replaying a write', async () => {
  respond = () => json({detail:'인증 확인 필요'},401)
  await assert.rejects(apiFetch('/api/subscriptions',{method:'POST'}), {status:401})
  assert.equal(calls.filter(c => c.url.endsWith('/api/subscriptions')).length,1)
})
