<script setup lang="ts">
import type { ChartSpec } from './components/ChartBlock.vue'
import type { Message, TableSpec } from './components/ChatMessage.vue'

// M1: a minimal chat page over POST /api/chat's SSE stream. No approval cards or charts
// yet (M2/M3) — a confirmation-gated tool just shows up as an ordinary tool result here.
const config = useRuntimeConfig()
const apiBase = config.public.apiBase as string

const conversationId = crypto.randomUUID()
const messages = ref<Message[]>([])
const draft = ref('')
const sending = ref(false)
const listEl = ref<HTMLElement | null>(null)
const composerEl = ref<{ focus: () => void } | null>(null)

function focusComposer() {
  nextTick(() => composerEl.value?.focus())
}

const { data: health } = await useFetch<{ status: string; version: string }>('/health', {
  baseURL: apiBase,
})

// Shown as clickable chips only on a blank conversation — once there's history the
// person already knows how to ask, so the chips would just be clutter in the feed.
const SUGGESTIONS = [
  'Bugün ciro ne kadar?',
  'En çok satan 5 ürün ne?',
  'Hangi masalar boş?',
  'Son 7 günün satış raporu',
]

function scrollToBottom() {
  requestAnimationFrame(() => {
    listEl.value?.scrollTo({ top: listEl.value.scrollHeight, behavior: 'smooth' })
  })
}

async function send(text = draft.value.trim()) {
  if (!text || sending.value) return
  draft.value = ''
  sending.value = true

  messages.value.push({ role: 'user', content: text })
  // reactive(), not a plain object: we mutate assistantMsg.* after pushing it into
  // messages (as each SSE event arrives), and Vue only tracks mutations made through the
  // reactive proxy — mutating the plain reference pushed into a ref([]) array is inert.
  const assistantMsg = reactive<Message>({
    role: 'assistant',
    content: '',
    tools: [],
    charts: [],
    tables: [],
  })
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
    onChart(tool, spec) {
      assistantMsg.charts!.push({ tool, spec: spec as unknown as ChartSpec })
      scrollToBottom()
    },
    onTable(tool, table) {
      assistantMsg.tables!.push({ tool, table: table as unknown as TableSpec })
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
      // The textarea was disabled while sending — a disabled element can't hold focus,
      // so only re-focus it now that it's enabled again, not the moment the turn starts.
      focusComposer()
    },
  })
}
</script>

<template>
  <UApp>
    <div class="flex h-dvh flex-col bg-neutral-50 dark:bg-neutral-950">
      <header
        class="flex shrink-0 items-center justify-between border-b border-neutral-200 bg-white px-5 py-3.5 dark:border-neutral-800 dark:bg-neutral-900"
      >
        <div class="flex items-center gap-2.5">
          <span
            class="size-2.5 rounded-full shadow-[0_0_8px]"
            :class="health ? 'bg-success-500 shadow-success-500/60' : 'bg-error-500 shadow-error-500/60'"
          />
          <span class="font-semibold tracking-tight text-neutral-900 dark:text-white">
            restaurant-chat-console
          </span>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex items-baseline gap-2 text-xs text-neutral-400">
            <span>{{ health ? 'online' : 'offline' }}</span>
            <span v-if="health">v{{ health.version }}</span>
          </div>
          <UColorModeButton size="sm" />
        </div>
      </header>

      <main
        ref="listEl"
        class="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-3 overflow-y-auto px-5"
        :class="messages.length ? 'py-6' : ''"
      >
        <!-- Blank conversation: greeting, suggestions and the composer all live together
             in the middle of the screen — there's nothing to scroll to yet. -->
        <div v-if="!messages.length" class="m-auto flex w-full max-w-xl flex-col items-center gap-6 py-10 text-center">
          <div
            class="size-14 rounded-full bg-gradient-to-br from-primary-400 via-primary-500 to-secondary-400 shadow-lg shadow-primary-500/30"
          />
          <div>
            <p class="text-xl font-semibold tracking-tight text-neutral-900 dark:text-white">
              Bugün nasıl yardımcı olabilirim?
            </p>
            <p class="mt-1.5 text-sm leading-relaxed text-neutral-400">
              Satış, stok ya da sipariş sor — aşağıdan örnek bir soru seç ya da kendin yaz.
            </p>
          </div>
          <ChatComposer
            ref="composerEl"
            v-model="draft"
            :disabled="sending"
            class="w-full"
            @submit="send()"
          />
          <div class="flex flex-wrap justify-center gap-2">
            <UButton
              v-for="q in SUGGESTIONS"
              :key="q"
              :label="q"
              color="neutral"
              variant="soft"
              size="sm"
              class="rounded-full"
              @click="send(q)"
            />
          </div>
        </div>
        <ChatMessage v-for="(m, i) in messages" :key="i" :message="m" />
      </main>

      <!-- Once there's history, the same composer relocates to a docked bar at the
           bottom — same card, same props, just a different home. -->
      <div
        v-if="messages.length"
        class="shrink-0 border-t border-neutral-200 bg-white px-5 py-4 dark:border-neutral-800 dark:bg-neutral-900"
      >
        <ChatComposer
          ref="composerEl"
          v-model="draft"
          :disabled="sending"
          class="mx-auto w-full max-w-2xl"
          @submit="send()"
        />
      </div>
    </div>
  </UApp>
</template>
