/**
 * Local Monaco Editor setup — no CDN dependency.
 * Workers are bundled by Vite so Monaco loads instantly from the LAN server.
 */
import * as monaco from 'monaco-editor'
import { loader } from '@monaco-editor/react'

import editorWorker from 'monaco-editor/esm/vs/editor/editor.worker?worker'
import jsonWorker from 'monaco-editor/esm/vs/language/json/json.worker?worker'
import cssWorker from 'monaco-editor/esm/vs/language/css/css.worker?worker'
import htmlWorker from 'monaco-editor/esm/vs/language/html/html.worker?worker'
import tsWorker from 'monaco-editor/esm/vs/language/typescript/ts.worker?worker'

self.MonacoEnvironment = {
  getWorker(_: unknown, label: string) {
    if (label === 'json') return new jsonWorker()
    if (label === 'css' || label === 'scss' || label === 'less') return new cssWorker()
    if (label === 'html' || label === 'handlebars' || label === 'razor') return new htmlWorker()
    if (label === 'typescript' || label === 'javascript') return new tsWorker()
    return new editorWorker()
  },
}

monaco.editor.defineTheme('mbm-dark', {
  base: 'vs-dark',
  inherit: true,
  rules: [],
  colors: {
    'editorCursor.foreground': '#FBBF24',
    'editor.lineHighlightBackground': '#2A3148',
    'editorLineNumber.foreground': '#5B6B86',
    'editorLineNumber.activeForeground': '#E3E7EA',
    'editor.selectionBackground': '#42506F99',
    'editor.inactiveSelectionBackground': '#33415555',
  },
})

monaco.editor.defineTheme('mbm-mix', {
  base: 'vs-dark',
  inherit: true,
  rules: [],
  colors: {
    'editorCursor.foreground': '#F59E0B',
    'editor.lineHighlightBackground': '#313B57',
    'editorLineNumber.foreground': '#6A738B',
    'editorLineNumber.activeForeground': '#EEF2FF',
    'editor.selectionBackground': '#5B6C9899',
    'editor.inactiveSelectionBackground': '#3D4A6A55',
  },
})

monaco.editor.defineTheme('mbm-light', {
  base: 'vs',
  inherit: true,
  rules: [],
  colors: {
    'editorCursor.foreground': '#B45309',
    'editor.lineHighlightBackground': '#EEF2FF',
    'editorLineNumber.foreground': '#9AA4B2',
    'editorLineNumber.activeForeground': '#1F2937',
    'editor.selectionBackground': '#C7D2FE80',
    'editor.inactiveSelectionBackground': '#D6DEF080',
  },
})

// Tell @monaco-editor/react to use the local Monaco instance (skip CDN)
loader.config({ monaco })
