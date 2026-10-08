import AppIcon from './AppIcon'
const navItems = [
  { icon: 'home', label: '홈' },
  { icon: 'chat', label: '채팅' },
  { icon: 'settings', label: '설정' },
]

export default function BottomNav({ activeTab, onTabChange }) {
  return (
    <nav className="bg-white dark:bg-[#1A1F35] border-t border-[#E2E8F0] dark:border-[#2A3050] flex">
      {navItems.map((item, i) => (
        <button
          key={i}
          onClick={() => onTabChange(i)}
          className="flex-1 flex flex-col items-center gap-[3px] py-[10px] pb-[12px] bg-transparent border-none cursor-pointer"
        >
          <span className="text-[20px]"><AppIcon name={item.icon} size={24} /></span>
          <span className={`text-[11px] ${activeTab === i ? 'text-[#4A7FFF] font-bold' : 'text-[#8899BB] dark:text-[#5566AA]'}`}>
            {item.label}
          </span>
        </button>
      ))}
    </nav>
  )
}
