<script setup lang="ts">
import type { Guide } from '~/types/guide'

/**
 * Head of the reading templates: type label, title (44px), subtitle (19px), meta chips,
 * introduction, actions (one primary button at most) and the "before you start" box.
 */
defineProps<{ guide: Guide; count?: number; locked?: boolean }>()
const t = useGuideLabels()
</script>

<template>
  <header class="guide-header">
    <p class="guide-kicker">
      <span class="type-label" :lang="t.lang">{{ t.types[guide.guide_type] }}</span>
      <span v-if="guide.category" class="tag">{{ guide.category.name }}</span>
      <span v-if="locked" class="badge-locked" lang="en">locked</span>
    </p>
    <h1 class="guide-title">{{ guide.title }}</h1>
    <p v-if="guide.subtitle" class="guide-subtitle">{{ guide.subtitle }}</p>
    <MetaChips :difficulty="guide.difficulty" :duration="guide.duration_minutes" :guide-type="guide.guide_type" :count="count" />
    <p v-if="guide.summary" class="guide-intro">{{ guide.summary }}</p>
    <div v-if="$slots.actions" class="guide-actions"><slot name="actions" /></div>
    <div v-if="$slots.tools" class="guide-tools-row" lang="en"><slot name="tools" /></div>

  </header>
</template>
