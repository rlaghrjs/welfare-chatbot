import { useState, useEffect } from 'react'
import { getChatList } from '../api/welfare'

export default function ChatList({ onSelectSession, onDeleteSession, isActive, revision, disabled }) {
  const [query, setQuery] = useState('')
  const [chats, setChats] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    let active = true
    if (isActive) getChatList().then(data => {
      if (active) { setChats(data); setError(''); setLoading(false) }
    }).catch(e => { if (active) { setError(e.message); setLoading(false) } })
    return () => { active = false }
  }, [isActive, revision, retry])

  const filtered = chats.filter(chat =>
    chat.title.includes(query) || chat.preview.includes(query)
  )

  return (
    <div className="flex flex-col h-full bg-[#F0F4FF] dark:bg-[#0F1120]">
      <div className="px-[14px] py-[12px]">
        <div className="flex items-center gap-[10px] bg-white dark:bg-[#1A1F35] border border-[#E2E8F0] dark:border-[#2A3050] rounded-2xl px-[14px] py-[10px]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <circle cx="11" cy="11" r="7" stroke="#8899BB" strokeWidth="2"/>
            <path d="M16.5 16.5L21 21" stroke="#8899BB" strokeWidth="2" strokeLinecap="round"/>
          </svg>
          <input
            className="flex-1 text-[#1A2340] dark:text-[#E8EEFF] outline-none placeholder:text-[#8899BB] bg-transparent"
            style={{ fontSize: '0.9em' }}
            placeholder="채팅 검색..."
            value={query}
            onChange={e => setQuery(e.target.value)}
          />
          {query && (
            <button onClick={() => setQuery('')} className="text-[#8899BB] text-[16px]">✕</button>
          )}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-[14px] flex flex-col gap-[8px]">
        {error && <p role="alert" className="text-[13px] text-[#4A5A7A] dark:text-[#E8EEFF]">{error}<button className="ml-2 text-[#4A7FFF]" onClick={() => setRetry(n => n + 1)}>다시 시도</button></p>}
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full gap-[8px]">
            <div className="flex gap-[4px]">
              <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-[8px]">
            <span className="text-[32px]">💬</span>
            <p className="text-[#8899BB] dark:text-[#5566AA]" style={{ fontSize: '0.9em' }}>
              {query ? '검색 결과가 없어요' : '아직 채팅 내역이 없어요'}
            </p>
          </div>
        ) : (
          filtered.map(chat => (
            <div
              key={chat.id}
              className="w-full bg-white dark:bg-[#1A1F35] rounded-2xl px-[16px] py-[14px] border border-[#E2E8F0] dark:border-[#2A3050] text-left active:scale-[0.98] transition-transform"
            >
              <button disabled={disabled} onClick={() => onSelectSession(chat.id)} className="w-full text-left disabled:opacity-50" aria-label={`${chat.title} 대화 열기`}>
              <div className="flex justify-between items-start mb-[4px]">
                <span className="font-bold text-[#1A2340] dark:text-[#E8EEFF] flex-1 truncate pr-[8px]"
                  style={{ fontSize: '1em' }}>
                  {chat.title}
                </span>
                <span className="text-[#AAB8D4] dark:text-[#445577] shrink-0"
                  style={{ fontSize: '0.8em' }}>{chat.date}</span>
              </div>
              <p className="text-[#8899BB] dark:text-[#5566AA] truncate" style={{ fontSize: '0.85em' }}>{chat.preview}</p>
              </button>
              <div className="text-right mt-1"><button disabled={disabled} onClick={() => onDeleteSession(chat.id)} className="text-[12px] text-[#8899BB] dark:text-[#8899BB] disabled:opacity-40" aria-label={`${chat.title} 기록 삭제`}>기록 삭제</button></div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
