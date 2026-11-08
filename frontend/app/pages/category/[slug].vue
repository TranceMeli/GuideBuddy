<script setup lang="ts">
import type { Category } from '~/types/guide'

const route = useRoute()
const slug = route.params.slug as string

const base = useApiBase()

const { data: categories } = await useFetch<Category[]>(`${base}/categories/`, {
  key: 'categories',
})
const category = computed(() => categories.value?.find((c) => c.slug === slug))

if (!category.value) {
  throw createError({ statusCode: 404, statusMessage: 'Category not found', fatal: true })
}

useSeoMeta({
  title: `Category ${category.value.name}`,
  description: `All guides in the category ${category.value.name}.`,
})
</script>

<template>
  <div>
    <GuideBrowser :category-slug="slug" :heading="`Category: ${category?.name}`" />
  </div>
</template>
