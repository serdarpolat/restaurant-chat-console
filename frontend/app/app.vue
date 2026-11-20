<script setup lang="ts">
// M0: just prove frontend <-> backend wiring works. The actual chat UI
// (ChatMessage.vue, ApprovalCard.vue, ChartBlock.vue, ToolCallCard.vue) lands in
// M1-M3 — see PROJECT6_SCOPE.md.
const config = useRuntimeConfig()

const { data, error, status } = await useFetch<{ status: string; version: string }>(
  '/health',
  { baseURL: config.public.apiBase }
)
</script>

<template>
  <main class="wrap">
    <h1>restaurant-chat-console</h1>
    <p class="muted">M0 — skeleton only. Chat UI arrives in M1.</p>

    <p v-if="status === 'pending'">Checking backend…</p>
    <p v-else-if="error" class="bad">
      Backend unreachable at {{ config.public.apiBase }}/health
    </p>
    <p v-else class="ok">
      Backend OK — {{ data?.status }} (v{{ data?.version }})
    </p>
  </main>
</template>

<style scoped>
.wrap {
  font-family: system-ui, sans-serif;
  max-width: 32rem;
  margin: 4rem auto;
  padding: 0 1rem;
}
.muted {
  color: #6b7280;
}
.ok {
  color: #15803d;
}
.bad {
  color: #b91c1c;
}
</style>
