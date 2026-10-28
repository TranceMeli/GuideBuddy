<script setup lang="ts">
import type { Paginated, Report } from '~/types/guide'

definePageMeta({ middleware: 'moderator' })
useSeoMeta({ title: 'Moderation', robots: 'noindex' })

const filter = ref<'open' | 'resolved'>('open')
const { data, refresh, error } = await useFetch<Paginated<Report> | Report[]>('/api/reports/', {
  key: 'reports',
  query: computed(() => ({ status: filter.value })),
  server: false,
})

const reports = computed<Report[]>(() => {
  const value = data.value
  if (!value) return []
  return Array.isArray(value) ? value : value.results
})

const notes = reactive<Record<number, string>>({})
const message = ref('')
const errors = ref<string[]>([])

async function act(fn: () => Promise<unknown>, ok: string) {
  errors.value = []
  message.value = ''
  try {
    await fn()
    message.value = ok
    clearNuxtData((key) => key.startsWith('guide'))
    await refresh()
  } catch (e) {
    errors.value = apiErrorMessages(e)
  }
}

const resolve = (r: Report) =>
  act(
    () => $fetch<unknown>(`/api/reports/${r.id}/resolve/`, { method: 'POST', body: { note: notes[r.id] ?? '' } }),
    'Report resolved.',
  )
const setLock = (r: Report, lock: boolean) =>
  act(
    () => $fetch<unknown>(`/api/guides/${r.guide}/${lock ? 'lock' : 'unlock'}/`, { method: 'POST' }),
    lock ? 'Guide locked.' : 'Guide unlocked.',
  )
</script>

<template>
  <div>
    <h1>Moderation</h1>
    <p class="chips">
      <a href="#" :aria-current="filter === 'open' ? 'page' : undefined" @click.prevent="filter = 'open'">Open</a>
      <a href="#" :aria-current="filter === 'resolved' ? 'page' : undefined" @click.prevent="filter = 'resolved'">Resolved</a>
    </p>
    <div v-if="message" class="ok-box" role="status">{{ message }}</div>
    <div v-if="errors.length || error" class="error-box" role="alert">
      <ul><li v-for="m in errors" :key="m">{{ m }}</li><li v-if="error">Reports could not be loaded.</li></ul>
    </div>

    <p v-if="!reports.length" class="muted">No reports.</p>
    <article v-for="r in reports" :key="r.id" class="report-card">
      <h2>
        <NuxtLink :to="`/guides/${r.guide}`">{{ r.guide_title }}</NuxtLink>
        <span v-if="r.guide_locked" class="badge-locked">locked</span>
      </h2>
      <p class="muted">
        {{ r.reason_label }} · by {{ r.reporter ?? 'a deleted account' }} ·
        {{ new Date(r.created_at).toLocaleString('en-GB') }}
      </p>
      <p v-if="r.comment">{{ r.comment }}</p>
      <blockquote v-if="r.reported_comment_body" class="muted">Reported comment: {{ r.reported_comment_body }}</blockquote>
      <template v-if="!r.resolved_at">
        <div>
          <label :for="`note-${r.id}`" class="muted">Note (optional)</label>
          <input :id="`note-${r.id}`" v-model="notes[r.id]" type="text" maxlength="200">
        </div>
        <p class="actions">
          <button type="button" class="secondary" @click="resolve(r)">Mark as resolved</button>
          <button v-if="!r.guide_locked" type="button" class="secondary danger" @click="setLock(r, true)">Lock guide</button>
          <button v-else type="button" class="secondary" @click="setLock(r, false)">Unlock guide</button>
        </p>
      </template>
      <p v-else class="muted">
        Resolved by {{ r.resolved_by ?? '?' }}<template v-if="r.resolution_note">: {{ r.resolution_note }}</template>
      </p>
    </article>
  </div>
</template>
