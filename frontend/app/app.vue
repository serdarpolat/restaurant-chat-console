<script setup lang="ts">
import type { Message } from './components/ChatMessage.vue'

// M1: a minimal chat page over POST /api/chat's SSE stream. No approval cards or charts
// yet (M2/M3) — a confirmation-gated tool just shows up as an ordinary tool result here.
const config = useRuntimeConfig()
const apiBase = config.public.apiBase as string

const conversationId = crypto.randomUUID()
const messages = ref<Message[]>([])
const draft = ref('')
const sending = ref(false)
const listEl = ref<HTMLElement | null>(null)

const { data: health } = await useFetch<{ status: string; version: string }>('/health', {
  baseURL: apiBase,
})

function scrollToBottom() {
  requestAnimationFrame(() => {
    listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })
  })
}

async function send() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  draft.value = ''
  sending.value = true

  messages.value.push({ role: 'user', content: text })
  const assistantMsg: Message = { role: 'assistant', content: '', tools: [] }
  messages.value.push(assistantMsg)
  scrollToBottom()

  await sendChatTurn(apiBase, conversationId, text, {
    onToolCall(name, args) {
      assistantMsg.tools!.push({ name, args })
      scrollToBottom()
    },
    onToolResult(name, ok, summary) {
      const call = assistantMsg.tools!.findLast((c) => c.name === name && c.ok === undefined)
      if (call) {
        call.ok = ok
        call.summary = summary
      }
      scrollToBottom()
    },
    onToken(text) {
      assistantMsg.content += text
      scrollToBottom()
    },
    onError(message) {
      messages.value.push({ role: 'system-error', content: message })
      scrollToBottom()
    },
    onDone() {
      sending.value = false
    },
  })
}
</script>

<template>
  <div class="page">
    <header>
      <h1>restaurant-chat-console</h1>
      <span class="status" :class="{ bad: !health }">
        {{ health ? `backend ok (v${health.version})` : 'backend unreachable' }}
      </span>
    </header>

    <main ref="listEl" class="messages">
      <p v-if="!messages.length" class="hint">
        Ask about sales, inventory, or an order — e.g. "en çok satan 5 ürün ne?"
      </p>
      <ChatMessage v-for="(m, i) in messages" :key="i" :message="m" />
    </main>

    <form class="composer" @submit.prevent="send">
      <input
        v-model="draft"
        type="text"
        placeholder="Yazın…"
        :disabled="sending"
        autofocus
      />
      <button type="submit" :disabled="sending || !draft.trim()">Gönder</button>
    </form>
  </div>
</template>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  max-width: 40rem;
  margin: 0 auto;
  font-family: system-ui, sans-serif;
}
header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}
h1 {
  font-size: 1.1rem;
  margin: 0;
}
.status {
  font-size: 0.8rem;
  color: #15803d;
}
.status.bad {
  color: #b91c1c;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}
.hint {
  color: #9ca3af;
  text-align: center;
  margin-top: 2rem;
}
.composer {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  border-top: 1px solid #e5e7eb;
}
.composer input {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 1rem;
}
.composer button {
  padding: 0.6rem 1.2rem;
  border: none;
  border-radius: 0.5rem;
  background: #2563eb;
  color: white;
  font-size: 1rem;
  cursor: pointer;
}
.composer button:disabled {
  background: #93c5fd;
  cursor: default;
}
</style>
