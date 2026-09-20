import { useState } from 'react'
import Header from './components/Header'
import HomeScreen from './components/HomeScreen'
import ChatArea from './components/ChatArea'
import ChatList from './components/ChatList'
import InputBar from './components/InputBar'
import BottomNav from './components/BottomNav'
import SettingsPage from './components/SettingsPage'
import { useTheme, FONT_SIZES } from './context/ThemeContext'
import { sendMessage, getSessionDetail, setCurrentSessionId } from './api/welfare'

export default function App() {
  const { isDark, fontSize, isBold } = useTheme()
  const [activeTab, setActiveTab] = useState(0)
  const [messages, setMessages] = useState([])
  const [isChatting, setIsChatting] = useState(false)
  const [chatAnimating, setChatAnimating] = useState(false)
  const [isLoading, setIsLoading] = useState(false)

  const handleTabChange = (i) => setActiveTab(i)

  const handleSend = async (text) => {
    if (!text.trim() || isLoading) return

    const userMsg = { role: 'user', text }

    if (!isChatting) {
      setChatAnimating(true)
      setTimeout(() => {
        setIsChatting(true)
        setChatAnimating(false)
        setMessages([userMsg, { role: 'loading' }])
      }, 400)
    } else {
      setMessages(prev => [...prev, userMsg, { role: 'loading' }])
    }

    setIsLoading(true)

    try {
      const response = await sendMessage(text)
      setMessages(prev => [
        ...prev.filter(m => m.role !== 'loading'),
        { role: 'bot', text: response.reply, welfareList: response.welfareList },
      ])
    } catch (err) {
      setMessages(prev => [
        ...prev.filter(m => m.role !== 'loading'),
        { role: 'bot', text: '죄송해요, 잠시 문제가 발생했어요. 다시 시도해주세요.' },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectSession = async (sessionId) => {
    try {
      const { messages: prevMessages } = await getSessionDetail(sessionId)
      setCurrentSessionId(sessionId)
      setMessages(prevMessages)
      setIsChatting(true)
      setActiveTab(0)
    } catch (err) {
      console.error('세션 불러오기 실패', err)
    }
  }

  const goHome = () => {
    setIsChatting(false)
    setMessages([])
    setCurrentSessionId(null)
  }

  const getTranslateX = (tabIndex) => {
    if (tabIndex === activeTab) return 'translateX(0)'
    if (tabIndex < activeTab) return 'translateX(-100%)'
    return 'translateX(100%)'
  }

  const tabs = [
    <div key="home" className="relative h-full overflow-hidden">
      <div
        className="absolute inset-0 transition-transform ease-in-out"
        style={{
          transform: chatAnimating || isChatting ? 'translateY(-100%)' : 'translateY(0)',
          transitionDuration: '0.4s',
        }}
      >
        <HomeScreen onSend={handleSend} />
      </div>
      <div
        className="absolute inset-0 transition-transform ease-in-out"
        style={{
          transform: !isChatting && !chatAnimating ? 'translateY(100%)' : 'translateY(0)',
          transitionDuration: '0.4s',
        }}
      >
        <ChatArea messages={messages} />
      </div>
    </div>,

    <ChatList key="chatlist" onSelectSession={handleSelectSession} isActive={activeTab === 1} />,
    <SettingsPage key="settings" />,
  ]

  return (
    <div
      className={`${isDark ? 'dark' : ''} flex flex-col h-screen max-w-[390px] mx-auto bg-[#F0F4FF] dark:bg-[#0F1120] font-['Noto_Sans_KR'] overflow-hidden relative`}
      style={{
        fontSize: FONT_SIZES[fontSize]?.base,
        fontWeight: isBold ? '700' : '400',
      }}
    >
      <div className="shrink-0">
        <Header />
      </div>

      <div className="flex-1 relative overflow-hidden">
        {tabs.map((tab, i) => (
          <div
            key={i}
            className="absolute inset-0 transition-transform ease-in-out overflow-hidden"
            style={{
              transform: getTranslateX(i),
              transitionDuration: '0.4s',
            }}
          >
            {tab}
          </div>
        ))}
      </div>

      <div className="shrink-0">
        {activeTab === 0 && <InputBar onSend={handleSend} isLoading={isLoading} />}
        <BottomNav
          activeTab={activeTab}
          onTabChange={(i) => {
            handleTabChange(i)
            if (i === 0) goHome()
          }}
        />
      </div>
    </div>
  )
}
