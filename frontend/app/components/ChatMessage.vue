<script setup lang="ts">
import type { ChartSpec } from './ChartBlock.vue'
import type { ToolCall } from './ToolCallCard.vue'

export interface TableSpec {
  columns: string[]
  rows: (string | number)[][]
}

export interface Message {
  role: 'user' | 'assistant' | 'system-error'
  content: string
  tools?: ToolCall[]
  charts?: { tool: string; spec: ChartSpec }[]
  tables?: { tool: string; table: TableSpec }[]
}

defineProps<{ message: Message }>()
</script>

<template>
  <div class="flex" :class="message.role === 'user' ? 'justify-end' : 'justify-start'">
    <div
      v-if="message.role === 'user'"
      class="max-w-[80%] rounded-2xl rounded-br-md bg-primary-500 px-4 py-2.5 text-white shadow-sm"
    >
      {{ message.content }}
    </div>

    <UAlert
      v-else-if="message.role === 'system-error'"
      color="error"
      variant="subtle"
      icon="i-lucide-triangle-alert"
      :title="message.content"
      class="max-w-[85%]"
    />

    <UCard v-else class="max-w-[85%] shadow-sm" :ui="{ body: 'p-4 sm:p-4' }">
      <div v-if="message.tools?.length" class="space-y-2">
        <ToolCallCard v-for="(call, i) in message.tools" :key="i" :call="call" />
      </div>
      <div v-if="message.tools?.length" class="my-3 border-t border-neutral-100 dark:border-neutral-800" />
      <!-- eslint-disable-next-line vue/no-v-html -- sanitized by useMarkdown's DOMPurify pass -->
      <div
        v-if="message.content"
        class="markdown-answer leading-relaxed text-neutral-700 dark:text-neutral-200"
        v-html="renderMarkdown(message.content)"
      />
      <div v-else class="flex gap-1 py-0.5">
        <span class="size-1.5 animate-bounce rounded-full bg-neutral-300 [animation-delay:-0.3s] dark:bg-neutral-600" />
        <span class="size-1.5 animate-bounce rounded-full bg-neutral-300 [animation-delay:-0.15s] dark:bg-neutral-600" />
        <span class="size-1.5 animate-bounce rounded-full bg-neutral-300 dark:bg-neutral-600" />
      </div>
      <!-- Deterministic, backend-built tables (chat_console/tables.py) — generated from
           the tool's own structured result, not from whether the model's prose happened
           to include a markdown table this time. -->
      <div v-if="message.tables?.length" class="markdown-answer mt-3 space-y-3">
        <div v-for="(t, i) in message.tables" :key="i" class="table-scroll">
          <table>
            <thead>
              <tr>
                <th v-for="col in t.table.columns" :key="col">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, ri) in t.table.rows" :key="ri">
                <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
      <div v-if="message.charts?.length" class="mt-3 space-y-3">
        <ChartBlock v-for="(c, i) in message.charts" :key="i" :spec="c.spec" />
      </div>
    </UCard>
  </div>
</template>

<style scoped>
/* markdown-it's output is plain tags (table/th/td/strong/ul/code/a) with no classes of its
   own to hook — style them directly rather than post-processing the HTML to inject
   Tailwind classes into every cell. */
.markdown-answer :deep(p) {
  margin: 0;
}
.markdown-answer :deep(p + p) {
  margin-top: 0.75em;
}
.markdown-answer :deep(strong) {
  font-weight: 600;
  color: inherit;
}
.markdown-answer :deep(ul),
.markdown-answer :deep(ol) {
  margin: 0.5em 0;
  padding-inline-start: 1.25em;
}
.markdown-answer :deep(li + li) {
  margin-top: 0.25em;
}
.markdown-answer :deep(code) {
  border-radius: 0.25rem;
  background: rgb(0 0 0 / 6%);
  padding: 0.1em 0.35em;
  font-size: 0.9em;
}
:global(.dark) .markdown-answer :deep(code) {
  background: rgb(255 255 255 / 10%);
}
.markdown-answer :deep(a) {
  color: var(--ui-primary, #8b5cf6);
  text-decoration: underline;
  text-underline-offset: 2px;
}
.markdown-answer :deep(.table-scroll) {
  margin: 0.75em 0;
  overflow-x: auto;
  border-radius: 0.5rem;
}
.markdown-answer :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9em;
}
.markdown-answer :deep(th),
.markdown-answer :deep(td) {
  border: 1px solid rgb(0 0 0 / 8%);
  padding: 0.45em 0.7em;
  text-align: left;
}
.markdown-answer :deep(th) {
  background: rgb(0 0 0 / 4%);
  font-weight: 600;
}
.markdown-answer :deep(tr:nth-child(even) td) {
  background: rgb(0 0 0 / 2%);
}
:global(.dark) .markdown-answer :deep(th),
:global(.dark) .markdown-answer :deep(td) {
  border-color: rgb(255 255 255 / 10%);
}
:global(.dark) .markdown-answer :deep(th) {
  background: rgb(255 255 255 / 6%);
}
:global(.dark) .markdown-answer :deep(tr:nth-child(even) td) {
  background: rgb(255 255 255 / 3%);
}
</style>
