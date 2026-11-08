<script setup lang="ts">
import type { BuilderGroup } from '~/composables/useBuilder'

/**
 * The tools of the builder. Wide panes: a search field, the tools used last, and a column of tool
 * buttons in groups that fold away, with the keyboard shortcut next to each. A tool is chosen by
 * clicking it (or its key) and then used on the guide; the chosen tool is highlighted. Narrow
 * panes: a "Tools" sheet above the publish bar. `used` marks parts that are already in the guide;
 * `disabled` returns the reason a tool cannot be used right now ("" = usable).
 */
const props = defineProps<{
  groups: BuilderGroup[]
  armed?: string
  recent?: string[]
  used?: (id: string) => boolean
  disabled?: (id: string) => string
}>()
const emit = defineEmits<{ add: [id: string]; hover: [id: string | null] }>()
const { startDrag, endDrag, sheetOpen, say } = useBuilderContext()

const query = ref('')
const folded = ref<Set<string>>(new Set())
const searching = computed(() => query.value.trim().length > 0)

const sections = computed(() => {
  const q = query.value.trim().toLowerCase()
  const byId = new Map(props.groups.flatMap((g) => g.parts).map((p) => [p.id, p]))
  const groups = props.groups
    .map((g) => ({ key: g.group, title: g.group, parts: g.parts.filter((p) => !q || p.label.toLowerCase().includes(q) || p.hint.toLowerCase().includes(q)) }))
    .filter((g) => g.parts.length)
  const recent = (props.recent ?? []).map((id) => byId.get(id)).filter((p): p is NonNullable<typeof p> => Boolean(p))
  return !q && recent.length ? [{ key: 'recent', title: 'Recent', parts: recent }, ...groups] : groups
})

function toggle(key: string) {
  const next = new Set(folded.value)
  if (!next.delete(key)) next.add(key)
  folded.value = next
}
const isOpen = (key: string) => searching.value || !folded.value.has(key)

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
      <div class="bd-search">
        <label for="bd-tool-search" class="visually-hidden">Search tools</label>
        <GuideIcon name="search" :size="16" />
        <input id="bd-tool-search" v-model="query" type="search" placeholder="Search tools" autocomplete="off">
      </div>
      <p v-if="!sections.length" class="muted small bd-no-tool">No tool matches “{{ query }}”.</p>
      <div v-for="section in sections" :key="section.key" class="bd-palette-group">
        <button type="button" class="bd-group bd-group-btn" :aria-expanded="isOpen(section.key)" :aria-controls="`bd-group-${section.key}`" @click="toggle(section.key)">
          <span>{{ section.title }}</span>
          <GuideIcon name="chevron-down" :size="14" class="bd-group-chevron" :class="{ 'is-folded': !isOpen(section.key) }" />
        </button>
        <ul v-show="isOpen(section.key)" :id="`bd-group-${section.key}`" class="bd-parts">
          <li v-for="part in section.parts" :key="part.id">
            <button
              type="button"
              class="bd-part"
              :class="{ 'is-used': used?.(part.id), 'is-disabled': disabled?.(part.id), 'is-armed': armed === part.id }"
              :draggable="!disabled?.(part.id) && part.id !== 'select'"
              :aria-pressed="armed === part.id"
              :aria-disabled="disabled?.(part.id) ? true : undefined"
              :title="disabled?.(part.id) || part.hint"
              :aria-describedby="`bd-hint-${section.key}-${part.id}`"
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
              <span :id="`bd-hint-${section.key}-${part.id}`" class="visually-hidden">{{ part.hint }}{{ part.shortcut ? ` (shortcut ${part.shortcut})` : '' }}{{ used?.(part.id) ? ' (already added)' : '' }}{{ disabled?.(part.id) ? ` (not available: ${disabled(part.id)})` : '' }}</span>
            </button>
          </li>
        </ul>
      </div>
    </div>
  </aside>
</template>
