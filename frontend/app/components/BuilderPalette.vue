<script setup lang="ts">
import type { BuilderGroup } from '~/composables/useBuilder'

/**
 * The tools of the builder. Wide panes: a column of tool buttons in groups, with the keyboard
 * shortcut next to each. A tool is chosen by clicking it (or its key) and then used on the
 * guide; the chosen tool is highlighted. Narrow panes: a "Tools" sheet above the publish
 * bar. `used` marks parts that are already in the guide; `disabled` returns the reason a
 * tool cannot be used right now ("" = usable).
 */
const props = defineProps<{
  groups: BuilderGroup[]
  armed?: string
  used?: (id: string) => boolean
  disabled?: (id: string) => string
}>()
const emit = defineEmits<{ add: [id: string]; hover: [id: string | null] }>()
const { startDrag, endDrag, sheetOpen, say } = useBuilderContext()

function pick(id: string) {
  const reason = props.disabled?.(id)
  if (reason) return say(reason)
  emit('add', id)
  sheetOpen.value = false
}
</script>

<template>
  <aside class="bd-palette bd-palette--side" :class="{ 'is-open': sheetOpen }" aria-label="Tools">
    <button type="button" class="bd-sheet-toggle" :aria-expanded="sheetOpen" aria-controls="bd-palette-body" @click="sheetOpen = !sheetOpen">
      <GuideIcon :name="sheetOpen ? 'close' : 'plus'" :size="18" />
      {{ sheetOpen ? 'Close tools' : 'Tools' }}
    </button>
    <div id="bd-palette-body" class="bd-palette-body">
      <div v-for="group in groups" :key="group.group" class="bd-palette-group">
        <p class="bd-group">{{ group.group }}</p>
        <ul class="bd-parts">
          <li v-for="part in group.parts" :key="part.id">
            <button
              type="button"
              class="bd-part"
              :class="{ 'is-used': used?.(part.id), 'is-disabled': disabled?.(part.id), 'is-armed': armed === part.id }"
              :draggable="!disabled?.(part.id) && part.id !== 'select'"
              :aria-pressed="armed === part.id"
              :aria-disabled="disabled?.(part.id) ? true : undefined"
              :title="disabled?.(part.id) || part.hint"
              :aria-describedby="`bd-hint-${part.id}`"
              @click="pick(part.id)"
              @mouseenter="emit('hover', part.id)"
              @mouseleave="emit('hover', null)"
              @focus="emit('hover', part.id)"
              @blur="emit('hover', null)"
              @dragstart="disabled?.(part.id) || part.id === 'select' ? $event.preventDefault() : startDrag($event, { kind: 'new', part: part.id })"
              @dragend="endDrag"
            >
              <GuideIcon :name="part.icon" :size="16" />
              <span class="bd-part-label">{{ part.label }}</span>
              <GuideIcon v-if="used?.(part.id)" name="check" :size="14" class="bd-part-used" />
              <kbd v-if="part.shortcut" class="bd-key" aria-hidden="true">{{ part.shortcut }}</kbd>
              <span :id="`bd-hint-${part.id}`" class="visually-hidden">{{ part.hint }}{{ part.shortcut ? ` (shortcut ${part.shortcut})` : '' }}{{ used?.(part.id) ? ' (already added)' : '' }}{{ disabled?.(part.id) ? ` (not available: ${disabled(part.id)})` : '' }}</span>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </aside>
</template>
