<script setup lang="ts">
/** Shows the message of useToast() at the bottom of the screen and hides it after six seconds. */
const { current, dismiss } = useToast()
let timer: ReturnType<typeof setTimeout> | undefined

watch(current, (message) => {
  clearTimeout(timer)
  if (message) timer = setTimeout(dismiss, 6000)
})
onBeforeUnmount(() => clearTimeout(timer))
</script>

<template>
  <div class="toast-region" role="status" aria-live="polite">
    <div v-if="current" :key="current.id" class="toast">
      <GuideIcon name="check-circle" :size="20" class="toast-icon" />
      <span class="toast-text">{{ current.text }}</span>
      <NuxtLink v-if="current.link" :to="current.link.to" class="toast-link" @click="dismiss">{{ current.link.label }}</NuxtLink>
      <button type="button" class="toast-close" aria-label="Close message" @click="dismiss"><GuideIcon name="close" :size="16" /></button>
    </div>
  </div>
</template>
