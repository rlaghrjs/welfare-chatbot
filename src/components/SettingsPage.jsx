import { useTheme, FONT_SIZES } from '../context/ThemeContext'

const settingsItems = [
  {
    section: '환경설정',
    items: [
      { icon: '🎨', label: '다크 모드', type: 'toggle' },
      { icon: '📝', label: '글자 크기', type: 'fontsize' },
      { icon: '𝐁', label: '굵은 글씨', type: 'bold' },
    ],
  },
  {
    section: '정보',
    items: [
      { icon: '📋', label: '이용약관', type: 'arrow' },
      { icon: '🔐', label: '개인정보 처리방침', type: 'arrow' },
      { icon: 'ℹ️', label: '앱 버전', value: 'v1.0.0', type: 'value' },
    ],
  },
]

export default function SettingsPage() {
  const { isDark, toggleDark, fontSize, changeFontSize, isBold, toggleBold } = useTheme()

  return (
    <div className="flex flex-col h-full bg-[#F0F4FF] dark:bg-[#0F1120] overflow-y-auto">
      {settingsItems.map((group, gi) => (
        <div key={gi} className="mx-[14px] mb-[8px]">
          <p className="font-bold text-[#8899BB] dark:text-[#5566AA] px-[4px] mb-[6px] mt-[16px]"
            style={{ fontSize: '0.8em' }}>
            {group.section}
          </p>
          <div className="bg-white dark:bg-[#1A1F35] rounded-2xl border border-[#E2E8F0] dark:border-[#2A3050] overflow-hidden">
            {group.items.map((item, ii) => (
              <div
                key={ii}
                className={`w-full flex flex-col px-[16px] py-[14px]
                  ${ii < group.items.length - 1 ? 'border-b border-[#F0F4FF] dark:border-[#2A3050]' : ''}`}
              >
                <div className="flex items-center gap-[12px]">
                  <span className="text-[18px] w-[24px] text-center">{item.icon}</span>
                  <span className="flex-1 text-[#1A2340] dark:text-[#E8EEFF]"
                    style={{ fontSize: '1em' }}>{item.label}</span>

                  {item.type === 'toggle' && (
                    <div
                      onClick={toggleDark}
                      className={`w-[48px] h-[26px] rounded-full flex items-center px-[3px] cursor-pointer transition-colors duration-200
                        ${isDark ? 'bg-[#4A7FFF]' : 'bg-[#CBD5E8]'}`}
                    >
                      <div className={`w-[20px] h-[20px] bg-white rounded-full shadow transition-transform duration-200
                        ${isDark ? 'translate-x-[22px]' : 'translate-x-0'}`} />
                    </div>
                  )}

                  {item.type === 'bold' && (
                    <div
                      onClick={toggleBold}
                      className={`w-[48px] h-[26px] rounded-full flex items-center px-[3px] cursor-pointer transition-colors duration-200
                        ${isBold ? 'bg-[#4A7FFF]' : 'bg-[#CBD5E8]'}`}
                    >
                      <div className={`w-[20px] h-[20px] bg-white rounded-full shadow transition-transform duration-200
                        ${isBold ? 'translate-x-[22px]' : 'translate-x-0'}`} />
                    </div>
                  )}

                  {item.type === 'fontsize' && (
                    <span className="text-[#8899BB] dark:text-[#5566AA]" style={{ fontSize: '0.85em' }}>
                      {FONT_SIZES[fontSize].label}
                    </span>
                  )}

                  {item.type === 'value' && (
                    <span className="text-[#8899BB] dark:text-[#5566AA]" style={{ fontSize: '0.85em' }}>{item.value}</span>
                  )}

                  {item.type === 'arrow' && (
                    <span className="text-[#CBD5E8] dark:text-[#3A4A70] text-[16px]">›</span>
                  )}
                </div>

                {item.type === 'fontsize' && (
                  <div className="flex gap-[8px] mt-[12px] ml-[36px]">
                    {Object.entries(FONT_SIZES).map(([key, val]) => (
                      <button
                        key={key}
                        onClick={() => {
                          changeFontSize(key)
                        }}
                        className={`flex-1 py-[8px] rounded-xl font-medium border transition-colors
                          ${fontSize === key
                            ? 'bg-[#4A7FFF] text-white border-[#4A7FFF]'
                            : 'bg-[#F0F4FF] dark:bg-[#0F1120] text-[#8899BB] dark:text-[#5566AA] border-[#E2E8F0] dark:border-[#2A3050]'
                          }`}
                        style={{ fontSize: '0.85em' }}
                      >
                        {val.label}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
