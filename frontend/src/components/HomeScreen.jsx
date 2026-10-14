import AppIcon from './AppIcon'
import { useTheme } from '../context/ThemeContext'

const recommendCards = [
  {
    icon: 'home',
    bg: '#E8F0FF',
    darkBg: '#1E2D5A',
    title: '청년 주거 지원',
    desc: '월세·전세 지원부터\n공공임대까지',
    query: '청년 주거 지원 알려줘',
  },
  {
    icon: 'childcare',
    bg: '#E0F5EC',
    darkBg: '#1A3D2E',
    title: '육아 복지 제도',
    desc: '아이돌봄·육아휴직\n지원금 한눈에',
    query: '육아 관련 복지 뭐 있어?',
  },
  {
    icon: 'health',
    bg: '#FFF0E8',
    darkBg: '#3D2A1A',
    title: '노인 의료 지원',
    desc: '건강보험·틀니\n임플란트 지원',
    query: '노인 의료 지원 제도는?',
  },
  {
    icon: 'accessibility',
    bg: '#EDE8FF',
    darkBg: '#2A1F4A',
    title: '장애인 복지 서비스',
    desc: '활동지원·보조기기\n지원 서비스',
    query: '장애인 복지 서비스 알려줘',
  },
]

export default function HomeScreen({ onSend, disabled }) {
  const { isDark } = useTheme()

  return (
    <div className="flex flex-col h-full px-[16px] py-[20px] overflow-y-auto bg-[#F0F4FF] dark:bg-[#0F1120]" style={{ justifyContent: 'safe center' }}>
      <div className="flex flex-col items-center gap-[10px] mb-[28px] mt-[8px]">
        <div className="w-[68px] h-[68px] bg-[#E8F0FF] dark:bg-[#2A3050] rounded-2xl flex items-center justify-center text-[38px]">
          <AppIcon name="robot" size={60} />
        </div>
        <h2 className="font-bold text-[#1A2340] dark:text-[#E8EEFF]" style={{ fontSize: '1.2em' }}>
          무엇이 궁금한가요?
        </h2>
        <p className="text-[#8899BB] dark:text-[#5566AA] text-center leading-relaxed" style={{ fontSize: '0.9em' }}>
          복지제도에 대해 무엇이든 물어보세요
        </p>
      </div>

      <div className="mb-[16px]">
        <p className="font-bold text-[#4A5A7A] dark:text-[#8899BB] mb-[12px] flex items-center gap-[6px]"
          style={{ fontSize: '0.9em' }}>
          <AppIcon name="recommendation" size={20} /> 추천 복지제도
        </p>
        <div className="grid grid-cols-2 gap-[10px]">
          {recommendCards.map((card, i) => (
            <button
              key={i}
              disabled={disabled}
              onClick={() => onSend(card.query)}
              className="bg-white dark:bg-[#1A1F35] rounded-2xl p-[16px] border border-[#E2E8F0] dark:border-[#2A3050] text-left active:scale-[0.97] transition-transform shadow-sm"
            >
              <div
                className="w-[44px] h-[44px] rounded-xl flex items-center justify-center text-[24px] mb-[10px]"
                style={{ background: isDark ? card.darkBg : card.bg }}
              >
                <AppIcon name={card.icon} size={38} />
              </div>
              <p className="font-bold text-[#1A2340] dark:text-[#E8EEFF] mb-[4px] leading-tight"
                style={{ fontSize: '0.9em' }}>
                {card.title}
              </p>
              <p className="text-[#8899BB] dark:text-[#5566AA] leading-snug whitespace-pre-line"
                style={{ fontSize: '0.8em' }}>
                {card.desc}
              </p>
            </button>
          ))}
        </div>
      </div>

      <p className="text-center text-[#AAB8D4] dark:text-[#445577] mt-[4px]" style={{ fontSize: '0.8em' }}>
        또는 아래 입력창에 직접 질문해보세요 <AppIcon name="chat" size={20} />
      </p>
    </div>
  )
}
