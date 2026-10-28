<script setup lang="ts">
import type { AttachmentKind } from '~/types/guide'

/** Shows an attached file: embedded PDF, image, or prepared HTML (Word, text …). */
defineProps<{
  kind: AttachmentKind
  name: string
  src?: string | null // address for PDF/image (also a blob: URL before uploading)
  html?: string // sanitized by the backend (nh3)
  downloadUrl?: string
}>()
</script>

<template>
  <figure class="file-viewer">
    <iframe v-if="kind === 'pdf' && src" :src="src" :title="name" class="file-viewer-pdf" />
    <img v-else-if="kind === 'image' && src" :src="src" :alt="name" class="file-viewer-image">
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-else-if="kind === 'html' && html" class="prose file-viewer-doc" v-html="html" />
    <p v-else class="file-viewer-empty muted">
      There is no preview for this format.
      <template v-if="downloadUrl">Please <a :href="downloadUrl" download>download the file</a>.</template>
    </p>
    <figcaption class="muted small">
      <GuideIcon name="file" :size="16" class="file-viewer-icon" /> {{ name }}
      <template v-if="downloadUrl"> · <a :href="downloadUrl" download>Download</a></template>
      <template v-if="kind === 'pdf' && src"> · <a :href="src" target="_blank" rel="noopener">Open in a new tab</a></template>
    </figcaption>
  </figure>
</template>
