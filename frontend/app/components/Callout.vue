<script setup lang="ts">
/**
 * Notice box with a fixed meaning (docs/guide-types.md). The label always comes first; an
 * icon and a word carry the meaning, never colour alone. Levels: note, important (careful),
 * warning (risk of injury or damage), danger (risk to life).
 */
export type CalloutKind = 'tip' | 'note' | 'important' | 'warning' | 'danger' | 'error' | 'result'

const props = defineProps<{ kind: CalloutKind; html?: string; label?: string }>()
const t = useGuideLabels()

const META = {
  tip: { icon: 'tip' },
  note: { icon: 'info' },
  important: { icon: 'alert' },
  warning: { icon: 'alert' },
  danger: { icon: 'stop' },
  error: { icon: 'close' },
  result: { icon: 'check-circle' },
} as const
const meta = computed(() => META[props.kind])
const text = computed(() => props.label ?? t.value[props.kind])
</script>

<template>
  <aside class="callout" :class="`callout-${kind}`" :role="['important', 'warning', 'danger', 'error'].includes(kind) ? 'note' : undefined">
    <p class="callout-label" :lang="t.lang">
      <GuideIcon :name="meta.icon" class="callout-icon" :size="20" />
      <span>{{ text }}</span>
    </p>
    <!-- HTML is sanitized by the backend (nh3) -->
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-if="html" class="prose callout-body" v-html="html" />
    <div v-else class="callout-body"><slot /></div>
  </aside>
</template>
