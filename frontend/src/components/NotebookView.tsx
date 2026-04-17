import { useNotebookStore } from '../stores/notebookStore'
import { NotebookCell } from './NotebookCell'
import { Plus } from 'lucide-react'

export function NotebookView() {
  const { notebook, addCell } = useNotebookStore()

  return (
    <div className="w-full max-w-[96%] xl:max-w-[92%] mx-auto px-2 sm:px-4 md:px-6 py-4 sm:py-6">
      {notebook.cells.map((cell, index) => (
        <NotebookCell key={cell.id} cell={cell} index={index} />
      ))}

      <div className="flex justify-center py-4">
        <div className="flex items-center gap-2">
          <button
            onClick={() => addCell(notebook.cells[notebook.cells.length - 1]?.id, 'code')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium
              border border-dashed border-line hover:border-accent
              text-content-muted hover:text-accent transition-colors"
          >
            <Plus size={14} /> Code
          </button>
          <button
            onClick={() => addCell(notebook.cells[notebook.cells.length - 1]?.id, 'markdown')}
            className="flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium
              border border-dashed border-line hover:border-purple-500
              text-content-muted hover:text-purple-400 transition-colors"
          >
            <Plus size={14} /> Markdown
          </button>
        </div>
      </div>
    </div>
  )
}
