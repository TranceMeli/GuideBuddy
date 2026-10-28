<script setup lang="ts">
/**
 * The properties of the selected element (the writing field). On wide panes it sits in its
 * own column; on narrower panes it replaces the tools or the canvas and "Back" or "Done"
 * return to them. The first field is focused on opening.
 */
defineProps<{ title: string }>()
defineEmits<{ done: []; remove: [] }>()

const root = ref<HTMLElement | null>(null)
onMounted(() => {
  // not on touch screens: the keyboard would hide half of the panel before the author asked for it
  if (window.matchMedia?.('(pointer: coarse)').matches) return
  root.value?.querySelector<HTMLElement>('.bd-panel-body input, .bd-panel-body textarea, .bd-panel-body select')?.focus({ preventScroll: true })
})
</script>

<template>
  <section ref="root" class="bd-panel" aria-label="Properties">
    <header class="bd-panel-head">
      <button type="button" class="bd-back" @click="$emit('done')">
        <GuideIcon name="arrow-left" :size="16" /> Back
      </button>
      <h3>{{ title }}</h3>
    </header>
    <div class="bd-panel-body"><slot /></div>
    <footer class="bd-panel-foot">
      <button type="button" class="button bd-done" @click="$emit('done')">Done</button>
      <button type="button" class="secondary danger" @click="$emit('remove')">Remove</button>
    </footer>
  </section>
</template>
