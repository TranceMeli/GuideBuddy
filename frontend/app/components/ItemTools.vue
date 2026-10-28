<script setup lang="ts">
/** Move up / move down / remove buttons for one item of an editor list. */
defineProps<{ index: number; count: number; name: string; min?: number }>()
defineEmits<{ up: []; down: []; remove: [] }>()
</script>

<template>
  <span class="item-tools">
    <button type="button" class="icon-button" :disabled="index === 0" :aria-label="`Move ${name} up`" title="Move up" @click="$emit('up')">↑</button>
    <button type="button" class="icon-button" :disabled="index === count - 1" :aria-label="`Move ${name} down`" title="Move down" @click="$emit('down')">↓</button>
    <button type="button" class="icon-button danger" :disabled="count <= (min ?? 1)" :aria-label="`Remove ${name}`" title="Remove" @click="$emit('remove')">✕</button>
  </span>
</template>
