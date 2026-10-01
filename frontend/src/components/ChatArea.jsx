import { useEffect, useRef } from 'react'
import WelfareCard from './WelfareCard'

export default function ChatArea({ messages }) {
  const bottomRef = useRef(null)

  useEffect(() => {
    if (messages.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  return (
    <div className="h-full px-[14px] py-[16px] flex flex-col gap-[12px] overflow-y-auto bg-[#F0F4FF] dark:bg-[#0F1120]">
      {messages.map((msg, i) => {
        if (msg.role === 'user') {
          return (
            <div key={i} className="flex justify-end">
              <div className="bg-[#C8D8FF] dark:bg-[#2A3F7F] text-[#1A2340] dark:text-[#E8EEFF] px-[16px] py-[12px] rounded-[18px_18px_4px_18px] max-w-[75%] leading-relaxed"
                style={{ fontSize: '1em' }}>
                <span className="whitespace-pre-wrap break-words">{msg.text}</span>
              </div>
            </div>
          )
        }

        if (msg.role === 'bot') {
          return (
            <div key={i} className="flex flex-col gap-[8px]">
              <div className="flex items-end gap-[8px]">
                <div className="w-[32px] h-[32px] bg-[#E8F0FF] dark:bg-[#2A3050] rounded-full flex items-center justify-center text-[16px] shrink-0">
                  🤖
                </div>
                <div>
                  <div className="bg-white dark:bg-[#1A1F35] text-[#1A2340] dark:text-[#E8EEFF] px-[16px] py-[12px] rounded-[18px_18px_18px_4px] max-w-[75%] leading-relaxed border border-[#E2E8F0] dark:border-[#2A3050]"
                    style={{ fontSize: '1em' }}>
                    <span className="whitespace-pre-wrap break-words">{msg.text}</span>
                  </div>
                </div>
              </div>

              {msg.welfareList && msg.welfareList.length > 0 && (
                <div className="ml-[40px]">
                  <h2 className="font-bold text-[#1A2340] dark:text-[#E8EEFF] mb-[10px] flex items-center gap-[6px]"
                    style={{ fontSize: '1em' }}>
                    ✨ 추천 복지제도 {msg.welfareList.length}건
                  </h2>
                  {msg.welfareList.map((card, j) => (
                    <WelfareCard key={j} {...card} />
                  ))}
                </div>
              )}
            </div>
          )
        }

        if (msg.role === 'loading') {
          return (
            <div key={i} className="flex items-end gap-[8px]">
              <div className="w-[32px] h-[32px] bg-[#E8F0FF] dark:bg-[#2A3050] rounded-full flex items-center justify-center text-[16px] shrink-0">
                🤖
              </div>
              <div className="bg-white dark:bg-[#1A1F35] px-[16px] py-[12px] rounded-[18px_18px_18px_4px] border border-[#E2E8F0] dark:border-[#2A3050]">
                <div className="flex gap-[4px] items-center h-[20px]">
                  <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )
        }

        return null
      })}
      <div ref={bottomRef} />
    </div>
  )
}
