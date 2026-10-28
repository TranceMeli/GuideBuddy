<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const notFound = computed(() => props.error.statusCode === 404)
const forbidden = computed(() => props.error.statusCode === 403)
const title = computed(() =>
  notFound.value ? 'Page not found' : forbidden.value ? 'Access denied' : 'Something went wrong',
)
useHead({ title: title.value })
</script>

<template>
  <NuxtLayout>
    <h1>{{ title }}</h1>
    <p class="muted">
      {{
        notFound
          ? 'This page does not exist (anymore).'
          : forbidden
            ? 'You do not have permission to view this page.'
            : 'The server has a problem right now. Please try again later.'
      }}
    </p>
    <p><button type="button" class="button" @click="clearError({ redirect: '/' })">Go to the home page</button></p>
  </NuxtLayout>
</template>
