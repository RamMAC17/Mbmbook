/**
 * MBM Book - Notebook state management using Zustand.
 * Notebooks are persisted to localStorage (Colab-like persistence).
 */

import { create } from 'zustand'

// ─── Storage Keys ───
const NOTEBOOKS_KEY = 'mbmbook-notebooks'
const CURRENT_KEY = 'mbmbook-current-nb-id'

// ─── Storage Helpers ───

interface SavedNotebookData {
  id: string
  title: string
  cells: Array<{
    id: string
    type: 'code' | 'markdown' | 'raw'
    language: string
    source: string
    outputs: CellOutput[]
    executionCount: number | null
  }>
  defaultLanguage: string
  updatedAt: string
}

function loadAllNotebooks(): Record<string, SavedNotebookData> {
  try {
    const raw = localStorage.getItem(NOTEBOOKS_KEY)
    return raw ? JSON.parse(raw) : {}
  } catch { return {} }
}

function saveAllNotebooks(nbs: Record<string, SavedNotebookData>) {
  try {
    localStorage.setItem(NOTEBOOKS_KEY, JSON.stringify(nbs))
  } catch { /* quota exceeded - ignore */ }
}

function saveNotebookToStorage(nb: Notebook) {
  const all = loadAllNotebooks()
  all[nb.id] = {
    id: nb.id,
    title: nb.title,
    defaultLanguage: nb.defaultLanguage,
    updatedAt: new Date().toISOString(),
    cells: nb.cells.map(c => ({
      id: c.id,
      type: c.type,
      language: c.language,
      source: c.source,
      outputs: c.outputs,
      executionCount: c.executionCount,
    })),
  }
  saveAllNotebooks(all)
  localStorage.setItem(CURRENT_KEY, nb.id)
}

function loadNotebookFromStorage(id: string): Notebook | null {
  const all = loadAllNotebooks()
  const saved = all[id]
  if (!saved) return null
  return {
    id: saved.id,
    title: saved.title,
    defaultLanguage: saved.defaultLanguage,
    cells: saved.cells.map(c => ({
      ...c,
      isExecuting: false,
      isEditing: false,
    })),
  }
}

function deleteNotebookFromStorage(id: string) {
  const all = loadAllNotebooks()
  delete all[id]
  saveAllNotebooks(all)
}

function getNotebookList(): Array<{ id: string; title: string; updatedAt: string }> {
  const all = loadAllNotebooks()
  return Object.values(all)
    .map(nb => ({ id: nb.id, title: nb.title, updatedAt: nb.updatedAt }))
    .sort((a, b) => b.updatedAt.localeCompare(a.updatedAt))
}

function loadInitialNotebook(): Notebook {
  const currentId = localStorage.getItem(CURRENT_KEY)
  if (currentId) {
    const nb = loadNotebookFromStorage(currentId)
    if (nb && nb.cells.length > 0) return nb
  }
  // Check if there are any saved notebooks
  const list = getNotebookList()
  if (list.length > 0) {
    const nb = loadNotebookFromStorage(list[0].id)
    if (nb) return nb
  }
  // Create fresh notebook
  const fresh: Notebook = {
    id: `nb-${Date.now()}`,
    title: 'Untitled Notebook',
    cells: [createDefaultCell('code', 'python')],
    defaultLanguage: 'python',
  }
  return fresh
}

export interface CellOutput {
  type: 'stream' | 'execute_result' | 'error' | 'display_data'
  name?: string      // stdout, stderr
  text?: string
  data?: Record<string, string>
  ename?: string
  evalue?: string
  traceback?: string[]
}

export interface Cell {
  id: string
  type: 'code' | 'markdown' | 'raw'
  language: string
  source: string
  outputs: CellOutput[]
  executionCount: number | null
  isExecuting: boolean
  isEditing: boolean
}

export interface Notebook {
  id: string
  title: string
  cells: Cell[]
  defaultLanguage: string
}

export interface ClusterNode {
  id: string
  hostname: string
  ipAddress: string
  status: string
  cpuCores: number
  ramTotalGb: number
  gpuName: string
  gpuVramGb: number
  activeKernels: number
}

interface NotebookState {
  // Notebook
  notebook: Notebook
  activeCell: string | null
  savedNotebooks: Array<{ id: string; title: string; updatedAt: string }>
  
  // Cluster
  clusterNodes: ClusterNode[]
  
  // UI
  sidebarOpen: boolean
  clusterPanelOpen: boolean
  
