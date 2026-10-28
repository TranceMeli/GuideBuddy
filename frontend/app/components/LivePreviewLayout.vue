<script setup lang="ts">
/**
 * The editor uses the whole width; "Show preview" puts the live preview on the right, with a
 * draggable divider in between (mouse, touch or arrow keys; double-click resets). The chosen
 * width is remembered in this browser. On narrow screens a switch shows one of the two panes
 * at a time.
 * The preview pane is a size container, so the reading templates use their compact
 * layout when the pane is narrow.
 */
defineProps<{ status?: string }>()

const view = ref<'edit' | 'preview'>('edit')
// Wide screens: the preview is hidden until asked for, so the builder has the room it needs
const previewOn = ref(false)
// Empty parts show a grey placeholder in the preview (see utils/placeholders.ts)
const page = ref<HTMLElement | null>(null)
usePlaceholderHighlights(page)
// split = width of the editor pane in percent
const { split, dragging, root, handleProps } = useSplitDrag({
  storageKey: 'guidebuddy:editor-split',
  min: 25,
  max: 75,
  initial: 50,
})
</script>

<template>
  <div
    ref="root"
    class="live-split"
    :class="{ 'is-dragging': dragging }"
    :data-view="view"
    :data-preview="previewOn ? 'on' : 'off'"
    :style="{ '--split': `${split}%` }"
  >
    <div class="live-switch" role="tablist" aria-label="View">
      <button type="button" role="tab" :aria-selected="view === 'edit'" :class="{ 'is-active': view === 'edit' }" @click="view = 'edit'">
        Edit
      </button>
      <button type="button" role="tab" :aria-selected="view === 'preview'" :class="{ 'is-active': view === 'preview' }" @click="view = 'preview'">
        Preview
      </button>
    </div>

    <button type="button" class="live-toggle" :aria-pressed="previewOn" @click="previewOn = !previewOn">
      <GuideIcon name="eye" :size="16" /> {{ previewOn ? 'Hide preview' : 'Show preview' }}
    </button>

    <div class="live-edit">
      <slot />
    </div>

    <div
      class="live-handle"
      v-bind="handleProps"
      aria-label="Resize editor and preview"
      :aria-valuetext="`Editor ${split} percent`"
    >
      <span class="live-handle-grip" aria-hidden="true" />
    </div>

    <aside class="live-preview" aria-label="Live preview">
      <p class="live-preview-label">
        <span class="live-dot" aria-hidden="true" /> Live preview
        <span v-if="status" class="muted small">· {{ status }}</span>
      </p>
      <div ref="page" class="live-preview-page">
        <slot name="preview" />
      </div>
    </aside>
  </div>
</template>
