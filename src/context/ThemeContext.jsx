import { createContext, useContext, useState } from 'react'

export const FONT_SIZES = {
  small:  { label: '작게', base: '13px' },
  medium: { label: '보통', base: '15px' },
  large:  { label: '크게', base: '21px' },
}

const ThemeContext = createContext()

export function ThemeProvider({ children }) {
  const [isDark, setIsDark] = useState(false)
  const [fontSize, setFontSize] = useState('medium')
  const [isBold, setIsBold] = useState(false)

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
