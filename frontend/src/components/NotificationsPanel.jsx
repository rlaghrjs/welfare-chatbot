import AppIcon from './AppIcon'
import { useEffect, useState } from 'react'
import { apiFetch } from '../api'

export default function NotificationsPanel({ ready }) {
  const [open, setOpen] = useState(false)
  const [data, setData] = useState({ items: [], unread_count: 0, total: 0 })
  const [error, setError] = useState('')
  const [page, setPage] = useState(0)
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    if (!ready) return
    let active = true
    let fetching = false
    async function refresh() {
      if (fetching) return
      fetching = true
      try {
        const response = await apiFetch(`/api/notifications?offset=${page * 20}&limit=20`)
        const next = await response.json()
        if (active) { setData(next); setError('') }
      } catch (e) { if (active) setError(e.message || '알림을 불러오지 못했어요.') }
      finally { fetching = false }
    }
    refresh()
    const timer = setInterval(refresh, 30000)
    return () => { active = false; clearInterval(timer) }
  }, [ready, page, open, revision])
  async function read(id) {
    try {
      await apiFetch(`/api/notifications/${id}/read`, { method: 'PATCH' })
      setRevision(n => n + 1)
    } catch (e) { setError(e.message) }
  }
  return <>
    <button disabled={!ready} aria-label={`알림 ${data.unread_count}개 읽지 않음`} aria-expanded={open} onClick={() => setOpen(!open)} className="text-[#4A7FFF] text-[13px]"><AppIcon name="notification" size={22} />{data.unread_count > 0 && ` ${data.unread_count}`}</button>
    {open && <section aria-label="정책 알림" className="absolute inset-x-0 top-[70px] bottom-[65px] z-50 bg-white dark:bg-[#1A1F35] text-[#1A2340] dark:text-[#E8EEFF] p-4 overflow-y-auto">
      <div className="flex justify-between mb-3"><h2 className="font-bold">정책 알림</h2><button onClick={() => setOpen(false)}>닫기</button></div>
      <p className="text-[12px] mb-3">관심 조건과 일치하는 정책이에요. 실제 지원 자격은 상세 안내에서 확인해주세요.</p>
      {error && <div role="alert">{error}<button onClick={() => setRevision(n => n + 1)} className="ml-2 underline">다시 시도</button></div>}
      {!error && !data.items.length && <p>아직 도착한 알림이 없어요. 설정에서 관심 조건을 등록해주세요.</p>}
      {data.items.map(item => <article key={item.id} className="border-b border-[#E2E8F0] py-3">
        <h3 className={item.read_at ? '' : 'font-bold'}>{item.title}</h3>
        <p className="text-[13px] my-2 whitespace-pre-wrap">{item.body}</p>
        <time className="text-[11px]">{new Date(item.created_at).toLocaleString('ko-KR')}</time>
        {!item.read_at && <button onClick={() => read(item.id)} className="ml-3 text-[12px] text-[#4A7FFF]">읽음 표시</button>}
        {/^https?:\/\//i.test(item.policy?.serv_dtl_link || '') && <a href={item.policy.serv_dtl_link} target="_blank" rel="noopener noreferrer" className="block text-[12px] text-[#4A7FFF] mt-2">정책 상세 보기</a>}
      </article>)}
      <div className="flex justify-between mt-4"><button disabled={!page} onClick={() => setPage(n => n - 1)}>이전</button><button disabled={(page + 1) * 20 >= data.total} onClick={() => setPage(n => n + 1)}>다음</button></div>
    </section>}
  </>
}
