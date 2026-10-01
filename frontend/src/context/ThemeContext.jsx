import { createContext, useContext, useEffect, useState } from 'react'

export const FONT_SIZES = {
  small:  { label: '작게', base: '13px' },
  medium: { label: '보통', base: '15px' },
  large:  { label: '크게', base: '21px' },
}

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(() => localStorage.getItem('welfareDark') === 'true')
  const [fontSize, setFontSize] = useState(() => {
    const saved = localStorage.getItem('welfareFontSize')
    return Object.hasOwn(FONT_SIZES, saved) ? saved : 'medium'
  })
  const [isBold, setIsBold] = useState(() => localStorage.getItem('welfareBold') === 'true')

  useEffect(() => {
    localStorage.setItem('welfareDark', String(isDark))
    localStorage.setItem('welfareFontSize', fontSize)
    localStorage.setItem('welfareBold', String(isBold))
  }, [isDark, fontSize, isBold])

  const toggleDark = () => setIsDark(prev => !prev)
  const changeFontSize = (size) => setFontSize(size)
  const toggleBold = () => setIsBold(prev => !prev)

  return (
    <ThemeContext.Provider value={{ isDark, toggleDark, fontSize, changeFontSize, isBold, toggleBold }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
