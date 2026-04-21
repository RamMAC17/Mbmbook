import { useRef } from 'react'
import { Plus, RotateCcw, Save, Download, PanelLeftClose, PanelLeftOpen, Server, Upload } from 'lucide-react'
import { useNotebookStore } from '../stores/notebookStore'
import { ThemeToggle } from './ThemeToggle'
import { AnimatedTitle } from './AnimatedTitle'
import { api } from '../services/api'

export function Toolbar() {
  const fileInputRef = useRef<HTMLInputElement | null>(null)
  const {
    notebook, sidebarOpen, clusterPanelOpen, addCell, clearAllOutputs,
    setNotebookTitle, toggleSidebar, toggleClusterPanel,
    saveNotebook, downloadNotebook,
  } = useNotebookStore()

  async function handleUploadFiles(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return

    try {
      const result = await api.uploadNotebookFiles(notebook.id, fileList)
      const uploaded = Array.isArray(result?.uploaded) ? result.uploaded : []

      if (uploaded.length > 0) {
        const message = [
          `Uploaded ${uploaded.length} file(s).`,
          '',
          'Use these paths in Python code:',
          ...uploaded.map((f: { path: string }) => f.path),
        ].join('\n')
        window.alert(message)
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'File upload failed'
      window.alert(`Upload failed: ${message}`)
    } finally {
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  return (
    <header className="bg-surface-secondary border-b border-line px-2 sm:px-4 py-2 flex items-center gap-2 sm:gap-3 transition-theme flex-shrink-0">
      {/* Sidebar toggle */}
      <button onClick={toggleSidebar}
        className="p-1.5 rounded-md hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors"
        title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}>
        {sidebarOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
      </button>

      {/* Animated logo & title */}
      <AnimatedTitle />

      {/* Notebook title input */}
      <input
        type="text"
        value={notebook.title}
        onChange={(e) => setNotebookTitle(e.target.value)}
        className="bg-transparent border border-transparent hover:border-line focus:border-accent
          rounded-md px-2 py-1 text-sm text-content-primary outline-none
          min-w-0 w-32 sm:w-48 md:min-w-[200px] transition-colors"
      />

      <div className="flex-1" />

      {/* Actions */}
      <div className="flex items-center gap-1">
        {/* Add cell buttons - hide on smallest screens */}
        <div className="hidden sm:flex items-center gap-1">
          <button onClick={() => addCell(undefined, 'code')}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium
              bg-surface-tertiary hover:bg-line-hover text-content-secondary hover:text-content-primary
              border border-line transition-colors"
            title="Add code cell">
            <Plus size={14} /> <span className="hidden md:inline">Code</span>
          </button>
          <button onClick={() => addCell(undefined, 'markdown')}
            className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium
              bg-surface-tertiary hover:bg-line-hover text-content-secondary hover:text-content-primary
              border border-line transition-colors"
            title="Add markdown cell">
            <Plus size={14} /> <span className="hidden md:inline">Markdown</span>
          </button>
          <div className="w-px h-5 bg-line mx-0.5" />
        </div>

        {/* Utility buttons */}
        <button onClick={clearAllOutputs}
          className="p-1.5 rounded-md hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors"
          title="Clear all outputs">
          <RotateCcw size={15} />
        </button>
        <button onClick={() => saveNotebook()}
          className="p-1.5 rounded-md hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors hidden sm:flex"
          title="Save notebook">
          <Save size={15} />
        </button>
        <button onClick={() => downloadNotebook()}
          className="p-1.5 rounded-md hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors hidden md:flex"
          title="Download notebook (.ipynb)">
          <Download size={15} />
        </button>
        <button onClick={() => fileInputRef.current?.click()}
          className="p-1.5 rounded-md hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors hidden md:flex"
          title="Upload files for notebook execution">
          <Upload size={15} />
        </button>
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          multiple
          onChange={(e) => void handleUploadFiles(e.target.files)}
        />

        <div className="w-px h-5 bg-line mx-0.5 hidden sm:block" />

        {/* Theme toggle */}
        <ThemeToggle />

        <div className="w-px h-5 bg-line mx-0.5" />

        {/* Cluster toggle */}
        <button onClick={toggleClusterPanel}
          className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-md text-xs font-medium transition-colors border
            ${clusterPanelOpen
              ? 'bg-accent text-white border-accent'
              : 'bg-surface-tertiary hover:bg-line-hover text-content-secondary hover:text-content-primary border-line'
            }`}
          title="Toggle cluster panel">
          <Server size={14} />
          <span className="hidden lg:inline">Cluster</span>
        </button>
      </div>
    </header>
  )
}
