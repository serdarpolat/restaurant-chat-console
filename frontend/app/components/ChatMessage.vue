<script setup lang="ts">
import type { ToolCall } from './ToolCallCard.vue'

export interface Message {
  role: 'user' | 'assistant' | 'system-error'
  content: string
  tools?: ToolCall[]
}

defineProps<{ message: Message }>()
</script>

<template>
  <div class="row" :class="message.role">
    <div v-if="message.role === 'user'" class="said">{{ message.content }}</div>

    <div v-else-if="message.role === 'system-error'" class="error">{{ message.content }}</div>

    <div v-else class="ticket">
      <ToolCallCard v-for="(call, i) in message.tools" :key="i" :call="call" />
      <div v-if="message.tools?.length && message.content" class="rule" />
      <p v-if="message.content" class="answer">{{ message.content }}</p>
      <p v-else-if="!message.tools?.length" class="answer waiting">···</p>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  margin: 0.6rem 0;
}
.row.user {
  justify-content: flex-end;
}
.row.assistant,
.row.system-error {
  justify-content: flex-start;
}

/* user: spoken, not printed — a simple warm pill, no ticket framing */
.said {
  max-width: 80%;
  background: var(--flame);
  color: #241a0f;
  font-weight: 500;
  border-radius: 1.1rem 1.1rem 0.2rem 1.1rem;
  padding: 0.55rem 0.95rem;
}

/* assistant: printed — an order-ticket card, perforation rule, monospace line items */
.ticket {
  max-width: 85%;
  background: var(--paper);
  color: var(--ink);
  border-radius: 0.3rem;
  padding: 0.85rem 1rem;
  position: relative;
}
.ticket::before {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 0;
  border-top: 2px dashed var(--line-paper);
  margin: 0 0.6rem;
}
.rule {
  border-top: 1px dashed var(--line-paper);
  margin: 0.5rem 0;
}
.answer {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
}
.answer.waiting {
  color: var(--ink-soft);
  letter-spacing: 0.15em;
}

.error {
  max-width: 85%;
  background: rgba(193, 68, 58, 0.14);
  color: #f3b9b2;
  border: 1px solid rgba(193, 68, 58, 0.4);
  border-radius: 0.5rem;
  padding: 0.55rem 0.85rem;
  font-size: 0.9rem;
}
</style>
