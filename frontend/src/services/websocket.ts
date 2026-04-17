/**
 * WebSocket service for real-time notebook communication.
 */

type MessageHandler = (msg: any) => void

class WebSocketService {
  private ws: WebSocket | null = null
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectTimer: number | null = null
  private notebookId: string | null = null
  private pendingMessages: string[] = []

  connect(notebookId: string) {
    // Clean up any existing connection first
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.onclose = null // prevent reconnect loop
      this.ws.close()
      this.ws = null
    }

    this.notebookId = notebookId
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/ws/notebook/${notebookId}`

    this.ws = new WebSocket(url)

    this.ws.onopen = () => {
      console.log('[WS] Connected to notebook:', notebookId)
      this.emit('connected', { notebookId })
      // Flush any messages that were queued while connecting
      while (this.pendingMessages.length > 0) {
        const queued = this.pendingMessages.shift()!
        this.ws!.send(queued)
      }
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        this.emit(msg.type, msg)
        this.emit('*', msg) // wildcard handler
      } catch (e) {
        console.error('[WS] Parse error:', e)
      }
    }

    this.ws.onclose = () => {
      console.log('[WS] Disconnected. Reconnecting in 3s...')
      this.emit('disconnected', {})
      this.reconnectTimer = window.setTimeout(() => {
        if (this.notebookId) this.connect(this.notebookId)
      }, 3000)
    }

    this.ws.onerror = (err) => {
      console.error('[WS] Error:', err)
    }
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this.notebookId = null
  }

  send(msg: any) {
    const data = JSON.stringify(msg)
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(data)
    } else if (this.ws?.readyState === WebSocket.CONNECTING) {
      // Queue the message to be sent when connected
      this.pendingMessages.push(data)
    } else {
      console.warn('[WS] Not connected. Attempting reconnect...')
      this.pendingMessages.push(data)
      if (this.notebookId && !this.reconnectTimer) {
        this.connect(this.notebookId)
      }
    }
  }

  executeCell(cellId: string, code: string, language: string, kernelId?: string) {
    this.send({
      type: 'execute',
      cell_id: cellId,
      code,
      language,
      kernel_id: kernelId,
    })
  }

  interruptKernel(kernelId: string) {
    this.send({ type: 'interrupt', kernel_id: kernelId })
  }

  requestCompletion(code: string, cursorPos: number, kernelId?: string) {
    this.send({ type: 'complete', code, cursor_pos: cursorPos, kernel_id: kernelId })
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)
    return () => this.handlers.get(type)?.delete(handler)
  }

  private emit(type: string, data: any) {
    this.handlers.get(type)?.forEach(h => h(data))
  }
}

export const wsService = new WebSocketService()
