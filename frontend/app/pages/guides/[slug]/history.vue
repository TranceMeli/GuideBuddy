<script setup lang="ts">
import type { GuideHistory, HistoryEntry } from '~/types/guide'

const route = useRoute()
const slug = route.params.slug as string
const base = useApiBase()

const { data: history, error } = await useFetch<GuideHistory>(`${base}/guides/${slug}/history/`, {
  key: `guide-history-${slug}`,
})

if (!history.value) {
  throw createError({
    statusCode: error.value?.statusCode === 404 || !error.value ? 404 : 502,
    statusMessage: 'Guide not found',
    fatal: true,
  })
}

useSeoMeta({ title: 'History', robots: 'noindex' })

const guideTypes: Record<HistoryEntry['type'], string> = {
  created: 'created',
  changed: 'changed',
  deleted: 'deleted',
}
const stepTypes: Record<HistoryEntry['type'], string> = {
  created: 'added',
  changed: 'changed',
  deleted: 'removed',
}

function formatDate(value: string) {
  return new Date(value).toLocaleString('en-GB', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'Europe/Berlin',
  })
}
</script>

<template>
  <div v-if="history">
    <h1>History: <NuxtLink :to="`/guides/${slug}`">back to the guide</NuxtLink></h1>

    <h2>Changes to the guide</h2>
    <table>
      <thead>
        <tr><th>Date</th><th>By</th><th>Type</th><th>Change</th><th>Title at that time</th><th>Attachment</th></tr>
      </thead>
      <tbody>
        <tr v-for="(entry, i) in history.guide" :key="i">
          <td>{{ formatDate(entry.date) }}</td>
          <td>{{ entry.user ?? '–' }}</td>
          <td>{{ guideTypes[entry.type] }}</td>
          <td>{{ entry.reason || '–' }}</td>
          <td>{{ entry.title }}</td>
          <td>{{ entry.attachment ?? '–' }}</td>
        </tr>
        <tr v-if="!history.guide.length">
          <td colspan="6" class="muted">No changes yet.</td>
        </tr>
      </tbody>
    </table>

    <h2>Changes to steps</h2>
    <table>
      <thead>
        <tr><th>Date</th><th>By</th><th>Type</th><th>Step</th></tr>
      </thead>
      <tbody>
        <tr v-for="(entry, i) in history.steps" :key="i">
          <td>{{ formatDate(entry.date) }}</td>
          <td>{{ entry.user ?? '–' }}</td>
          <td>{{ stepTypes[entry.type] }}</td>
          <td>{{ entry.order }}. {{ entry.title }}</td>
        </tr>
        <tr v-if="!history.steps.length">
          <td colspan="4" class="muted">No changes yet.</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
