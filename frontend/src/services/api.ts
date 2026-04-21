/**
 * API client for MBM Book backend.
 */

const API_BASE = '/api/v1'
const SESSION_KEY = 'mbm_session'

export function getClientSessionId(): string {
  let sessionId = localStorage.getItem(SESSION_KEY)
  if (!sessionId) {
    const randomPart = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
    sessionId = `sess-${randomPart}`
    localStorage.setItem(SESSION_KEY, sessionId)
  }
  return sessionId
}

async function request(path: string, options: RequestInit = {}) {
  const token = localStorage.getItem('mbm_token')
  const isFormData = options.body instanceof FormData
  const sessionId = getClientSessionId()
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    'X-MBM-Session': sessionId,
    ...(options.headers as Record<string, string> || {}),
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || 'API request failed')
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // Auth
  register: (data: { username: string; email: string; password: string }) =>
    request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),

  login: (username: string, password: string) => {
    const body = new URLSearchParams({ username, password })
    return fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-MBM-Session': getClientSessionId(),
      },
      body,
    }).then(r => r.json())
  },

  // Notebooks
  listNotebooks: () => request('/notebooks'),
  getNotebook: (id: string) => request(`/notebooks/${id}`),
  createNotebook: (data: { title?: string; default_language?: string }) =>
    request('/notebooks', { method: 'POST', body: JSON.stringify(data) }),
  updateNotebook: (id: string, data: any) =>
    request(`/notebooks/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteNotebook: (id: string) =>
    request(`/notebooks/${id}`, { method: 'DELETE' }),

  // Cells
  createCell: (nbId: string, data: any) =>
    request(`/notebooks/${nbId}/cells`, { method: 'POST', body: JSON.stringify(data) }),
  updateCell: (nbId: string, cellId: string, data: any) =>
    request(`/notebooks/${nbId}/cells/${cellId}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteCell: (nbId: string, cellId: string) =>
    request(`/notebooks/${nbId}/cells/${cellId}`, { method: 'DELETE' }),
  uploadNotebookFiles: (nbId: string, files: FileList | File[]) => {
    const form = new FormData()
    Array.from(files).forEach((file) => form.append('files', file))
    return request(`/notebooks/${nbId}/uploads`, { method: 'POST', body: form })
  },

  // Kernels
  launchKernel: (language: string, notebookId?: string) =>
    request('/kernels/launch', {
      method: 'POST',
      body: JSON.stringify({ language, notebook_id: notebookId }),
    }),
  listKernels: () => request('/kernels'),
  shutdownKernel: (id: string) =>
    request(`/kernels/${id}`, { method: 'DELETE' }),
  getLanguages: () => request('/kernels/languages/available'),

  // Cluster
  getClusterStatus: () => request('/cluster/status'),
  listNodes: () => request('/cluster/nodes'),
  getNodeResources: (id: string) => request(`/cluster/nodes/${id}/resources`),
}
