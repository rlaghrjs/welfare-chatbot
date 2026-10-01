const tagStyles = {
  blue:   { bg: 'bg-[#E0EAFF] dark:bg-[#1E2D5A]', text: 'text-[#3560CC] dark:text-[#7A9FFF]' },
  green:  { bg: 'bg-[#E0F5EC] dark:bg-[#1A3D2E]', text: 'text-[#1A7A50] dark:text-[#4ACC8A]' },
  purple: { bg: 'bg-[#EDE8FF] dark:bg-[#2A1F4A]', text: 'text-[#6040CC] dark:text-[#A080FF]' },
}

const checkColors = {
  blue:   'bg-[#4A7FFF]',
  green:  'bg-[#1A9A60]',
  orange: 'bg-[#FF8C42]',
}

export default function WelfareCard({ icon, iconBg, title, tag, tagColor, checkColor, items, link, source }) {
  const tagStyle = tagStyles[tagColor] || tagStyles.blue
  const checkBg = checkColors[checkColor] || checkColors.blue

  return (
    <a
      href={link || undefined} target="_blank" rel="noopener noreferrer"
      className="bg-white dark:bg-[#1A1F35] rounded-2xl p-[14px] flex items-center gap-3 border border-[#E2E8F0] dark:border-[#2A3050] mb-[10px] cursor-pointer active:scale-[0.98] transition-transform"
    >
      <div
        className="w-[52px] h-[52px] rounded-[14px] flex items-center justify-center text-[26px] shrink-0"
        style={{ background: iconBg || '#E8F0FF' }}
      >
        {icon}
      </div>

      <div className="flex-1 min-w-0">
        {source && <span className="text-[11px] text-[#8899BB] dark:text-[#8899BB]">{source}</span>}
        <div className="flex items-center gap-[6px] mb-[6px] flex-wrap">
          <span className="font-bold text-[#1A2340] dark:text-[#E8EEFF]" style={{ fontSize: '1em' }}>{title}</span>
          <span className={`px-[8px] py-[3px] rounded-full font-medium whitespace-nowrap ${tagStyle.bg} ${tagStyle.text}`}
            style={{ fontSize: '0.75em' }}>
            {tag}
          </span>
        </div>

        <div className="flex flex-col gap-[3px]">
          {items.map((item, i) => (
            <div key={i} className="flex items-center gap-[5px] text-[#4A5A7A] dark:text-[#8899BB]"
              style={{ fontSize: '0.85em' }}>
              <span className={`w-[14px] h-[14px] rounded-full flex items-center justify-center text-[9px] text-white shrink-0 ${checkBg}`}>
                ✓
              </span>
              {item}
            </div>
          ))}
        </div>
      </div>

      <span className="text-[#CBD5E8] dark:text-[#3A4A70] text-[18px] shrink-0">›</span>
    </a>
  )
}
