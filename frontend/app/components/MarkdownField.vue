<script setup lang="ts">
import * as edit from '~/utils/markdownEdit'
import type { StyleKind } from '~/utils/textStyles'

/**
 * Textarea for a Markdown field, with a small formatting toolbar (bold, italic, code, list,
 * link and the text styles colour, highlight and font) and a character counter near the
 * limit. The toolbar writes plain Markdown (and <span class="…"> for text styles), so the
 * field stays a normal text field.
 */
const model = defineModel<string>({ required: true })
withDefaults(
  defineProps<{ id: string; label: string; maxlength: number; rows?: number; optional?: boolean; hint?: string; placeholder?: string; toolbar?: boolean }>(),
  { rows: 3, optional: false, hint: '', placeholder: '', toolbar: true },
)

const area = ref<HTMLTextAreaElement | null>(null)
const selection = reactive({ start: 0, end: 0 })
function remember() {
  if (!area.value) return
  selection.start = area.value.selectionStart
  selection.end = area.value.selectionEnd
}

/** Runs an edit on the current selection, then puts the cursor back */
async function run(change: (text: string, start: number, end: number) => edit.Edit) {
  const el = area.value
  if (!el) return
  const result = change(model.value, el.selectionStart, el.selectionEnd)
  model.value = result.text
  await nextTick()
  el.focus()
  el.setSelectionRange(result.start, result.end)
  remember()
}

const currentStyles = computed(() => edit.stylesOf(model.value.slice(selection.start, selection.end)))
const onStyle = (kind: StyleKind, value: string | null) => run((t, s, e) => edit.applyStyle(t, s, e, kind, value))

const TOOLS = [
  { title: 'Bold', label: 'B', run: () => run((t, s, e) => edit.wrap(t, s, e, '**', '**', 'bold text')) },
  { title: 'Italic', label: 'I', run: () => run((t, s, e) => edit.wrap(t, s, e, '*', '*', 'italic text')) },
  { title: 'Code', label: '</>', run: () => run((t, s, e) => edit.wrap(t, s, e, '`', '`', 'code')) },
  { title: 'List', label: '• List', run: () => run(edit.toggleList) },
  { title: 'Link', label: 'Link', run: () => run(edit.link) },
]
</script>

<template>
  <div class="md-field">
    <label :for="id">{{ label }} <span v-if="optional" class="muted">(optional)</span></label>
    <div v-if="toolbar" class="md-toolbar" role="toolbar" :aria-label="`Format ${label.toLowerCase()}`" :aria-controls="id">
      <button v-for="tool in TOOLS" :key="tool.title" type="button" :title="tool.title" :aria-label="tool.title" :data-tool="tool.title" @mousedown.prevent @click="tool.run">
        {{ tool.label }}
      </button>
      <TextStyleMenu :current="currentStyles" @apply="onStyle" />
    </div>
    <textarea
      :id="id"
      ref="area"
      v-model="model"
      :rows="rows"
      :maxlength="maxlength"
      :placeholder="placeholder"
      :aria-describedby="hint ? `${id}-hint` : undefined"
      @select="remember"
      @keyup="remember"
      @mouseup="remember"
      @blur="remember"
    />
    <p class="field-meta">
      <span v-if="hint" :id="`${id}-hint`">{{ hint }}</span>
      <span v-if="model.length > maxlength * 0.8" class="counter">{{ model.length }} / {{ maxlength }}</span>
    </p>
  </div>
</template>
