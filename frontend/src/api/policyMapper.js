const themes = {
  '010': ['신체건강', '🏥', '#E0F5EC', 'green'], '020': ['정신건강', '🏥', '#E0F5EC', 'green'],
  '030': ['생활지원', '📋', '#E8F0FF', 'blue'], '040': ['주거', '🏠', '#E8F0FF', 'blue'],
  '050': ['일자리', '💼', '#FFF0E8', 'blue'], '060': ['문화·여가', '🎨', '#EDE8FF', 'purple'],
  '070': ['안전·위기', '📋', '#E8F0FF', 'blue'], '080': ['임신·출산', '👶', '#FFF0E8', 'blue'],
  '090': ['보육', '👶', '#FFF0E8', 'blue'], '100': ['교육', '📚', '#EDE8FF', 'purple'],
  '110': ['입양·위탁', '👶', '#FFF0E8', 'blue'], '120': ['보호·돌봄', '👶', '#FFF0E8', 'blue'],
  '130': ['서민금융', '💰', '#E8F0FF', 'blue'], '140': ['법률', '📋', '#E8F0FF', 'blue'],
  '150': ['관계개선', '📋', '#E8F0FF', 'blue'], '160': ['에너지', '💡', '#E8F0FF', 'blue'],
}

export function safePolicyLink(link) {
  try { const url = new URL(link); return ['http:', 'https:'].includes(url.protocol) ? url.href : null }
  catch { return null }
}

export function toWelfareCard(policy, source = '') {
  const raw = String(policy.intrs_thema_array || policy.intrs_thema_nm_array || '')
  const tokens = raw.split(/[,\s]+/)
  const theme = Object.entries(themes).find(([code, [name]]) =>
    tokens.includes(code) || raw.includes(name) || name.split('·').some(part => raw.includes(part)))?.[1]
    || ['복지', '📋', '#E8F0FF', 'blue']
  const summary = policy.serv_dgst || ''
  return {
    id: `${source}:${policy.serv_id}`, source,
    icon: theme[1], iconBg: theme[2], title: policy.serv_nm || '복지제도',
    tag: theme[0], tagColor: theme[3], checkColor: 'blue',
    items: [summary.length > 80 ? `${summary.slice(0, 80)}…` : summary,
      policy.jur_mnof_nm || policy.biz_chr_dept_nm,
      [policy.ctpv_nm, policy.sgg_nm].filter(Boolean).join(' '), policy.srv_pvsn_nm].filter(Boolean),
    link: safePolicyLink(policy.serv_dtl_link),
  }
}

export function responseCards(data) {
  return [
    ...(data.results?.central?.policies || []).map(p => toWelfareCard(p, '중앙')),
    ...(data.results?.local?.policies || []).map(p => toWelfareCard(p, '지자체')),
  ]
}

export function restoreMessages(rows) {
  const messages = []
  let answer = null
  // The backend orders by sequence_no. Never match cards using timestamps.
  for (const row of rows) {
    if (row.role === 'user') {
      messages.push({ role: 'user', text: row.content || '' }); answer = null
    } else if (row.role === 'assistant' && row.message_type === 'welfare_cards') {
      if (!answer) { answer = { role: 'bot', text: '검색한 복지제도입니다.', welfareList: [] }; messages.push(answer) }
      const source = row.message_metadata?.title?.includes('지자체') ? '지자체' : '중앙'
      answer.welfareList.push(...(row.message_metadata?.policies || []).map(p => toWelfareCard(p, source)))
    } else if (row.role === 'assistant' && (!row.message_type || row.message_type === 'text')) {
      answer = { role: 'bot', text: row.content || '', welfareList: [] }; messages.push(answer)
    }
  }
  return messages
}
