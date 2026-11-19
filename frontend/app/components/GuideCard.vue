<script setup lang="ts">
import type { GuideListItem } from '~/types/guide'

/**
 * Card of the guide overview: preview image (140px, or a placeholder with a line
 * illustration for the category or guide type), category label with icon, title, summary,
 * chips for level, duration and number of steps. The card carries the colour of its category
 * (a line on top and a tint), and the whole card is one link.
 */
const props = defineProps<{ guide: GuideListItem }>()
const chipLabels = computed(() => labelsFor(props.guide.language))
const placeholder = computed(() => placeholderFor(props.guide.category?.slug, props.guide.guide_type, props.guide.slug))
</script>

<template>
  <li class="guide-card" :class="`tint-${placeholder.tint}`">
    <div class="card-image" :class="guide.cover_image ? undefined : 'is-placeholder'">
      <img v-if="guide.cover_image" :src="guide.cover_image.url" :alt="guide.cover_image.alt" loading="lazy">
      <span v-else class="card-image-icon"><GuideIcon :name="placeholder.icon" :size="44" /></span>
    </div>
    <div class="card-body">
      <p class="card-kicker"><GuideIcon :name="placeholder.icon" :size="16" /> {{ guide.category?.name ?? 'Guide' }}</p>
      <h2 class="card-title" :lang="guide.language">
        <NuxtLink :to="`/guides/${guide.slug}`" class="card-link">{{ guide.title }}</NuxtLink>
      </h2>
      <p v-if="guide.status === 'outdated'" class="status-chip status-caution" lang="en"><GuideIcon name="alert" :size="14" /> Outdated</p>
      <p v-if="guide.summary" class="card-summary" :lang="guide.language">{{ guide.summary }}</p>
      <MetaChips
        :difficulty="guide.difficulty"
        :duration="guide.duration_minutes"
        :guide-type="guide.guide_type"
        :count="guide.step_count"
        :has-pdf="guide.has_pdf"
        :labels="chipLabels"
      />
    </div>
  </li>
</template>
