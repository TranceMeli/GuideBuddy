<script setup lang="ts">
/**
 * Editing buttons above the builder, like the toolbar of a drawing tool: undo and redo for the
 * whole guide, and duplicate, move and delete for the selected element. Every button has a text
 * (hidden on narrow panes, then it stays as the accessible name) and its keyboard shortcut.
 */
defineProps<{
  canUndo: boolean
  canRedo: boolean
  hasSelection: boolean
  canUp: boolean
  canDown: boolean
  savedAt?: string
}>()
defineEmits<{ undo: []; redo: []; duplicate: []; up: []; down: []; remove: [] }>()
</script>

<template>
  <div class="bd-tb" role="toolbar" aria-label="Edit">
    <button type="button" class="bd-tb-btn" :disabled="!canUndo" title="Undo (Ctrl+Z)" @click="$emit('undo')">
      <GuideIcon name="undo" :size="16" /><span class="bd-tb-label">Undo</span>
    </button>
    <button type="button" class="bd-tb-btn" :disabled="!canRedo" title="Redo (Ctrl+Y)" @click="$emit('redo')">
      <GuideIcon name="redo" :size="16" /><span class="bd-tb-label">Redo</span>
    </button>
    <span class="bd-tb-sep" aria-hidden="true" />
    <button type="button" class="bd-tb-btn" :disabled="!hasSelection" title="Duplicate (Ctrl+D)" @click="$emit('duplicate')">
      <GuideIcon name="copy" :size="16" /><span class="bd-tb-label">Duplicate</span>
    </button>
    <button type="button" class="bd-tb-btn" :disabled="!canUp" title="Move up (Alt+Up)" @click="$emit('up')">
      <GuideIcon name="arrow-up" :size="16" /><span class="bd-tb-label">Up</span>
    </button>
    <button type="button" class="bd-tb-btn" :disabled="!canDown" title="Move down (Alt+Down)" @click="$emit('down')">
      <GuideIcon name="arrow-down" :size="16" /><span class="bd-tb-label">Down</span>
    </button>
    <button type="button" class="bd-tb-btn" :disabled="!hasSelection" title="Delete (Delete key)" @click="$emit('remove')">
      <GuideIcon name="trash" :size="16" /><span class="bd-tb-label">Delete</span>
    </button>
    <span v-if="savedAt" class="bd-tb-saved" role="status"><GuideIcon name="check" :size="14" /> Draft saved {{ savedAt }}</span>
  </div>
</template>
