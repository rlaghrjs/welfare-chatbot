import { ICON_NAMES } from '../assets/iconNames'
import { LEGACY_ICONS } from '../assets/legacyIcons'

/** name: semantic key or a legacy emoji; decorative unless alt is supplied. */
export default function AppIcon({ name = 'general-welfare', size = 24, alt = '', className = '' }) {
  const resolved = LEGACY_ICONS[name] || name
  const key = ICON_NAMES.includes(resolved) ? resolved : 'general-welfare'
  const base = `${import.meta.env.BASE_URL}icons/welfare/`
  const fallback = `${base}general-welfare.webp`

  return (
    <img
      src={`${base}${key}.webp`}
      alt={alt}
      aria-hidden={alt ? undefined : true}
      width={size}
      height={size}
      className={className}
      draggable={false}
      decoding="async"
      style={{ width: size, height: size, objectFit: 'contain', display: 'inline-block', verticalAlign: 'middle', flexShrink: 0 }}
      onError={event => {
        const image = event.currentTarget
        if (image.src !== new URL(fallback, window.location.href).href) image.src = fallback
        else image.style.visibility = 'hidden'
      }}
    />
  )
}
