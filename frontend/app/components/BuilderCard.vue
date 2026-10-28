<script setup lang="ts">
import type { IconName } from '~/components/GuideIcon.vue'

/**
 * One part in the big box of a building-block editor: a compact card with the kind of part
 * and one line of its content (or its placeholder in grey italics while it is empty). A click
 * selects the part so its writing field opens; the grip drags it, the x removes it.
 * `number` shows a numbered badge (steps, problems, questions) instead of the icon;
 * `status` marks empty and incomplete parts by shape, not by colour alone.
 */
const props = defineProps<{
  icon: IconName
  label: string
  summary?: string
  placeholder?: string
  selected?: boolean
  child?: boolean
  status?: 'empty' | 'partial' | 'done'
  number?: number | string
  drag?: { what: string; key: string }
  removeLabel: string
  tag?: string
}>()
defineEmits<{ select: []; remove: [] }>()

const { startDrag, endDrag } = useBuilderContext()
const el = ref<HTMLElement | null>(null)
</script>

<template>
  <div ref="el" class="bd-card" :class="{ 'is-selected': selected, 'is-child': child, [`is-${status}`]: Boolean(status) }">
    <span
      v-if="drag"
      class="bd-grip"
      draggable="true"
      title="Drag to move"
      aria-hidden="true"
      @dragstart="startDrag($event, { kind: 'move', what: drag.what, key: drag.key }, el)"
      @dragend="endDrag"
    ><GuideIcon name="grip" :size="16" /></span>
    <button type="button" class="bd-card-main" :aria-pressed="selected" @click="$emit('select')">
      <span v-if="number !== undefined" class="ed-num" :data-state="status ?? 'done'" aria-hidden="true">{{ number }}</span>
      <GuideIcon v-else :name="icon" :size="16" class="bd-card-icon" />
      <span class="bd-card-text">
        <span class="bd-card-label">{{ label }}<span v-if="tag" class="bd-tag">{{ tag }}</span></span>
        <span class="bd-card-summary" :class="{ 'is-empty': !summary }">{{ summary || placeholder }}</span>
      </span>
    </button>
    <button type="button" class="bd-x bd-x-inline" :aria-label="props.removeLabel" @click.stop="$emit('remove')">
      <GuideIcon name="close" :size="16" />
    </button>
  </div>
</template>
