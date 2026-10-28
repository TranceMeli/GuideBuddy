<script setup lang="ts">
const { mode, label, next } = useTheme()
const icon = computed(() => ({ auto: '◐', light: '☀', dark: '☾' })[mode.value])
</script>

<template>
  <button
    type="button"
    class="theme"
    :aria-label="`Theme: ${label}. Click to change.`"
    :title="`Theme: ${label}`"
    @click="next"
  >
    <span aria-hidden="true">{{ icon }}</span> {{ label }}
  </button>
</template>
