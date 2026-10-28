<script setup lang="ts">
import type { BuilderPart } from '~/composables/useBuilder'

/**
 * Place between two parts of a building-block editor. It is a drop target: while a part it
 * `accepts` is dragged it grows and shows a dashed line. With `insert` it also shows a small
 * "+" on hover or keyboard focus that opens a menu of the parts that make sense at this spot,
 * so nobody has to carry a part over from the palette. With `place` (a tool is chosen) it
 * shows a "Place here" button instead. With slot content (e.g. a "+ Step"
 * button) it keeps its size and highlights that content instead.
 */
const props = defineProps<{ id: string; accepts: boolean; insert?: BuilderPart[]; place?: string }>()
const emit = defineEmits<{ drop: []; pick: [id: string]; place: [] }>()
const slots = useSlots()
const { drag, over, endDrag } = useBuilderContext()

const menuOpen = ref(false)
const root = ref<HTMLElement | null>(null)

function onOver(event: DragEvent) {
  if (!drag.value || !props.accepts) return
  event.preventDefault()
  event.stopPropagation()
  over.value = props.id
}
function onDrop(event: DragEvent) {
  if (!props.accepts) return
  event.preventDefault()
  event.stopPropagation()
  emit('drop')
  endDrag()
}
function pick(id: string) {
  menuOpen.value = false
  emit('pick', id)
}

function onDocumentClick(event: MouseEvent) {
  if (menuOpen.value && !root.value?.contains(event.target as Node)) menuOpen.value = false
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') menuOpen.value = false
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
  <div
    ref="root"
    class="bd-gap"
    :class="{ 'can-drop': drag && accepts, 'is-over': over === id, 'has-content': slots.default, 'has-place': place, 'has-insert': insert?.length && !slots.default && !place, 'menu-open': menuOpen }"
    @dragover="onOver"
    @dragleave="over === id && (over = '')"
    @drop="onDrop"
  >
    <slot />
    <button v-if="place" type="button" class="bd-place" @click="emit('place')">
      <GuideIcon name="plus" :size="14" /> {{ place }}
    </button>
    <template v-if="insert?.length && !slots.default && !place">
      <button type="button" class="bd-plus" :aria-expanded="menuOpen" aria-label="Add a part here" title="Add a part here" @click.stop="menuOpen = !menuOpen">
        <GuideIcon name="plus" :size="14" />
      </button>
      <div v-if="menuOpen" class="bd-menu" role="menu" aria-label="Add a part here">
        <button v-for="part in insert" :key="part.id" type="button" role="menuitem" class="bd-menu-item" @click="pick(part.id)">
          <GuideIcon :name="part.icon" :size="16" /> {{ part.label }}
        </button>
      </div>
    </template>
  </div>
</template>
