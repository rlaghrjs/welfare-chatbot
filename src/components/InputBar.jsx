import { useState, useRef } from 'react'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function InputBar({ onSend, isLoading = false }) {
  const [value, setValue] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream)
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      mediaRecorder.onstop = async () => {
        // 스트림 종료
        stream.getTracks().forEach(track => track.stop())

        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        setIsTranscribing(true)

        try {
          const formData = new FormData()
          formData.append('file', blob, 'recording.webm')

          const res = await fetch(`${BASE_URL}/api/stt/transcribe`, {
            method: 'POST',
            body: formData,
          })
          const data = await res.json()
          console.log('STT 응답:', data) // 응답 구조 확인용
          const text = typeof data === 'string' ? data : data.text || data.transcript || data.result || ''
          if (text) setValue(text)
        } catch (err) {
          alert('음성 인식에 실패했어요. 다시 시도해주세요.')
        } finally {
          setIsTranscribing(false)
        }
      }

      mediaRecorder.start()
      setIsRecording(true)
    } catch (err) {
      alert('마이크 권한을 허용해주세요.')
    }
  }

  const stopRecording = () => {
    mediaRecorderRef.current?.stop()
    setIsRecording(false)
  }

  const handleMic = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="bg-white dark:bg-[#1A1F35] px-[14px] py-[12px] flex items-center gap-[10px] border-t border-[#E2E8F0] dark:border-[#2A3050]">

      <input
        className="flex-1 bg-[#F5F7FF] dark:bg-[#0F1120] border border-[#E2E8F0] dark:border-[#2A3050] rounded-full px-[16px] py-[10px] text-[13px] text-[#1A2340] dark:text-[#E8EEFF] outline-none focus:border-[#4A7FFF] placeholder:text-[#8899BB] dark:placeholder:text-[#445577]"
        type="text"
        placeholder={isRecording ? '녹음 중...' : isTranscribing ? '변환 중...' : '궁금한 복지제도를 입력해보세요...'}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />

      <button
        onClick={handleMic}
        disabled={isTranscribing}
        className={`w-[38px] h-[38px] rounded-full flex items-center justify-center cursor-pointer shrink-0 transition-all active:scale-95
          ${isRecording ? 'bg-red-500 animate-pulse' : isTranscribing ? 'bg-[#E2E8F0] dark:bg-[#2A3050]' : 'bg-[#F0F4FF] dark:bg-[#2A3050] border border-[#C8D8FF] dark:border-[#3A4A70]'}`}
      >
        {isRecording ? (
          // 녹음 중 - 정지 아이콘
          <svg width="14" height="14" viewBox="0 0 24 24" fill="white">
            <rect x="4" y="4" width="16" height="16" rx="2" />
          </svg>
        ) : isTranscribing ? (
          // 변환 중 - 로딩 점
          <div className="flex gap-[2px]">
            <span className="w-1 h-1 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
            <span className="w-1 h-1 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
            <span className="w-1 h-1 bg-[#4A7FFF] rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
          </div>
        ) : (
          // 기본 - 마이크 아이콘
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <rect x="9" y="2" width="6" height="11" rx="3" fill="#4A7FFF" />
            <path d="M5 10C5 10 5 16 12 16C19 16 19 10 19 10" stroke="#4A7FFF" strokeWidth="2" strokeLinecap="round" />
            <line x1="12" y1="16" x2="12" y2="20" stroke="#4A7FFF" strokeWidth="2" strokeLinecap="round" />
            <line x1="9" y1="20" x2="15" y2="20" stroke="#4A7FFF" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )}
      </button>

      <button
        onClick={() => { if (!isLoading && value.trim()) { onSend(value); setValue('') } }}
        className="w-[38px] h-[38px] rounded-full bg-[#4A7FFF] flex items-center justify-center cursor-pointer shrink-0 active:scale-95 transition-transform"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" />
          <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
    </div>
  )
}