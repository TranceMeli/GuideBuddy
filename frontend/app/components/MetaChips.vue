<script setup lang="ts">
import type { GuideType } from '~/types/guide'
import type { GuideLabels } from '~/utils/guideLabels'

/**
 * Key facts as pills: level, duration, number of steps/problems/…, PDF.
 * --primary-light pills. Labels follow `labels`
 * (the guide's language in reading templates, English on the overview).
 */
const props = defineProps<{
  difficulty?: string
  duration?: number | null
  guideType?: GuideType
  count?: number
  hasPdf?: boolean
  labels?: GuideLabels
}>()

const injected = useGuideLabels()
const t = computed(() => props.labels ?? injected.value)
const levelNumber = computed(() => ({ beginner: 1, intermediate: 2, advanced: 3 })[props.difficulty ?? ''] ?? 0)
const countText = computed(() => {
  if (!props.count || !props.guideType) return ''
  const [one, many] = t.value.count[props.guideType] ?? ['', '']
  return `${props.count} ${props.count === 1 ? one : many}`
})
</script>

<template>
  <ul class="meta-chips" :aria-label="`${t.level}, ${t.duration}`" :lang="t.lang">
    <li v-if="levelNumber" class="meta-chip meta-chip--level">
      <span class="level-bars" :data-level="levelNumber" aria-hidden="true"><i /><i /><i /></span>
      <span><span class="visually-hidden">{{ t.level }}: </span>{{ t.levels[difficulty!] }}</span>
    </li>
    <li v-if="duration" class="meta-chip">
      <GuideIcon name="clock" :size="16" />
      <span><span class="visually-hidden">{{ t.duration }}: </span>{{ formatDuration(duration) }}</span>
    </li>
    <li v-if="countText" class="meta-chip">
      <GuideIcon name="steps" :size="16" />
      <span>{{ countText }}</span>
    </li>
    <li v-if="hasPdf" class="meta-chip">
      <GuideIcon name="file" :size="16" />
      <span>PDF</span>
    </li>
  </ul>
</template>
