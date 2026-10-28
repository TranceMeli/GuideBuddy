<script setup lang="ts">
import type { Category, Guide } from '~/types/guide'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const slug = route.params.slug as string
const base = useApiBase()

const { data: guide, error } = await useFetch<Guide>(`${base}/guides/${slug}/`, {
  key: `guide-edit-${slug}`,
})
const { data: categories } = await useFetch<Category[]>(`${base}/categories/`, { key: 'categories' })

if (!guide.value) {
  throw createError({
    statusCode: error.value?.statusCode === 404 || !error.value ? 404 : 502,
    statusMessage: 'Guide not found',
    fatal: true,
  })
}

useSeoMeta({ title: `Edit ${guide.value.title}`, robots: 'noindex' })
</script>

<template>
  <div v-if="guide">
    <h1>Edit “<span :lang="guide.language">{{ guide.title }}</span>”</h1>
    <GuideEditor v-if="guide.guide_type === 'free'" :guide="guide" :categories="categories ?? []" />
    <StructuredGuideEditor v-else :guide="guide" :categories="categories ?? []" />
  </div>
</template>
