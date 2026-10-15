import { useEffect, useState } from 'react'
import { Loader2, Square, Volume2 } from 'lucide-react'
import { synthesizeSpeech } from '../api/welfare'

// 말하기 속도: 1.0 = 기본, 1.2 = 조금 빠르게, 1.5 = 빠르게 (0.5 ~ 2.0 권장)
const PLAYBACK_RATE = 1.2

// One item plays at a time; each button subscribes to this shared player.
const audioCache = new Map()
const listeners = new Set()
let current = { id: null, status: 'idle', audio: null }

function setCurrent(next) {
  current = next
  listeners.forEach(listener => listener(current))
}

function stop() {
  current.audio?.pause()
  setCurrent({ id: null, status: 'idle', audio: null })
}

async function play(id, text) {
  stop()
  setCurrent({ id, status: 'loading', audio: null })
  try {
    if (!audioCache.has(text)) audioCache.set(text, URL.createObjectURL(await synthesizeSpeech(text)))
    if (current.id !== id) return
    const audio = new Audio(audioCache.get(text))
    audio.playbackRate = PLAYBACK_RATE
    audio.onended = () => current.audio === audio && stop()
    audio.onerror = () => current.audio === audio && stop()
    setCurrent({ id, status: 'playing', audio })
    await audio.play()
  } catch (error) {
    if (current.id === id) stop()
    alert(error.message || '음성을 재생하지 못했습니다.')
  }
}

let nextId = 0

export default function SpeakButton({ text, label: idleLabel = '읽어주기' }) {
  const [id] = useState(() => ++nextId)
  const [state, setState] = useState(current)

  useEffect(() => {
    listeners.add(setState)
    return () => {
      listeners.delete(setState)
      if (current.id === id) stop()
    }
  }, [id])

  const status = state.id === id ? state.status : 'idle'
  const label = status === 'idle' ? idleLabel : '읽기 멈추기'

  return (
    <button
      type="button"
      onClick={event => {
        event.stopPropagation()
        if (status === 'idle') play(id, text)
        else stop()
      }}
      aria-label={label}
      title={label}
      className={`w-[36px] h-[36px] shrink-0 rounded-full flex items-center justify-center border transition-colors active:scale-95 ${
        status === 'idle'
          ? 'bg-white dark:bg-[#1A1F35] text-[#4A7FFF] border-[#E2E8F0] dark:border-[#2A3050] hover:bg-[#E8F0FF] dark:hover:bg-[#2A3050]'
          : 'bg-[#4A7FFF] text-white border-[#4A7FFF]'
      }`}
    >
      {status === 'loading' && <Loader2 size={20} className="animate-spin" />}
      {status === 'playing' && <Square size={16} fill="currentColor" />}
      {status === 'idle' && <Volume2 size={22} />}
    </button>
  )
}
