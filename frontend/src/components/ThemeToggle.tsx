import { useThemeStore, ThemeMode } from '../stores/themeStore'
import { Sun, Moon, Blend } from 'lucide-react'

const icons: Record<ThemeMode, typeof Sun> = { light: Sun, dark: Moon, mix: Blend }
const labels: Record<ThemeMode, string> = { light: 'Light', dark: 'Dark', mix: 'Mix' }

export function ThemeToggle() {
  const { theme, cycleTheme } = useThemeStore()
  const Icon = icons[theme]

  return (
    <button
      onClick={cycleTheme}
      className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium
        bg-surface-tertiary hover:bg-line-hover text-content-secondary hover:text-content-primary
        border border-line transition-all duration-200"
      title={`Theme: ${labels[theme]} — Click to switch`}
    >
      <Icon size={14} />
      <span className="hidden sm:inline">{labels[theme]}</span>
    </button>
  )
}
