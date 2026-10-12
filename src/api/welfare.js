const isEmulator = window.location.hostname === '10.0.2.2'
const BASE_URL = import.meta.env.VITE_API_URL || 
  (isEmulator ? 'http://10.0.2.2:8000' : 'http://localhost:8000')

let currentSessionId = null

export const createSession = async () => {
  const res = await fetch(`${BASE_URL}/api/chat/session`, { method: 'POST' })
  const data = await res.json()
  currentSessionId = data.session_id
  return currentSessionId
}

export const getCurrentSessionId = () => currentSessionId

export const setCurrentSessionId = (id) => {
  currentSessionId = id
}

export const sendMessage = async (message) => {
  if (!currentSessionId) {
    await createSession()
  }

  const res = await fetch(`${BASE_URL}/api/chat/session/${currentSessionId}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message }),
  })
  const data = await res.json()

  return {
    reply: data.answer,
    welfareList: data.policies.map(p => ({
      icon: getIcon(p.intrs_thema_array),
      iconBg: getBg(p.intrs_thema_array),
      title: p.serv_nm,
      tag: p.intrs_thema_array?.split(',')[0] || '복지',
      tagColor: getTagColor(p.intrs_thema_array),
      checkColor: 'blue',
      items: [
        p.serv_dgst?.slice(0, 40) + '...',
        p.jur_mnof_nm,
        p.srv_pvsn_nm,
      ].filter(Boolean),
      link: p.serv_dtl_link,
    })),
  }
}

export const getChatList = async () => {
  const res = await fetch(`${BASE_URL}/api/chat/sessions`)
  const data = await res.json()
  return data.map(session => ({
    id: session.session_id,
    title: session.title || '새 채팅',
    preview: session.status === 'active' ? '진행 중' : '종료된 채팅',
    date: new Date(session.created_at).toLocaleDateString('ko-KR', { month: 'long', day: 'numeric' }),
  }))
}

export const getSessionDetail = async (sessionId) => {
  const res = await fetch(`${BASE_URL}/api/chat/session/${sessionId}`)
  const data = await res.json()

  // 메시지를 ChatArea가 쓰는 형태로 변환
  const messages = []
  const metaMap = {}

  // welfare_cards 메시지 먼저 맵으로 정리
  data.messages.forEach(msg => {
    if (msg.message_type === 'welfare_cards' && msg.message_metadata?.policies) {
      // 직전 assistant 텍스트 메시지와 연결하기 위해 저장
      metaMap[msg.created_at] = msg.message_metadata.policies
    }
  })

  data.messages.forEach(msg => {
    if (msg.message_type === 'text' && msg.role === 'user') {
      messages.push({ role: 'user', text: msg.content })
    } else if (msg.message_type === 'text' && msg.role === 'assistant') {
      // 바로 다음 welfare_cards 메시지 찾기
      const nextMeta = data.messages.find(
        m => m.message_type === 'welfare_cards' &&
          new Date(m.created_at) > new Date(msg.created_at)
      )
      messages.push({
        role: 'bot',
        text: msg.content,
        welfareList: nextMeta?.message_metadata?.policies?.map(p => ({
          icon: getIcon(p.intrs_thema_array),
          iconBg: getBg(p.intrs_thema_array),
          title: p.serv_nm,
          tag: p.intrs_thema_array?.split(',')[0] || '복지',
          tagColor: getTagColor(p.intrs_thema_array),
          checkColor: 'blue',
          items: [
            p.serv_dgst?.slice(0, 40) + '...',
            p.jur_mnof_nm,
            p.srv_pvsn_nm,
          ].filter(Boolean),
          link: p.serv_dtl_link,
        })) || [],
      })
    }
  })

  return { sessionId, messages }
}

// ─── 헬퍼 함수 ───────────────────────────────
const getIcon = (thema) => {
  if (!thema) return '📋'
  if (thema.includes('주거')) return '🏠'
  if (thema.includes('일자리')) return '💼'
  if (thema.includes('건강') || thema.includes('의료')) return '🏥'
  if (thema.includes('돌봄') || thema.includes('보호')) return '👶'
  if (thema.includes('교육')) return '📚'
  if (thema.includes('금융')) return '💰'
  return '📋'
}

const getBg = (thema) => {
  if (!thema) return '#E8F0FF'
  if (thema.includes('주거')) return '#E8F0FF'
  if (thema.includes('일자리')) return '#FFF0E8'
  if (thema.includes('건강') || thema.includes('의료')) return '#E0F5EC'
  if (thema.includes('돌봄')) return '#FFF0E8'
  if (thema.includes('교육')) return '#EDE8FF'
  return '#E8F0FF'
}

const getTagColor = (thema) => {
  if (!thema) return 'blue'
  if (thema.includes('주거')) return 'blue'
  if (thema.includes('건강') || thema.includes('의료')) return 'green'
  if (thema.includes('교육')) return 'purple'
  return 'blue'
}
