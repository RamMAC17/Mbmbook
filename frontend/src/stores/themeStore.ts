import { create } from 'zustand'

export type ThemeMode = 'light' | 'dark' | 'mix'
export type SidebarPosition = 'left' | 'right'

interface ThemeState {
  theme: ThemeMode
  sidebarWidth: number
  clusterPanelWidth: number
  sidebarPosition: SidebarPosition
  clusterPosition: SidebarPosition
  isResizing: boolean

  setTheme: (theme: ThemeMode) => void
  cycleTheme: () => void
  setSidebarWidth: (w: number) => void
  setClusterPanelWidth: (w: number) => void
  setSidebarPosition: (p: SidebarPosition) => void
  setClusterPosition: (p: SidebarPosition) => void
  setIsResizing: (r: boolean) => void
}

const THEME_KEY = 'mbmbook-theme'
const SIDEBAR_W_KEY = 'mbmbook-sidebar-w'
const CLUSTER_W_KEY = 'mbmbook-cluster-w'
const SIDEBAR_POS_KEY = 'mbmbook-sidebar-pos'
const CLUSTER_POS_KEY = 'mbmbook-cluster-pos'

function loadTheme(): ThemeMode {
  const saved = localStorage.getItem(THEME_KEY) as ThemeMode | null
  return saved && ['light', 'dark', 'mix'].includes(saved) ? saved : 'dark'
}

function loadNumber(key: string, fallback: number): number {
  const v = localStorage.getItem(key)
  return v ? Math.max(180, Math.min(600, parseInt(v, 10) || fallback)) : fallback
}

function loadPos(key: string, fallback: SidebarPosition): SidebarPosition {
  const v = localStorage.getItem(key) as SidebarPosition | null
  return v === 'left' || v === 'right' ? v : fallback
}

function applyThemeClass(theme: ThemeMode) {
  const html = document.documentElement
  html.classList.remove('light', 'dark', 'mix')
  html.classList.add(theme)
}

export const useThemeStore = create<ThemeState>((set, get) => {
  const initial = loadTheme()
  applyThemeClass(initial)

  return {
    theme: initial,
    sidebarWidth: loadNumber(SIDEBAR_W_KEY, 260),
    clusterPanelWidth: loadNumber(CLUSTER_W_KEY, 300),
    sidebarPosition: loadPos(SIDEBAR_POS_KEY, 'left'),
    clusterPosition: loadPos(CLUSTER_POS_KEY, 'right'),
    isResizing: false,

    setTheme: (theme) => {
      applyThemeClass(theme)
      localStorage.setItem(THEME_KEY, theme)
      set({ theme })
    },

    cycleTheme: () => {
      const order: ThemeMode[] = ['dark', 'mix', 'light']
      const cur = get().theme
      const next = order[(order.indexOf(cur) + 1) % order.length]
      get().setTheme(next)
    },

    setSidebarWidth: (w) => {
      const clamped = Math.max(180, Math.min(480, w))
      localStorage.setItem(SIDEBAR_W_KEY, String(clamped))
      set({ sidebarWidth: clamped })
    },

    setClusterPanelWidth: (w) => {
      const clamped = Math.max(220, Math.min(520, w))
      localStorage.setItem(CLUSTER_W_KEY, String(clamped))
      set({ clusterPanelWidth: clamped })
    },

    setSidebarPosition: (p) => {
      localStorage.setItem(SIDEBAR_POS_KEY, p)
      set({ sidebarPosition: p })
    },

    setClusterPosition: (p) => {
      localStorage.setItem(CLUSTER_POS_KEY, p)
      set({ clusterPosition: p })
    },

    setIsResizing: (r) => set({ isResizing: r }),
  }
})
