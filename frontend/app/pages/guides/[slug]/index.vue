<script setup lang="ts">
import type { Guide, GuideListItem } from '~/types/guide'

const route = useRoute()
const slug = route.params.slug as string
const config = useRuntimeConfig()
const base = useApiBase()

const { data: guide, error, refresh } = await useFetch<Guide>(`${base}/guides/${slug}/`, {
  key: `guide-${slug}`,
})
const { data: related } = await useFetch<GuideListItem[]>(`${base}/guides/${slug}/related/`, {
  key: `guide-related-${slug}`,
  default: () => [],
})

if (!guide.value) {
  throw createError({
    statusCode: error.value?.statusCode === 404 || !error.value ? 404 : 502,
    statusMessage: 'Guide not found',
    fatal: true,
  })
}

const { loggedIn, isModerator, user, clearSession } = useAuth()
// The comment buttons of the reading view (and the filter of the comments) are only on this page
const commentsOn = useState<boolean>('gb-comments-on', () => false)
commentsOn.value = true
onBeforeUnmount(() => { commentsOn.value = false })

const reportReason = ref('spam')
const reportComment = ref('')
const reportMessage = ref('')
const reportErrors = ref<string[]>([])
const locked = ref(guide.value.is_locked)

async function sendReport() {
  reportErrors.value = []
  try {
    const result = await $fetch<{ detail: string }>(`/api/guides/${slug}/report/`, {
      method: 'POST',
      body: { reason: reportReason.value, comment: reportComment.value },
    })
    reportMessage.value = result.detail
    reportComment.value = ''
  } catch (e) {
    reportErrors.value = apiErrorMessages(e)
  }
}

async function toggleLock() {
  try {
    const result = await $fetch<{ is_locked: boolean }>(
      `/api/guides/${slug}/${locked.value ? 'unlock' : 'lock'}/`,
      { method: 'POST' },
    )
    locked.value = result.is_locked
    clearNuxtData((key) => key.startsWith('guide'))
  } catch (e) {
    reportErrors.value = apiErrorMessages(e)
  }
}

// Same rule as the API (guides/permissions.py): the author and moderators may delete,
// locked guides only moderators. The server checks again; this only decides the button.
const canDelete = computed(() => {
  if (!loggedIn.value || !user.value?.can_write) return false
  if (isModerator.value) return true
  return !locked.value && !!guide.value?.created_by && guide.value.created_by === user.value.username
})
// Anyone who may edit can say that a guide is out of date; archiving follows the delete rule
const canMark = computed(() => loggedIn.value && !!user.value?.can_write && (!locked.value || isModerator.value))
const note = computed(() => (guide.value ? outdatedNote(guide.value.status, guide.value.outdated_reports) : ''))
const deleting = ref(false)
const deleteError = ref('')
const { ask } = useConfirm()
const toast = useToast()

/** Archive, restore or mark a guide; the page shows the new status from the reloaded guide */
async function changeStatus(action: 'archive' | 'restore' | 'mark-outdated' | 'mark-current', message: string) {
  deleteError.value = ''
  try {
    await $fetch(`/api/guides/${slug}/${action}/`, { method: 'POST' })
    await refresh()
    toast.show(message)
  } catch (e) {
    if ((e as { statusCode?: number }).statusCode === 401) {
      await clearSession()
      await navigateTo({ path: '/login', query: { next: `/guides/${slug}` } })
      return
    }
    deleteError.value = apiErrorMessages(e).join(' ')
  }
}

async function archiveGuide() {
  const sure = await ask({
    title: `Archive “${guide.value?.title ?? ''}”?`,
    body: 'The guide leaves search and the overview. Its link still works and shows a note that the guide is archived. You can restore it at any time.',
    confirmLabel: 'Archive guide',
    cancelLabel: 'Keep guide',
  })
  if (sure) await changeStatus('archive', 'Guide archived.')
}

async function deleteGuide() {
  deleteError.value = ''
  const title = guide.value?.title ?? ''
  const sure = await ask({
    title: `Delete “${title}”?`,
    body: 'The guide disappears for all readers. An admin can restore it from the history.',
    confirmLabel: 'Delete guide',
    cancelLabel: 'Keep guide',
    danger: true,
  })
  if (!sure) return
  deleting.value = true
  try {
    await $fetch(`/api/guides/${slug}/`, { method: 'DELETE' })
    clearNuxtData((key) => key.startsWith('guide'))
    toast.show(`The guide “${title}” was deleted.`)
    await navigateTo('/')
  } catch (e) {
    if ((e as { statusCode?: number }).statusCode === 401) {
      await clearSession()
      await navigateTo({ path: '/login', query: { next: `/guides/${slug}` } })
      return
    }
    deleteError.value = apiErrorMessages(e).join(' ')
  } finally {
    deleting.value = false
  }
}

const siteUrl = String(config.public.siteUrl).replace(/\/$/, '')

