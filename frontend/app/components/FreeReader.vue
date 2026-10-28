<script setup lang="ts">
import type { Guide } from '~/types/guide'

/** "Freier Guide / Datei": rich-text steps and/or one attached file. */
defineProps<{ guide: Guide; preview?: boolean }>()
const t = useGuideLabels()
</script>

<template>
  <div class="free-reader">
    <ol v-if="guide.steps.length" class="free-steps">
      <li v-for="(step, i) in guide.steps" :key="step.id ?? i" class="step-card is-active">
        <header class="step-head">
          <StepBadge :number="i + 1" />
          <h2 class="step-title">{{ step.title }}</h2>
        </header>
        <!-- body_html is sanitized by the backend with nh3 (no scripts possible) -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="prose reading" v-html="step.body_html" />
      </li>
    </ol>
    <AttachmentViewer
      v-else-if="guide.attachment_info && !preview"
      :kind="guide.attachment_info.kind"
      :name="guide.attachment_info.name"
      :src="guide.attachment_info.view_url"
      :html="guide.attachment_info.preview_html"
      :download-url="guide.attachment_info.download_url"
    />
    <p v-else class="muted" :lang="t.lang">{{ t.noContent }}</p>
  </div>
</template>
