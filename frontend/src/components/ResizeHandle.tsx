import { useCallback, useRef } from 'react'
import { useThemeStore } from '../stores/themeStore'

interface Props {
  side: 'left' | 'right'
  target: 'sidebar' | 'cluster'
}

export function ResizeHandle({ side, target }: Props) {
  const { sidebarWidth, clusterPanelWidth, setSidebarWidth, setClusterPanelWidth, setIsResizing } = useThemeStore()
  const startRef = useRef({ x: 0, width: 0 })

  const getWidth = () => target === 'sidebar' ? sidebarWidth : clusterPanelWidth
  const setWidth = target === 'sidebar' ? setSidebarWidth : setClusterPanelWidth

  const onPointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault()
    e.stopPropagation()
    startRef.current = { x: e.clientX, width: getWidth() }
    setIsResizing(true)

    const onPointerMove = (ev: PointerEvent) => {
      const delta = ev.clientX - startRef.current.x
      // If handle is on the right side of panel, dragging right = wider
      // If handle is on the left side of panel, dragging left = wider
      const newWidth = side === 'right'
        ? startRef.current.width + delta
        : startRef.current.width - delta
      setWidth(newWidth)
    }

    const onPointerUp = () => {
      document.removeEventListener('pointermove', onPointerMove)
      document.removeEventListener('pointerup', onPointerUp)
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      setIsResizing(false)
    }

    document.addEventListener('pointermove', onPointerMove)
    document.addEventListener('pointerup', onPointerUp)
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
  }, [side, target, getWidth, setWidth])

  return (
    <div
      className={`resize-handle group/rh absolute top-0 bottom-0 z-20 w-[5px] cursor-col-resize
        ${side === 'right' ? '-right-[2px]' : '-left-[2px]'}
        hover:bg-accent/40 active:bg-accent/60 transition-colors`}
      onPointerDown={onPointerDown}
    >
      <div className={`absolute top-1/2 -translate-y-1/2 ${side === 'right' ? '-right-[1px]' : '-left-[1px]'}
        w-[3px] h-8 rounded-full bg-content-muted/0 group-hover/rh:bg-accent/60 transition-colors`} />
    </div>
  )
}
