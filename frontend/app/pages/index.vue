<script setup lang="ts">
useSeoMeta({
  title: 'Discover guides',
  description: 'Step-by-step guides on any topic – free to read and to download as PDF.',
})

// One-time notice from another page, e.g. after deleting a guide
const flash = useState<string>('flash', () => '')
const notice = flash.value
flash.value = ''
</script>

<template>
  <div>
    <p v-if="notice" class="ok-box" role="status">{{ notice }}</p>
    <GuideBrowser heading="Discover guides" />
  </div>
</template>
