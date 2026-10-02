import NotificationsPanel from './NotificationsPanel'
import { useTheme } from '../context/ThemeContext'

export default function Header({ onNewChat, disabled, ready }) {
  const { isDark, toggleDark } = useTheme()

  return (
    <header className="bg-white dark:bg-[#1A1F35] px-[18px] py-[14px] flex items-center gap-[10px] border-b border-[#E2E8F0] dark:border-[#2A3050]">
      <div className="w-[42px] h-[42px] bg-[#E8F0FF] dark:bg-[#2A3050] rounded-xl flex items-center justify-center text-[22px]">
        🤖
      </div>
      <div className="flex-1">
        <h1 className="text-[16px] font-bold text-[#1A2340] dark:text-[#E8EEFF] m-0">복지제도 안내 챗봇</h1>
      </div>
      <NotificationsPanel ready={ready} />
      <button
        aria-label={isDark ? '라이트 모드로 변경' : '다크 모드로 변경'}
        onClick={toggleDark}
        className="w-[36px] h-[36px] rounded-full bg-[#F0F4FF] dark:bg-[#2A3050] flex items-center justify-center text-[18px]"
      >
        {isDark ? '🌙' : '☀️'}
      </button>
      {onNewChat && <button onClick={onNewChat} disabled={disabled} className="text-[12px] text-[#4A7FFF] dark:text-[#7A9FFF] disabled:opacity-40 whitespace-nowrap">새 대화</button>}
    </header>
  )
}
