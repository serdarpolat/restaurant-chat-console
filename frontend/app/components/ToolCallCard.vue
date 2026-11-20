<script setup lang="ts">
export interface ToolCall {
  name: string
  args: Record<string, unknown>
  ok?: boolean
  summary?: string
}

const { call } = defineProps<{ call: ToolCall }>()

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args)
  if (!entries.length) return ''
  return entries.map(([k, v]) => `${k}=${JSON.stringify(v)}`).join(' ')
}
</script>

<template>
  <div class="flex items-start gap-2 font-mono text-xs">
    <UIcon
      :name="
        call.ok === undefined
          ? 'i-lucide-loader-circle'
          : call.ok
            ? 'i-lucide-check-circle-2'
            : 'i-lucide-x-circle'
      "
      class="mt-0.5 size-3.5 shrink-0"
      :class="[
        call.ok === undefined && 'animate-spin text-neutral-400',
        call.ok === true && 'text-success-500',
        call.ok === false && 'text-error-500',
      ]"
    />
    <div class="min-w-0 flex-1">
      <div class="flex flex-wrap items-baseline gap-x-1.5">
        <span class="font-semibold text-neutral-700 dark:text-neutral-200">{{ call.name }}</span>
        <span v-if="formatArgs(call.args)" class="truncate text-neutral-400">
          {{ formatArgs(call.args) }}
        </span>
      </div>
      <p
        v-if="call.summary"
        :title="call.summary"
        class="mt-0.5 truncate rounded-md px-1.5 py-0.5 text-neutral-500 dark:text-neutral-400"
        :class="
          call.ok === false
            ? 'bg-error-50 text-error-600 dark:bg-error-950 dark:text-error-400'
            : 'bg-neutral-50 dark:bg-neutral-800'
        "
      >
        {{ call.summary }}
      </p>
    </div>
  </div>
</template>
