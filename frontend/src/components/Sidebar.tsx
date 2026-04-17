import { FileText, Plus, Settings, Users, HardDrive, ArrowLeftRight, Trash2 } from 'lucide-react'
import { useNotebookStore } from '../stores/notebookStore'
import { useThemeStore } from '../stores/themeStore'

export function Sidebar() {
  const { notebook, savedNotebooks, createNewNotebook, loadSavedNotebook, deleteSavedNotebook } = useNotebookStore()
  const { sidebarPosition, setSidebarPosition } = useThemeStore()

  const togglePosition = () => {
    setSidebarPosition(sidebarPosition === 'left' ? 'right' : 'left')
  }

  return (
    <aside className="h-full bg-surface-secondary border-r border-line flex flex-col overflow-hidden transition-theme">
      <div className="px-4 py-3 border-b border-line flex items-center justify-between">
        <h2 className="text-xs font-semibold text-content-muted uppercase tracking-wider">Explorer</h2>
        <button
          onClick={togglePosition}
          className="p-1 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors"
          title={`Move to ${sidebarPosition === 'left' ? 'right' : 'left'}`}
        >
          <ArrowLeftRight size={12} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        <div className="px-3 mb-3">
          <button
            onClick={() => createNewNotebook()}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-xs
              bg-accent hover:bg-accent-hover text-white font-medium transition-colors shadow-sm">
            <Plus size={14} /> New Notebook
          </button>
        </div>

        <div className="px-2">
          <p className="px-2 py-1 text-[10px] font-semibold text-content-muted uppercase tracking-wide">Recent</p>
          <div className="space-y-0.5">
            {savedNotebooks.length === 0 ? (
              <div className="text-xs text-content-muted px-2 py-2">No saved notebooks</div>
            ) : (
              savedNotebooks.map(nb => (
                <div
                  key={nb.id}
                  className={`group flex items-center gap-2 px-2 py-1.5 rounded-md text-sm cursor-pointer transition-colors ${
                    notebook.id === nb.id
                      ? 'bg-accent-muted text-content-primary border border-accent/20'
                      : 'hover:bg-surface-tertiary text-content-secondary'
                  }`}
                  onClick={() => { if (notebook.id !== nb.id) loadSavedNotebook(nb.id) }}
                >
                  <FileText size={14} className={`shrink-0 ${notebook.id === nb.id ? 'text-accent' : 'text-content-muted'}`} />
                  <span className="truncate flex-1">{nb.title}</span>
                  {notebook.id !== nb.id && (
                    <button
                      onClick={(e) => { e.stopPropagation(); deleteSavedNotebook(nb.id) }}
                      className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-danger/20 text-content-muted hover:text-danger transition-all"
                      title="Delete notebook"
                    >
                      <Trash2 size={12} />
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="px-2 mt-4">
          <p className="px-2 py-1 text-[10px] font-semibold text-content-muted uppercase tracking-wide">Active Kernels</p>
          <div className="text-xs text-content-muted px-2 py-2">No active kernels</div>
        </div>
      </div>

      <div className="border-t border-line px-3 py-2 flex items-center gap-2">
        <button className="p-1.5 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors" title="Settings"><Settings size={15} /></button>
        <button className="p-1.5 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors" title="Users"><Users size={15} /></button>
        <button className="p-1.5 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors" title="Storage"><HardDrive size={15} /></button>
        <div className="flex-1" />
        <span className="text-[10px] text-content-muted">v0.1.0</span>
      </div>
    </aside>
  )
}