  // Actions
  setNotebook: (nb: Notebook) => void
  setActiveCell: (id: string | null) => void
  addCell: (after?: string, type?: 'code' | 'markdown', language?: string) => void
  deleteCell: (id: string) => void
  updateCellSource: (id: string, source: string) => void
  updateCellLanguage: (id: string, language: string) => void
  setCellType: (id: string, type: 'code' | 'markdown' | 'raw') => void
  setCellExecuting: (id: string, executing: boolean) => void
  setCellOutputs: (id: string, outputs: CellOutput[]) => void
  appendCellOutput: (id: string, output: CellOutput) => void
  setCellExecutionCount: (id: string, count: number) => void
  moveCellUp: (id: string) => void
  moveCellDown: (id: string) => void
  clearCellOutputs: (id: string) => void
  clearAllOutputs: () => void
  setNotebookTitle: (title: string) => void
  toggleSidebar: () => void
  toggleClusterPanel: () => void
  setClusterNodes: (nodes: ClusterNode[]) => void

  // Persistence actions
  saveNotebook: () => void
  createNewNotebook: () => void
  loadSavedNotebook: (id: string) => void
  deleteSavedNotebook: (id: string) => void
  refreshNotebookList: () => void
  downloadNotebook: () => void
}

let cellCounter = 0
function newCellId(): string {
  return `cell-${Date.now()}-${++cellCounter}`
}

function createDefaultCell(type: 'code' | 'markdown' = 'code', language = 'python'): Cell {
  return {
    id: newCellId(),
    type,
    language,
    source: '',
    outputs: [],
    executionCount: null,
    isExecuting: false,
    isEditing: true,
  }
}

