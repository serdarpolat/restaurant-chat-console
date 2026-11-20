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
    <div class="bubble">
      <ToolCallCard v-for="(call, i) in message.tools" :key="i" :call="call" />
      <p v-if="message.content" class="text">{{ message.content }}</p>
      <p v-else-if="!message.tools?.length" class="text thinking">…</p>
    </div>
  </div>
</template>

<style scoped>
.row {
  display: flex;
  margin: 0.5rem 0;
}
.row.user {
  justify-content: flex-end;
}
.row.assistant,
.row.system-error {
  justify-content: flex-start;
}
.bubble {
  max-width: 80%;
  border-radius: 0.75rem;
  padding: 0.6rem 0.9rem;
}
.user .bubble {
  background: #2563eb;
  color: white;
}
.assistant .bubble {
  background: #f3f4f6;
  color: #111827;
}
.system-error .bubble {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}
.text {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.thinking {
  color: #9ca3af;
}
</style>
