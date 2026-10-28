<script setup lang="ts">
/**
 * Two columns with a draggable divider (wide screens). On narrow screens the second column
 * moves below the first and the divider disappears.
 */
const props = withDefaults(
  defineProps<{ storageKey: string; defaultSplit?: number; min?: number; max?: number; label?: string }>(),
  { defaultSplit: 66, min: 40, max: 80, label: 'Resize columns' },
)

const { split, dragging, root, handleProps } = useSplitDrag({
  storageKey: props.storageKey,
  min: props.min,
  max: props.max,
  initial: props.defaultSplit,
})
</script>

<template>
  <div ref="root" class="resizable-columns" :class="{ 'is-dragging': dragging }" :style="{ '--split': `${split}%` }">
    <div class="resizable-start">
      <slot />
    </div>
    <div class="resizable-handle" v-bind="handleProps" :aria-label="label" :aria-valuetext="`${split} percent`">
      <span class="resizable-grip" aria-hidden="true" />
    </div>
    <div class="resizable-end">
      <slot name="end" />
    </div>
  </div>
</template>
