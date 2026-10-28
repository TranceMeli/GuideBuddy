<script setup lang="ts">
// Light/dark mode (data-mode) on <html>
useTheme()

useHead({
  titleTemplate: (title) => (title ? `${title} – GuideBuddy` : 'GuideBuddy'),
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
