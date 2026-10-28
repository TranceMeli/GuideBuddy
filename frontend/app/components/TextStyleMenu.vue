<script setup lang="ts">
import { STYLE_LABELS, STYLE_OPTIONS, type StyleKind } from '~/utils/textStyles'

/**
 * Picker for the text styles: three small menus (colour, highlight, font). It only reports
 * the choice; the rich text editor and the Markdown fields apply it. The panel names every
 * option in words, so nothing depends on seeing the colour.
 */
defineProps<{ current?: Partial<Record<StyleKind, string | null>> }>()
const emit = defineEmits<{ apply: [kind: StyleKind, value: string | null] }>()

const KINDS: StyleKind[] = ['color', 'highlight', 'font']
const open = ref<StyleKind | null>(null)
const root = ref<HTMLElement | null>(null)

function pick(kind: StyleKind, value: string | null) {
  emit('apply', kind, value)
  open.value = null
}

function onDocumentClick(event: MouseEvent) {
  if (open.value && !root.value?.contains(event.target as Node)) open.value = null
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') open.value = null
}
onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <span ref="root" class="tsm">
    <span v-for="kind in KINDS" :key="kind" class="tsm-item">
      <button
        type="button"
        class="tsm-button"
        :class="{ 'is-active': current?.[kind] }"
        :aria-expanded="open === kind"
        :aria-haspopup="true"
        :title="STYLE_LABELS[kind]"
        @mousedown.prevent
        @click="open = open === kind ? null : kind"
      >
        <span v-if="kind === 'color'" class="tsm-a" aria-hidden="true">A</span>
        <span v-else-if="kind === 'highlight'" class="tsm-mark" aria-hidden="true">ab</span>
        <span v-else class="tsm-font" aria-hidden="true">Aa</span>
        <span class="tsm-label">{{ STYLE_LABELS[kind] }}</span>
        <span v-if="current?.[kind]" class="visually-hidden">: {{ STYLE_OPTIONS[kind].find((o) => o.value === current?.[kind])?.label }}</span>
      </button>
      <div v-if="open === kind" class="tsm-panel" role="menu" :aria-label="STYLE_LABELS[kind]">
        <button
          v-for="option in STYLE_OPTIONS[kind]"
          :key="option.value"
          type="button"
          role="menuitemradio"
          class="tsm-option"
          :class="{ 'is-current': current?.[kind] === option.value }"
          :aria-checked="current?.[kind] === option.value"
          @mousedown.prevent
          @click="pick(kind, current?.[kind] === option.value ? null : option.value)"
        >
          <span v-if="option.swatch" class="tsm-swatch" :style="{ background: option.swatch }" aria-hidden="true" />
          <span :class="kind === 'font' ? option.value : undefined">{{ option.label }}</span>
          <GuideIcon v-if="current?.[kind] === option.value" name="check" :size="14" class="tsm-check" />
        </button>
        <button type="button" role="menuitem" class="tsm-option tsm-none" @mousedown.prevent @click="pick(kind, null)">
          None
        </button>
      </div>
    </span>
  </span>
</template>
