<script setup lang="ts">
/**
 * Layout of the guide builder, modelled on a design tool: an options bar on top (edit buttons and
 * the active tool), the tools in a column on the left, the guide itself (the canvas) in the middle
 * and a panel on the right with four tabs: Properties of the selected element, Outline of the
 * guide, Checks (suggestions before publishing) and Help for the chosen tool. On narrower panes
 * the panel takes the place of the tools while an element is selected; on phones the tools are a
 * sheet and the panel replaces the canvas.
 */
const props = defineProps<{ editing: boolean }>()
const tab = defineModel<'props' | 'outline' | 'checks' | 'help'>('tab', { default: 'props' })
const slots = useSlots()
const { drag } = useBuilderContext()

const tabs = computed(() => [
  { id: 'props' as const, label: 'Properties' },
  ...(slots.outline ? [{ id: 'outline' as const, label: 'Outline' }] : []),
  ...(slots.checks ? [{ id: 'checks' as const, label: 'Checks' }] : []),
  ...(slots.help ? [{ id: 'help' as const, label: 'Help' }] : []),
])

// Choosing an element shows its properties
watch(() => props.editing, (now) => {
  if (now) tab.value = 'props'
})
</script>

<template>
  <div class="steps-ed-wrap">
    <div class="builder" :class="{ 'is-dragging': drag, 'is-editing': editing }">
      <div v-if="$slots.options" class="bd-options"><slot name="options" /></div>
      <div class="bd-side"><slot name="palette" /></div>
      <div class="bd-main"><slot /></div>
      <div class="bd-props">
        <div v-if="tabs.length > 1" class="bd-tabs" role="tablist" aria-label="Side panel">
          <button
            v-for="t in tabs"
            :id="`bd-tab-${t.id}`"
            :key="t.id"
            type="button"
            role="tab"
            class="bd-tab"
            :class="{ 'is-active': tab === t.id }"
            :aria-selected="tab === t.id"
            aria-controls="bd-tabpanel"
            @click="tab = t.id"
          >
            {{ t.label }}
          </button>
        </div>
        <div id="bd-tabpanel" role="tabpanel" :aria-labelledby="`bd-tab-${tab}`">
          <template v-if="tab === 'props'">
            <slot v-if="editing" name="panel" />
            <div v-else class="bd-props-empty">
              <p class="bd-props-title">Properties</p>
              <p class="muted small">Select an element in the guide to edit it here.</p>
            </div>
          </template>
          <div v-else-if="tab === 'outline'" class="bd-outline"><slot name="outline" /></div>
          <div v-else-if="tab === 'checks'" class="bd-checks"><slot name="checks" /></div>
          <div v-else class="bd-help"><slot name="help" /></div>
        </div>
      </div>
    </div>
  </div>
</template>
