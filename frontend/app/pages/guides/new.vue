<script setup lang="ts">
import type { Category } from '~/types/guide'

definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'New guide', robots: 'noindex' })

const base = useApiBase()
const route = useRoute()
const { data: categories } = await useFetch<Category[]>(`${base}/categories/`, { key: 'categories' })

// One kind of guide, built with the tools. ?file=1 is the way to publish an existing file instead.
const fileMode = computed(() => route.query.file === '1')
</script>

<template>
  <div>
    <h1>New guide</h1>
    <p class="muted small">
      <template v-if="!fileMode">
        Choose tools on the left and place them in your guide.
        Already have a finished document?
        <NuxtLink :to="{ query: { file: '1' } }">Upload a file instead</NuxtLink>
      </template>
      <template v-else>
        Uploading a file or pasting finished text.
        <NuxtLink :to="{ query: {} }">Build a guide with the tools instead</NuxtLink>
      </template>
    </p>
    <GuideEditor v-if="fileMode" :categories="categories ?? []" />
    <StructuredGuideEditor v-else :categories="categories ?? []" />
  </div>
</template>
