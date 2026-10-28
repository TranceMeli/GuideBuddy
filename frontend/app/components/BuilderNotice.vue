<script setup lang="ts">
/**
 * Notice line of a building-block editor: short hints ("A question needs at least two
 * answers.") and, after a removal, an "Undo" button for a few seconds.
 */
const { notice, undoAction, undo } = useBuilderContext()
</script>

<template>
  <p class="bd-notice" role="status">
    <span>{{ notice }}</span>
    <button v-if="undoAction" type="button" class="bd-undo" @click="undo">Undo</button>
  </p>
</template>
