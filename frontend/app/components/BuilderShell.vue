<script setup lang="ts">
/**
 * Layout of the guide builder, modelled on a design tool: an options bar for the active tool
 * on top, the tools in a column on the left, the guide itself (the canvas) in the middle and
 * the properties of the selected element on the right. On narrower panes the properties take
 * the place of the tools while an element is selected; on phones the tools are a sheet and
 * the properties replace the canvas.
 */
defineProps<{ editing: boolean }>()
const { drag } = useBuilderContext()
</script>

<template>
  <div class="steps-ed-wrap">
    <div class="builder" :class="{ 'is-dragging': drag, 'is-editing': editing }">
      <div v-if="$slots.options" class="bd-options"><slot name="options" /></div>
      <div class="bd-side"><slot name="palette" /></div>
      <div class="bd-main"><slot /></div>
      <div class="bd-props">
        <div v-if="$slots.help" class="bd-help"><slot name="help" /></div>
        <slot v-if="editing" name="panel" />
        <div v-else class="bd-props-empty">
          <p class="bd-props-title">Properties</p>
          <p class="muted small">Select an element in the guide to edit it here.</p>
        </div>
      </div>
    </div>
  </div>
</template>
