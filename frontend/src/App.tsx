import { useEffect, useState } from 'react'
import { Toolbar } from './components/Toolbar'
import { Sidebar } from './components/Sidebar'
import { NotebookView } from './components/NotebookView'
import { ClusterPanel } from './components/ClusterPanel'
import { ResizeHandle } from './components/ResizeHandle'
import { useNotebookStore } from './stores/notebookStore'
import { useThemeStore } from './stores/themeStore'
import { wsService } from './services/websocket'

function useIsMobile() {
  const [mobile, setMobile] = useState(window.innerWidth < 768)
  useEffect(() => {
    const handler = () => setMobile(window.innerWidth < 768)
    window.addEventListener('resize', handler)
    return () => window.removeEventListener('resize', handler)
  }, [])
  return mobile
}

export default function App() {
  const { notebook, sidebarOpen, clusterPanelOpen, appendCellOutput, setCellExecuting, toggleSidebar, toggleClusterPanel } =
    useNotebookStore()
  const { sidebarWidth, clusterPanelWidth, sidebarPosition, clusterPosition, isResizing } = useThemeStore()
  const isMobile = useIsMobile()

  useEffect(() => {
    wsService.connect(notebook.id)
    const unsub = wsService.on('*', (msg: any) => {
      const cellId = msg.cell_id
      if (!cellId) return
      switch (msg.type) {
        case 'stream':
          appendCellOutput(cellId, { type: 'stream', name: msg.name, text: msg.text })
          break
        case 'execute_result':
          appendCellOutput(cellId, { type: 'execute_result', data: msg.data })
          break
        case 'error':
          appendCellOutput(cellId, { type: 'error', ename: msg.ename, evalue: msg.evalue, traceback: msg.traceback })
          setCellExecuting(cellId, false)
          break
        case 'display_data':
          appendCellOutput(cellId, { type: 'display_data', data: msg.data })
          break
        case 'status':
          if (msg.execution_state === 'idle') { setCellExecuting(cellId, false) }
          break
      }
    })
    return () => { unsub(); wsService.disconnect() }
  }, [notebook.id])

  // Build ordered panels
  const panels: JSX.Element[] = []

  const sidebarEl = sidebarOpen ? (
    <div
      key="sidebar"
      className={`relative flex-shrink-0 ${isMobile ? '' : 'panel-slide-left'}`}
      style={isMobile ? {} : { width: sidebarWidth }}
    >
      <Sidebar />
      {!isMobile && (
        <ResizeHandle
          side={sidebarPosition === 'left' ? 'right' : 'left'}
          target="sidebar"
        />
      )}
    </div>
  ) : null

  const clusterEl = clusterPanelOpen ? (
    <div
      key="cluster"
      className={`relative flex-shrink-0 ${isMobile ? '' : 'panel-slide-right'}`}
      style={isMobile ? {} : { width: clusterPanelWidth }}
    >
      <ClusterPanel />
      {!isMobile && (
        <ResizeHandle
          side={clusterPosition === 'right' ? 'left' : 'right'}
          target="cluster"
        />
      )}
    </div>
  ) : null

  // Position panels: left side first, then main, then right side
  const leftPanels: JSX.Element[] = []
  const rightPanels: JSX.Element[] = []

  if (sidebarEl) {
    if (sidebarPosition === 'left') leftPanels.push(sidebarEl)
    else rightPanels.push(sidebarEl)
  }
  if (clusterEl) {
    if (clusterPosition === 'left') leftPanels.push(clusterEl)
    else rightPanels.push(clusterEl)
  }

  // Mobile: use overlay drawers
  if (isMobile) {
    return (
      <div className="h-[100dvh] flex flex-col bg-surface-primary breathing-bg">
        <Toolbar />
        <div className="flex-1 overflow-hidden relative">
          <main className="h-full overflow-y-auto">
            <NotebookView />
          </main>
          {sidebarOpen && (
            <>
              <div className="mobile-overlay" onClick={toggleSidebar} />
              <div className="mobile-drawer from-left" style={{ width: '80vw', maxWidth: 320 }}>
                <Sidebar />
              </div>
            </>
          )}
          {clusterPanelOpen && (
            <>
              <div className="mobile-overlay" onClick={toggleClusterPanel} />
              <div className="mobile-drawer from-right" style={{ width: '85vw', maxWidth: 360 }}>
                <ClusterPanel />
              </div>
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={`h-screen flex flex-col bg-surface-primary breathing-bg ${isResizing ? 'select-none' : ''}`}>
      <Toolbar />
      <div className="flex flex-1 overflow-hidden">
        {leftPanels}
        <main className="flex-1 min-w-0 overflow-y-auto">
          <NotebookView />
        </main>
        {rightPanels}
      </div>
    </div>
  )
}
