import { useState, useCallback, useRef } from 'react'
import Editor from '@monaco-editor/react'
import ReactMarkdown from 'react-markdown'
import { Play, Square, Trash2, ChevronUp, ChevronDown, Plus, Copy, GripVertical } from 'lucide-react'
import { useNotebookStore, Cell } from '../stores/notebookStore'
import { useThemeStore } from '../stores/themeStore'
import { wsService } from '../services/websocket'
import { CellOutput } from './CellOutput'

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python', color: '#3572A5' },
  { value: 'javascript', label: 'JavaScript', color: '#f1e05a' },
  { value: 'typescript', label: 'TypeScript', color: '#3178c6' },
  { value: 'r', label: 'R', color: '#198CE7' },
  { value: 'julia', label: 'Julia', color: '#a270ba' },
  { value: 'c', label: 'C', color: '#555555' },
  { value: 'cpp', label: 'C++', color: '#f34b7d' },
  { value: 'java', label: 'Java', color: '#b07219' },
  { value: 'go', label: 'Go', color: '#00ADD8' },
  { value: 'rust', label: 'Rust', color: '#dea584' },
  { value: 'csharp', label: 'C#', color: '#178600' },
  { value: 'ruby', label: 'Ruby', color: '#701516' },
  { value: 'kotlin', label: 'Kotlin', color: '#A97BFF' },
  { value: 'scala', label: 'Scala', color: '#c22d40' },
  { value: 'swift', label: 'Swift', color: '#F05138' },
  { value: 'haskell', label: 'Haskell', color: '#5e5086' },
  { value: 'php', label: 'PHP', color: '#4F5D95' },
  { value: 'perl', label: 'Perl', color: '#0298c3' },
  { value: 'lua', label: 'Lua', color: '#000080' },
  { value: 'bash', label: 'Bash', color: '#89e051' },
  { value: 'powershell', label: 'PowerShell', color: '#012456' },
  { value: 'sql', label: 'SQL', color: '#e38c00' },
  { value: 'octave', label: 'Octave', color: '#E16737' },
  { value: 'zig', label: 'Zig', color: '#ec915c' },
  { value: 'html', label: 'HTML', color: '#e34c26' },
]

function getMonacoLanguage(lang: string): string {
  const map: Record<string, string> = {
    python: 'python', javascript: 'javascript', typescript: 'typescript',
    r: 'r', julia: 'julia', c: 'c', cpp: 'cpp', java: 'java', go: 'go',
    rust: 'rust', csharp: 'csharp', ruby: 'ruby', kotlin: 'kotlin',
    scala: 'scala', swift: 'swift', haskell: 'haskell', php: 'php',
    perl: 'perl', lua: 'lua', bash: 'shell', powershell: 'powershell',
    sql: 'sql', octave: 'plaintext', zig: 'plaintext', html: 'html',
    markdown: 'markdown',
  }
  return map[lang] || 'plaintext'
}

function getMonacoTheme(theme: string): string {
  if (theme === 'light') return 'mbm-light'
  if (theme === 'mix') return 'mbm-mix'
  return 'mbm-dark'
}

interface Props { cell: Cell; index: number }

