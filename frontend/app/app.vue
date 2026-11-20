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
  // reactive(), not a plain object: we mutate assistantMsg.* after pushing it into
  // messages (as each SSE event arrives), and Vue only tracks mutations made through the
  // reactive proxy — mutating the plain reference pushed into a ref([]) array is inert.
  const assistantMsg = reactive<Message>({ role: 'assistant', content: '', tools: [] })
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
      } else if (!ok) {
        // A failing tool_result with no matching tool_call is a stream-level failure
        // (LLM/MCP error, step-limit hit — backend's "_system" name) rather than an
        // actual tool outcome. Surface it as an error instead of dropping it silently,
        // or the ticket is left stuck on "···" forever with no visible cause.
        // The in-progress assistant ticket never got a tool card or an answer, so drop
        // it rather than leave an empty "···" card sitting above the error.
        if (assistantMsg.content === '' && assistantMsg.tools!.length === 0) {
          const idx = messages.value.indexOf(assistantMsg)
          if (idx !== -1) messages.value.splice(idx, 1)
        }
        messages.value.push({ role: 'system-error', content: summary })
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
  <div class="shell">
    <header>
      <div class="brand">
        <span class="led" :class="{ off: !health }" />
        <span class="name">restaurant-chat-console</span>
      </div>
      <div class="status">
        <span>{{ health ? 'online' : 'offline' }}</span>
        <span class="version" v-if="health">v{{ health.version }}</span>
      </div>
    </header>

    <main ref="listEl" class="feed">
      <p v-if="!messages.length" class="hint">
        Satış, stok ya da sipariş sor — örn. "en çok satan 5 ürün ne?"
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
.shell {
  display: flex;
  flex-direction: column;
  height: 100dvh;
}

header {
  flex: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.25rem;
  background: var(--bg-raised);
  border-bottom: 1px solid var(--line-dark);
}
.brand {
  display: flex;
  align-items: center;
  gap: 0.6rem;
}
.led {
  width: 0.55rem;
  height: 0.55rem;
  border-radius: 50%;
  background: var(--sage);
  box-shadow: 0 0 0.4rem var(--sage);
}
.led.off {
  background: var(--brick);
  box-shadow: 0 0 0.4rem var(--brick);
}
.name {
  font-weight: 600;
  letter-spacing: -0.01em;
}
.status {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.78rem;
  color: var(--cream-soft);
}
.version {
  opacity: 0.6;
}

.feed {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  max-width: 42rem;
  width: 100%;
  margin: 0 auto;
}
.hint {
  color: var(--cream-soft);
  text-align: center;
  margin: auto 0;
  max-width: 24rem;
  align-self: center;
  line-height: 1.5;
}

.composer {
  flex: none;
  display: flex;
  gap: 0.6rem;
  padding: 1rem 1.25rem;
  background: var(--bg-raised);
  border-top: 1px solid var(--line-dark);
  max-width: 42rem;
  width: 100%;
  margin: 0 auto;
}
.composer input {
  flex: 1;
  padding: 0.65rem 0.9rem;
  border: 1px solid var(--line-dark);
  border-radius: 0.5rem;
  background: var(--bg);
  color: var(--cream);
  font-size: 0.95rem;
  font-family: inherit;
}
.composer input::placeholder {
  color: var(--cream-soft);
}
.composer button {
  padding: 0.65rem 1.3rem;
  border: none;
  border-radius: 0.5rem;
  background: var(--flame);
  color: #241a0f;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
}
.composer button:hover:not(:disabled) {
  background: var(--flame-deep);
}
.composer button:disabled {
  background: var(--bg);
  color: var(--cream-soft);
  cursor: default;
}
</style>
