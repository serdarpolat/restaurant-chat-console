<script setup lang="ts">
// Renders a Chart.js spec the backend already decided on (chat_console/charts.py,
// PROJECT6_SCOPE.md section 5) — this component never infers chart shape from the
// answer text, it just draws whatever spec arrived with the `chart` SSE event.
import { Bar, Line } from 'vue-chartjs'
import { Chart as ChartJS, registerables } from 'chart.js'

// Hand-picking controllers/elements/scales (the tree-shaken route) is easy to get subtly
// wrong — e.g. scales/legend still render but the dataset itself silently never draws.
// This is an internal staff tool, not a public bundle shipped to thousands of visitors;
// registering everything trades a few KB for "it just works".
ChartJS.register(...registerables)

export interface ChartSpec {
  type: 'bar' | 'line'
  data: Record<string, unknown>
  options?: Record<string, unknown>
  meta?: { headline?: number; headlineLabel?: string }
}

const props = defineProps<{ spec: ChartSpec }>()

const COMPONENTS = { bar: Bar, line: Line } as const

// Chart.js stores its own per-dataset bookkeeping (_meta, parsed caches, ...) directly on
// the objects it's handed, and mutating a Vue reactive Proxy that way silently breaks its
// internal identity checks — the scales/legend render fine but the dataset itself never
// gets drawn. spec.* comes off an SSE event pushed into a reactive() message, so hand
// Chart.js a plain clone instead of the live proxy.
const chartData = computed(() => structuredClone(toRaw(props.spec.data)))

// Chart.js draws on a <canvas>, so it needs real color values, not CSS variables — read
// the app's own dark-mode state (bundled with @nuxt/ui) and recompute them reactively
// instead of hand-maintaining a second light/dark palette.
const colorMode = useColorMode()
const isDark = computed(() => colorMode.value === 'dark')
const axisColor = computed(() => (isDark.value ? '#a1a1aa' : '#71717a'))
const gridColor = computed(() => (isDark.value ? 'rgba(255,255,255,0.07)' : 'rgba(0,0,0,0.06)'))

const mergedOptions = computed(() => {
  const legend = (props.spec.options?.plugins as Record<string, unknown> | undefined)?.legend as
    | Record<string, unknown>
    | undefined
  return {
    maintainAspectRatio: false,
    responsive: true,
    // vue-chartjs re-calls chart.update() on every reactive tick anywhere in the parent
    // (a token streaming into the answer above, the composer re-focusing, ...) — with
    // Chart.js's default animated update that means each tick restarts the draw
    // transition from scratch, so a screenshot (or a person's eye) can land on a
    // half-finished or just-reset frame instead of the finished chart. None of those
    // updates are ever "new data" for a chart that's static once the SSE event lands, so
    // there's nothing worth animating — draw the final state immediately every time.
    animation: false,
    indexAxis: props.spec.options?.indexAxis,
    scales: {
      x: { ticks: { color: axisColor.value }, grid: { color: gridColor.value, display: false } },
      y: { ticks: { color: axisColor.value }, grid: { color: gridColor.value } },
    },
    plugins: {
      legend: { ...legend, labels: { color: axisColor.value } },
    },
  }
})

function formatHeadline(n: number): string {
  return new Intl.NumberFormat('tr-TR', { maximumFractionDigits: 0 }).format(n)
}
</script>

<template>
  <div
    class="rounded-2xl border border-neutral-100 bg-neutral-50/70 p-4 dark:border-neutral-800 dark:bg-neutral-800/40"
  >
    <div v-if="spec.meta?.headline !== undefined" class="mb-3">
      <p class="text-xs text-neutral-400">{{ spec.meta.headlineLabel }}</p>
      <p class="text-2xl font-semibold tracking-tight text-neutral-900 dark:text-white">
        {{ formatHeadline(spec.meta.headline) }}
      </p>
    </div>
    <div class="h-56">
      <component :is="COMPONENTS[spec.type]" :data="chartData" :options="mergedOptions" />
    </div>
  </div>
</template>