export function NotebookCell({ cell, index }: Props) {
  const {
    activeCell, setActiveCell, updateCellSource, updateCellLanguage,
    setCellType, setCellExecuting, clearCellOutputs, deleteCell,
    addCell, moveCellUp, moveCellDown,
  } = useNotebookStore()
  const { theme } = useThemeStore()

  const isActive = activeCell === cell.id
  const editorRef = useRef<any>(null)

  const handleRun = useCallback(() => {
    if (cell.type === 'markdown') return
    clearCellOutputs(cell.id)
    setCellExecuting(cell.id, true)
    wsService.executeCell(cell.id, cell.source, cell.language)
  }, [cell.id, cell.source, cell.language])

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.shiftKey && e.key === 'Enter') { e.preventDefault(); handleRun() }
  }, [handleRun])

  // Markdown cell (rendered)
  if (cell.type === 'markdown' && !isActive) {
    return (
      <div
        className="group relative mb-2 rounded-lg border border-transparent hover:border-line
          px-3 sm:px-4 py-3 cursor-pointer transition-colors"
        onClick={() => setActiveCell(cell.id)}
      >
        <div className="markdown-cell text-content-secondary">
          {cell.source
            ? <ReactMarkdown>{cell.source}</ReactMarkdown>
            : <p className="text-content-muted italic">Click to edit markdown...</p>
          }
        </div>
      </div>
    )
  }

  const langInfo = LANGUAGE_OPTIONS.find(l => l.value === cell.language) || LANGUAGE_OPTIONS[0]

  return (
    <div
      className={`group relative mb-2 rounded-lg border transition-colors ${
        isActive
          ? 'border-accent/40 bg-surface-secondary/60'
          : 'border-line hover:border-line-hover bg-surface-secondary/30'
      } ${cell.isExecuting ? 'cell-executing' : ''}`}
      onClick={() => setActiveCell(cell.id)}
      onKeyDown={handleKeyDown}
    >
      {/* Cell header */}
      <div className="flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1.5 border-b border-line/50">
        <GripVertical size={14} className="text-content-muted cursor-grab hidden sm:block" />
        <span className="text-[11px] text-content-muted font-mono w-8 sm:w-10 text-right">
          {cell.type === 'code' ? `[${cell.executionCount ?? ' '}]` : cell.type === 'markdown' ? 'MD' : 'RAW'}
        </span>
        {cell.type === 'code' && (
          <select
            value={cell.language}
            onChange={(e) => updateCellLanguage(cell.id, e.target.value)}
            className="bg-surface-tertiary border border-line rounded px-1.5 py-0.5 text-[11px]
              text-content-secondary outline-none cursor-pointer hover:border-line-hover transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            {LANGUAGE_OPTIONS.map((lang) => (
              <option key={lang.value} value={lang.value}>{lang.label}</option>
            ))}
          </select>
        )}
        <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: langInfo.color }} title={langInfo.label} />
        <div className="flex-1" />

        {/* Action buttons */}
        <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 focus-within:opacity-100 transition-opacity">
          {cell.type === 'code' && (
            <button
              onClick={(e) => { e.stopPropagation(); handleRun() }}
              disabled={cell.isExecuting}
              className="p-1 rounded hover:bg-surface-tertiary text-success hover:text-green-300
                disabled:text-content-muted disabled:cursor-not-allowed transition-colors"
              title="Run cell (Shift+Enter)"
            >
              {cell.isExecuting ? <Square size={14} /> : <Play size={14} />}
            </button>
          )}
          <button onClick={(e) => { e.stopPropagation(); moveCellUp(cell.id) }}
            className="p-1 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors hidden sm:block"
            title="Move up"><ChevronUp size={14} /></button>
          <button onClick={(e) => { e.stopPropagation(); moveCellDown(cell.id) }}
            className="p-1 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors hidden sm:block"
            title="Move down"><ChevronDown size={14} /></button>
          <button onClick={(e) => { e.stopPropagation(); addCell(cell.id, 'code') }}
            className="p-1 rounded hover:bg-surface-tertiary text-content-muted hover:text-content-primary transition-colors"
            title="Add cell below"><Plus size={14} /></button>
          <button onClick={(e) => { e.stopPropagation(); deleteCell(cell.id) }}
            className="p-1 rounded hover:bg-surface-tertiary text-danger hover:text-red-300 transition-colors"
            title="Delete cell"><Trash2 size={14} /></button>
        </div>
      </div>

      {/* Code editor */}
      <div className="px-0.5 sm:px-1">
        <Editor
          height={Math.max(60, Math.min(400, (cell.source.split('\n').length + 1) * 20))}
          language={cell.type === 'markdown' ? 'markdown' : getMonacoLanguage(cell.language)}
          value={cell.source}
          onChange={(value) => updateCellSource(cell.id, value || '')}
          theme={getMonacoTheme(theme)}
          options={{
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            fontSize: 13,
            fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
            fontLigatures: false,
            lineNumbers: 'on',
            lineNumbersMinChars: 3,
            glyphMargin: false,
            folding: false,
            renderLineHighlight: 'all',
            renderWhitespace: 'none',
            renderControlCharacters: false,
            renderFinalNewline: 'off',
            cursorStyle: 'line',
            cursorWidth: 3,
            cursorBlinking: 'phase',
            cursorSmoothCaretAnimation: 'on',
            scrollbar: { vertical: 'hidden', horizontal: 'auto' },
            padding: { top: 8, bottom: 8 },
            automaticLayout: true,
            tabSize: 4,
            wordWrap: 'on',
          }}
          onMount={(editor) => {
            editorRef.current = editor
            editor.addAction({
              id: 'run-cell',
              label: 'Run Cell',
              keybindings: [2049],
              run: () => handleRun(),
            })
          }}
        />
      </div>

      {/* Cell outputs */}
      {cell.outputs.length > 0 && (
        <div className="border-t border-line/50 px-2 sm:px-4 py-2 cell-output">
          {cell.outputs.map((output, i) => (
            <CellOutput key={i} output={output} />
          ))}
        </div>
      )}
    </div>
  )
}