export const useNotebookStore = create<NotebookState>((set, get) => {
  const initialNotebook = loadInitialNotebook()

  // Debounced auto-save
  let saveTimer: ReturnType<typeof setTimeout> | null = null
  function debouncedSave() {
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => {
      const state = get()
      saveNotebookToStorage(state.notebook)
      set({ savedNotebooks: getNotebookList() })
    }, 500)
  }

  return {
    notebook: initialNotebook,
    activeCell: null,
    savedNotebooks: getNotebookList(),
    clusterNodes: [],
    sidebarOpen: true,
    clusterPanelOpen: false,

    setNotebook: (nb) => { set({ notebook: nb }); debouncedSave() },
    setActiveCell: (id) => set({ activeCell: id }),

    addCell: (after, type = 'code', language) => {
      set((state) => {
        const lang = language || state.notebook.defaultLanguage
        const newCell = createDefaultCell(type, lang)
        const cells = [...state.notebook.cells]

        if (after) {
          const idx = cells.findIndex(c => c.id === after)
          cells.splice(idx + 1, 0, newCell)
        } else {
          cells.push(newCell)
        }

        return {
          notebook: { ...state.notebook, cells },
          activeCell: newCell.id,
        }
      })
      debouncedSave()
    },

    deleteCell: (id) => {
      set((state) => {
        const cells = state.notebook.cells.filter(c => c.id !== id)
        if (cells.length === 0) {
          cells.push(createDefaultCell())
        }
        return { notebook: { ...state.notebook, cells } }
      })
      debouncedSave()
    },

    updateCellSource: (id, source) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c => c.id === id ? { ...c, source } : c),
        },
      }))
      debouncedSave()
    },

    updateCellLanguage: (id, language) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c => c.id === id ? { ...c, language } : c),
        },
      }))
      debouncedSave()
    },

    setCellType: (id, type) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c => c.id === id ? { ...c, type } : c),
        },
      }))
      debouncedSave()
    },

    setCellExecuting: (id, isExecuting) => set((state) => ({
      notebook: {
        ...state.notebook,
        cells: state.notebook.cells.map(c => c.id === id ? { ...c, isExecuting } : c),
      },
    })),

    setCellOutputs: (id, outputs) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c => c.id === id ? { ...c, outputs } : c),
        },
      }))
      debouncedSave()
    },

    appendCellOutput: (id, output) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c =>
            c.id === id ? { ...c, outputs: [...c.outputs, output] } : c
          ),
        },
      }))
      debouncedSave()
    },

    setCellExecutionCount: (id, count) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c =>
            c.id === id ? { ...c, executionCount: count } : c
          ),
        },
      }))
      debouncedSave()
    },

    moveCellUp: (id) => {
      set((state) => {
        const cells = [...state.notebook.cells]
        const idx = cells.findIndex(c => c.id === id)
        if (idx > 0) {
          [cells[idx - 1], cells[idx]] = [cells[idx], cells[idx - 1]]
        }
        return { notebook: { ...state.notebook, cells } }
      })
      debouncedSave()
    },

    moveCellDown: (id) => {
      set((state) => {
        const cells = [...state.notebook.cells]
        const idx = cells.findIndex(c => c.id === id)
        if (idx < cells.length - 1) {
          [cells[idx], cells[idx + 1]] = [cells[idx + 1], cells[idx]]
        }
        return { notebook: { ...state.notebook, cells } }
      })
      debouncedSave()
    },

    clearCellOutputs: (id) => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c =>
            c.id === id ? { ...c, outputs: [], executionCount: null } : c
          ),
        },
      }))
      debouncedSave()
    },

    clearAllOutputs: () => {
      set((state) => ({
        notebook: {
          ...state.notebook,
          cells: state.notebook.cells.map(c => ({ ...c, outputs: [], executionCount: null })),
        },
      }))
      debouncedSave()
    },

    setNotebookTitle: (title) => {
      set((state) => ({
        notebook: { ...state.notebook, title },
      }))
      debouncedSave()
    },

    toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
    toggleClusterPanel: () => set((state) => ({ clusterPanelOpen: !state.clusterPanelOpen })),
    setClusterNodes: (nodes) => set({ clusterNodes: nodes }),

    // ── Persistence Actions ──

    saveNotebook: () => {
      const state = get()
      saveNotebookToStorage(state.notebook)
      set({ savedNotebooks: getNotebookList() })
    },

    createNewNotebook: () => {
      // Save current notebook first
      const state = get()
      saveNotebookToStorage(state.notebook)

      const fresh: Notebook = {
        id: `nb-${Date.now()}`,
        title: 'Untitled Notebook',
        cells: [createDefaultCell('code', 'python')],
        defaultLanguage: 'python',
      }
      saveNotebookToStorage(fresh)
      set({
        notebook: fresh,
        activeCell: null,
        savedNotebooks: getNotebookList(),
      })
    },

    loadSavedNotebook: (id) => {
      // Save current notebook first
      const state = get()
      saveNotebookToStorage(state.notebook)

      const nb = loadNotebookFromStorage(id)
      if (nb) {
        set({
          notebook: nb,
          activeCell: null,
          savedNotebooks: getNotebookList(),
        })
      }
    },

    deleteSavedNotebook: (id) => {
      const state = get()
      deleteNotebookFromStorage(id)
      // If deleting current notebook, switch to another or create new
      if (state.notebook.id === id) {
        const list = getNotebookList()
        if (list.length > 0) {
          const nb = loadNotebookFromStorage(list[0].id)
          if (nb) {
            set({ notebook: nb, activeCell: null, savedNotebooks: list })
            return
          }
        }
        // No notebooks left - create fresh
        const fresh: Notebook = {
          id: `nb-${Date.now()}`,
          title: 'Untitled Notebook',
          cells: [createDefaultCell('code', 'python')],
          defaultLanguage: 'python',
        }
        set({ notebook: fresh, activeCell: null, savedNotebooks: getNotebookList() })
      } else {
        set({ savedNotebooks: getNotebookList() })
      }
    },

    refreshNotebookList: () => {
      set({ savedNotebooks: getNotebookList() })
    },

    downloadNotebook: () => {
      const state = get()
      const nb = state.notebook
      // Convert to .ipynb format
      const ipynb = {
        nbformat: 4,
        nbformat_minor: 5,
        metadata: {
          kernelspec: {
            display_name: nb.defaultLanguage.charAt(0).toUpperCase() + nb.defaultLanguage.slice(1),
            language: nb.defaultLanguage,
            name: nb.defaultLanguage,
          },
          language_info: { name: nb.defaultLanguage },
          title: nb.title,
        },
        cells: nb.cells.map(c => ({
          cell_type: c.type === 'raw' ? 'raw' : c.type,
          source: c.source.split('\n').map((line, i, arr) => i < arr.length - 1 ? line + '\n' : line),
          metadata: { language: c.language },
          ...(c.type === 'code' ? {
            execution_count: c.executionCount,
            outputs: c.outputs.map(o => {
              if (o.type === 'stream') return { output_type: 'stream', name: o.name || 'stdout', text: [o.text || ''] }
              if (o.type === 'error') return { output_type: 'error', ename: o.ename || '', evalue: o.evalue || '', traceback: o.traceback || [] }
              return { output_type: 'execute_result', data: o.data || {}, metadata: {} }
            }),
          } : {}),
        })),
      }
      const blob = new Blob([JSON.stringify(ipynb, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${nb.title.replace(/[^a-zA-Z0-9-_ ]/g, '')}.ipynb`
      a.click()
      URL.revokeObjectURL(url)
    },
  }
})
