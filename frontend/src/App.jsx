import { useEffect, useRef, useState } from 'react'
import Header from './components/Header'
import HomeScreen from './components/HomeScreen'
import ChatArea from './components/ChatArea'
import ChatList from './components/ChatList'
import InputBar from './components/InputBar'
import BottomNav from './components/BottomNav'
import SettingsPage from './components/SettingsPage'
import { useTheme, FONT_SIZES } from './context/ThemeContext'
import { sendMessage, getChatList, getSessionDetail, getCurrentSessionId, setCurrentSessionId, deleteSession } from './api/welfare'

export default function App() {
  const { isDark, fontSize, isBold } = useTheme()
  const [activeTab, setActiveTab] = useState(0)
  const [messages, setMessages] = useState([])
  const [isChatting, setIsChatting] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [ready, setReady] = useState(false)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [listRevision, setListRevision] = useState(0)
  const busyRef = useRef(false)

  useEffect(() => {
    let active = true
    async function restore() {
      try {
        await getChatList() // Also registers the persisted anonymous installation.
        const id = getCurrentSessionId()
        if (id) {
          try {
            const data = await getSessionDetail(id)
            if (active) { setMessages(data.messages); setIsChatting(true) }
          } catch (e) {
            if (e.status === 404) setCurrentSessionId(null)
            else throw e
          }
        }
        if (active) { setReady(true); setError('') }
      } catch (e) { if (active) setError(e.message || '앱에 연결하지 못했어요.') }
    }
    restore()
    return () => { active = false }
  }, [attempt])

  const handleSend = async (text) => {
    if (!ready || busyRef.current || !text.trim()) return
    busyRef.current = true
    setIsLoading(true); setIsChatting(true); setError('')
    // Update immediately: a fast response must not be overwritten by the animation timer.
    setMessages(prev => [...prev, { role: 'user', text: text.trim() }, { role: 'loading' }])
    try {
      const response = await sendMessage(text.trim())
      setMessages(prev => [...prev.filter(m => m.role !== 'loading'), { role: 'bot', text: response.reply, welfareList: response.welfareList }])
      setListRevision(n => n + 1)
    } catch (e) {
      if (e.status === 404) { setCurrentSessionId(null); setError('이 대화가 삭제되었어요. 새 대화를 시작해주세요.') }
      setMessages(prev => [...prev.filter(m => m.role !== 'loading'), { role: 'bot', text: e.message || '잠시 문제가 발생했어요. 다시 시도해주세요.' }])
    } finally { busyRef.current = false; setIsLoading(false) }
  }

  const handleSelectSession = async (id) => {
    if (!ready || busyRef.current) return
    busyRef.current = true; setIsLoading(true); setError('')
    try {
      const data = await getSessionDetail(id)
      setCurrentSessionId(data.sessionId); setMessages(data.messages)
      setIsChatting(true); setActiveTab(0)
    } catch (e) { setError(e.message || '대화를 불러오지 못했어요.') }
    finally { busyRef.current = false; setIsLoading(false) }
  }

  const goHome = () => {
    if (busyRef.current) return
    setIsChatting(false); setMessages([]); setCurrentSessionId(null); setError(''); setActiveTab(0)
  }

  const handleDelete = async (id) => {
    if (busyRef.current || !window.confirm('이 채팅 기록을 삭제할까요? 관심 조건은 유지됩니다.')) return
    const current = getCurrentSessionId() === id
    busyRef.current = true; setIsLoading(true)
    try {
      await deleteSession(id)
      if (current) { setMessages([]); setIsChatting(false) }
      setListRevision(n => n + 1); setError('')
    } catch (e) { setError(e.message || '기록 삭제에 실패했어요.') }
    finally { busyRef.current = false; setIsLoading(false) }
  }

  const tabs = [
    <div key="home" className="relative h-full overflow-hidden">
      <div inert={isChatting} className="absolute inset-0 transition-transform ease-in-out" style={{ transform: isChatting ? 'translateY(-100%)' : 'translateY(0)', transitionDuration: '0.4s' }}>
        <HomeScreen onSend={handleSend} disabled={!ready || isLoading} />
      </div>
      <div inert={!isChatting} className="absolute inset-0 transition-transform ease-in-out" style={{ transform: isChatting ? 'translateY(0)' : 'translateY(100%)', transitionDuration: '0.4s' }}>
        <ChatArea messages={messages} />
      </div>
    </div>,
    <ChatList key="chatlist" onSelectSession={handleSelectSession} onDeleteSession={handleDelete} isActive={activeTab === 1 && ready} revision={listRevision} disabled={isLoading} />,
    <SettingsPage key="settings" isActive={activeTab === 2} busy={isLoading || !ready} />,
  ]

  return (
    <div className={`${isDark ? 'dark' : ''} flex flex-col h-screen h-[100dvh] max-w-[390px] mx-auto bg-[#F0F4FF] dark:bg-[#0F1120] font-['Noto_Sans_KR'] overflow-hidden relative`}
      style={{ fontSize: FONT_SIZES[fontSize]?.base, fontWeight: isBold ? '700' : '400' }}>
      <div className="shrink-0"><Header onNewChat={isChatting ? goHome : undefined} disabled={isLoading || !ready} /></div>
      {(!ready || error) && <div role={error ? 'alert' : 'status'} className="px-[14px] py-[10px] text-[13px] text-[#4A5A7A] dark:text-[#E8EEFF] bg-white dark:bg-[#1A1F35]">
        {error || '앱에 연결하는 중이에요…'}
        {!ready && error && <button className="ml-2 text-[#4A7FFF] underline" onClick={() => { setError(''); setAttempt(n => n + 1) }}>다시 연결</button>}
        {ready && error && <button className="ml-2 text-[#4A7FFF]" onClick={() => setError('')}>닫기</button>}
      </div>}
      <div className="flex-1 relative overflow-hidden">
        {tabs.map((tab, i) => <div key={i} inert={i !== activeTab} className="absolute inset-0 transition-transform ease-in-out overflow-hidden"
          style={{ transform: i === activeTab ? 'translateX(0)' : i < activeTab ? 'translateX(-100%)' : 'translateX(100%)', transitionDuration: '0.4s' }}>{tab}</div>)}
      </div>
      <div className="shrink-0">
        {activeTab === 0 && <InputBar onSend={handleSend} isLoading={isLoading || !ready} />}
        <BottomNav activeTab={activeTab} onTabChange={setActiveTab} />
      </div>
    </div>
  )
}