// Structured data for search engines (schema.org HowTo).
// "<" is escaped so content cannot end the <script> tag.
const jsonLd = JSON.stringify({
  '@context': 'https://schema.org',
  '@type': 'HowTo',
  inLanguage: guide.value.language,
  name: guide.value.title,
  description: guide.value.summary,
  step: guide.value.steps.map((s, i) => ({
    '@type': 'HowToStep',
    position: i + 1,
    name: s.title,
    text: s.body,
  })),
}).replace(/</g, '\\u003c')

useSeoMeta({
  title: guide.value.title,
  description: guide.value.summary || guide.value.title,
  ogTitle: guide.value.title,
  ogDescription: guide.value.summary || guide.value.title,
  ogType: 'article',
})
useHead({
  link: [{ rel: 'canonical', href: `${siteUrl}/guides/${slug}` }],
  script: [{ type: 'application/ld+json', innerHTML: jsonLd }],
})
</script>

<template>
  <div v-if="guide">
    <ReadingBars :title="guide.title" />
    <nav aria-label="Breadcrumbs" class="crumbs">
      <NuxtLink to="/">Home</NuxtLink>
      <template v-if="guide.category">
        › <NuxtLink :to="`/category/${guide.category.slug}`">{{ guide.category.name }}</NuxtLink>
      </template>
    </nav>

    <ResizableColumns class="guide-layout" storage-key="guidebuddy:guide-split" :default-split="68" :min="45" :max="80" label="Resize guide and comments">
      <div class="guide-article">
        <p v-if="guide.status === 'archived'" class="status-note is-archived" role="status">
          <GuideIcon name="document" :size="18" />
          <span><strong>This guide is archived.</strong> It no longer shows in search and the overview.</span>
          <button v-if="canDelete" type="button" class="link-button" @click="changeStatus('restore', 'Guide restored.')">Restore guide</button>
        </p>
        <p v-else-if="note" class="status-note" role="status">
          <GuideIcon name="alert" :size="18" />
          <span><strong>This guide may be out of date.</strong> {{ note }}</span>
          <button v-if="canMark && guide.status === 'outdated'" type="button" class="link-button" @click="changeStatus('mark-current', 'Guide marked as up to date.')">Mark as up to date</button>
        </p>
        <GuideReader :guide="guide" :locked="locked">
          <template #tools>
            <span class="guide-tools">
              <NuxtLink v-if="!locked || isModerator" :to="`/guides/${slug}/edit`">Edit</NuxtLink>
              <button v-if="isModerator" type="button" class="secondary small" @click="toggleLock">
                {{ locked ? 'Unlock' : 'Lock' }}
              </button>
              <NuxtLink :to="`/guides/${slug}/history`">History</NuxtLink>
              <button v-if="canMark && guide.status === 'published'" type="button" class="link-button" @click="changeStatus('mark-outdated', 'Guide marked as outdated.')">
                Mark as outdated
              </button>
              <button v-if="canDelete && guide.status !== 'archived'" type="button" class="link-button" @click="archiveGuide">Archive</button>
              <button v-if="canDelete" type="button" class="link-button danger" :disabled="deleting" @click="deleteGuide">
                {{ deleting ? 'Deleting …' : 'Delete' }}
              </button>
            </span>
          </template>
        </GuideReader>
        <p v-if="deleteError" class="error-box" role="alert">{{ deleteError }}</p>
        <p v-if="locked" class="hint-box">This guide is locked and cannot be edited at the moment.</p>

        <p class="muted">
          License: <a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="license noopener">CC BY-SA 4.0</a>.
          The authors are listed in the <NuxtLink :to="`/guides/${slug}/history`">history</NuxtLink>.
        </p>

        <details v-if="loggedIn && user" class="report-box">
          <summary>Report this guide</summary>
          <div v-if="reportMessage" class="ok-box" role="status">{{ reportMessage }}</div>
          <form v-else class="stack narrow" @submit.prevent="sendReport">
            <div v-if="reportErrors.length" class="error-box" role="alert">
              <ul><li v-for="m in reportErrors" :key="m">{{ m }}</li></ul>
            </div>
            <div>
              <label for="reason">Reason</label>
              <select id="reason" v-model="reportReason">
                <option v-for="r in GUIDE_REPORT_REASONS" :key="r.value" :value="r.value">{{ r.label }}</option>
              </select>
            </div>
            <div>
              <label for="rcomment">Remark (optional)</label>
              <textarea id="rcomment" v-model="reportComment" rows="3" maxlength="1000" />
            </div>
            <p><button type="submit" class="button">Send report</button></p>
          </form>
        </details>
        <p v-else class="muted"><NuxtLink :to="{ path: '/login', query: { next: `/guides/${slug}` } }">Sign in</NuxtLink> to report this guide.</p>

        <section v-if="related?.length" class="related" aria-labelledby="related-title">
          <h2 id="related-title">Related guides</h2>
          <ul class="guide-cards">
            <GuideCard v-for="item in related" :key="item.slug" :guide="item" />
          </ul>
        </section>
      </div>

      <template #end>
      <GuideComments :slug="slug" :guide="guide" />
      </template>
    </ResizableColumns>
  </div>
</template>
