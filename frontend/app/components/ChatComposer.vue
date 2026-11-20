<script setup lang="ts">
// Same card, two homes: app.vue centers it on a blank conversation and docks it to the
// bottom once there's history — the component itself doesn't know which, it just exposes
// focus() so the parent can return the cursor here after a send.
const model = defineModel<string>({ required: true })
const props = defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ submit: [] }>()

const textareaEl = ref<HTMLTextAreaElement | null>(null)

function autoGrow() {
  const el = textareaEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = `${Math.min(el.scrollHeight, 160)}px`
}

function submit() {
  if (props.disabled || !model.value.trim()) return
  emit('submit')
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    submit()
  }
}

// Draft is cleared by the parent right after submit; collapse the textarea back down
// instead of leaving it stretched to the height of the question just sent.
watch(model, (value) => {
  if (!value) nextTick(autoGrow)
})

defineExpose({
  focus: () => textareaEl.value?.focus(),
})
</script>

<template>
  <div
    class="flex flex-col gap-2 rounded-3xl border border-neutral-200 bg-white p-3 shadow-lg shadow-neutral-900/5 transition-colors focus-within:border-primary-300 dark:border-neutral-800 dark:bg-neutral-900 dark:focus-within:border-primary-700"
  >
    <textarea
      ref="textareaEl"
      v-model="model"
      rows="1"
      :disabled="disabled"
      placeholder="Satış, stok ya da sipariş sor…"
      class="max-h-40 min-h-10 w-full resize-none border-0 bg-transparent px-2 py-1.5 text-[15px] leading-relaxed text-neutral-900 placeholder-neutral-400 focus:outline-none focus:ring-0 disabled:opacity-60 dark:text-neutral-100"
      @input="autoGrow"
      @keydown="onKeydown"
    />
    <div class="flex items-center justify-between px-1">
      <span class="text-xs text-neutral-400">Enter ile gönder · Shift+Enter yeni satır</span>
      <UButton
        icon="i-lucide-arrow-up"
        color="primary"
        :disabled="disabled || !model.trim()"
        class="size-9 rounded-full"
        @click="submit"
      />
    </div>
  </div>
</template>
