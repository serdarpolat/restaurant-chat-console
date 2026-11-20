/**
 * Thin client for POST /api/chat's SSE stream (PROJECT6_SCOPE.md section 6).
 *
 * Native EventSource only does GET, and the API takes a POST body (conversation_id +
 * message), so this parses the "event: X\ndata: {...}\n\n" wire format by hand off a
 * plain fetch() ReadableStream instead of pulling in an SSE client library for it.
 */

export interface ChatEventHandlers {
  onToolCall?: (name: string, args: Record<string, unknown>) => void
  onToolResult?: (name: string, ok: boolean, summary: string) => void
  onToken?: (text: string) => void
  onError?: (message: string) => void
  onDone?: () => void
}

export async function sendChatTurn(
  apiBase: string,
  conversationId: string,
  message: string,
  handlers: ChatEventHandlers,
): Promise<void> {
  let response: Response
  try {
    response = await fetch(`${apiBase}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ conversation_id: conversationId, message }),
    })
  } catch {
    handlers.onError?.(`Backend unreachable at ${apiBase}`)
    handlers.onDone?.()
    return
  }

  if (!response.ok || !response.body) {
    handlers.onError?.(`HTTP ${response.status}`)
    handlers.onDone?.()
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  // sse-starlette terminates each line (and the blank line between events) with "\r\n",
  // not "\n" — matching only "\n\n" never finds the boundary, since "\r\n\r\n" contains no
  // adjacent "\n\n". Match either line ending explicitly.
  const EVENT_SEP = /\r?\n\r?\n/

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let match: RegExpMatchArray | null
      while ((match = buffer.match(EVENT_SEP)) !== null) {
        const rawEvent = buffer.slice(0, match.index)
        buffer = buffer.slice((match.index ?? 0) + match[0].length)
        dispatchEvent(rawEvent, handlers)
      }
    }
  } catch {
    handlers.onError?.('Connection lost while streaming the answer.')
  } finally {
    handlers.onDone?.()
  }
}

function dispatchEvent(rawEvent: string, handlers: ChatEventHandlers): void {
  let eventName = 'message'
  let dataLine = ''
  for (const line of rawEvent.split('\n')) {
    if (line.startsWith('event:')) eventName = line.slice('event:'.length).trim()
    else if (line.startsWith('data:')) dataLine += line.slice('data:'.length).trim()
  }
  if (!dataLine) return

  let parsed: Record<string, unknown>
  try {
    parsed = JSON.parse(dataLine)
  } catch {
    return
  }

  switch (eventName) {
    case 'tool_call':
      handlers.onToolCall?.(
        parsed.name as string,
        (parsed.args as Record<string, unknown>) ?? {},
      )
      break
    case 'tool_result':
      handlers.onToolResult?.(parsed.name as string, parsed.ok as boolean, parsed.summary as string)
      break
    case 'token':
      handlers.onToken?.(parsed.text as string)
      break
    case 'done':
      // handled via the finally{} in sendChatTurn — the backend may also omit it on a
      // mid-stream crash, which is exactly what that finally{} is for.
      break
  }
}
