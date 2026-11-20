<script setup lang="ts">
export interface ToolCall {
  name: string
  args: Record<string, unknown>
  ok?: boolean
  summary?: string
}

defineProps<{ call: ToolCall }>()
</script>

<template>
  <div class="tool-card" :class="{ pending: call.ok === undefined, bad: call.ok === false }">
    <div class="tool-head">
      <span class="tool-icon">{{ call.ok === undefined ? '…' : call.ok ? '✓' : '✗' }}</span>
      <span class="tool-name">{{ call.name }}</span>
      <span v-if="Object.keys(call.args).length" class="tool-args">{{ JSON.stringify(call.args) }}</span>
    </div>
    <div v-if="call.summary" class="tool-summary">{{ call.summary }}</div>
  </div>
</template>

<style scoped>
.tool-card {
  border: 1px solid #e5e7eb;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  margin: 0.35rem 0;
  font-size: 0.85rem;
  background: #f9fafb;
}
.tool-card.pending {
  opacity: 0.7;
}
.tool-card.bad {
  border-color: #fca5a5;
  background: #fef2f2;
}
.tool-head {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-family: ui-monospace, monospace;
}
.tool-icon {
  color: #6b7280;
}
.tool-card.bad .tool-icon {
  color: #b91c1c;
}
.tool-name {
  font-weight: 600;
}
.tool-args {
  color: #6b7280;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.tool-summary {
  margin-top: 0.25rem;
  color: #374151;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
