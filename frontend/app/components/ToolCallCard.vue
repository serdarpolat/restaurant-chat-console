<script setup lang="ts">
export interface ToolCall {
  name: string
  args: Record<string, unknown>
  ok?: boolean
  summary?: string
}

defineProps<{ call: ToolCall }>()

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args)
  if (!entries.length) return ''
  return entries.map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(' ')
}
</script>

<template>
  <div class="line" :class="{ pending: call.ok === undefined, bad: call.ok === false }">
    <span class="mark">{{ call.ok === undefined ? '…' : call.ok ? '✓' : '✗' }}</span>
    <span class="name">{{ call.name }}</span>
    <span v-if="formatArgs(call.args)" class="args">{{ formatArgs(call.args) }}</span>
    <span v-if="call.summary" class="result" :title="call.summary">{{ call.summary }}</span>
  </div>
</template>

<style scoped>
.line {
  font-family: var(--font-mono);
  font-size: 0.78rem;
  line-height: 1.5;
  color: var(--ink-soft);
  display: grid;
  grid-template-columns: 1.1em auto 1fr;
  column-gap: 0.5rem;
  align-items: baseline;
}
.line.pending {
  color: var(--ink-soft);
}
.line.bad .mark {
  color: var(--brick);
}
.mark {
  color: var(--sage);
  text-align: center;
}
.name {
  color: var(--ink);
  font-weight: 600;
}
.args {
  color: var(--ink-soft);
  grid-column: 3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.result {
  grid-column: 2 / 4;
  color: var(--ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding-left: 1.6em;
  opacity: 0.8;
  cursor: default;
}
</style>
