<script setup lang="ts">
import type { Guide, GuideComment } from '~/types/guide'

/**
 * Comments of a guide: on the whole guide or on one of its elements, as comment or question,
 * with replies (one level), "Helpful", an answer marked on a question, and a report button per
 * comment. The counts per element go to useState('gb-comment-counts'), where the reading view
 * picks them up for its comment buttons; a click on such a button arrives as
 * useState('gb-comment-target') and filters the list to that element.
 */
const props = defineProps<{ slug: string; guide: Guide }>()
const base = useApiBase()
const { loggedIn, isModerator, user, clearSession } = useAuth()

const { data: comments, error: loadError, refresh } = await useFetch<GuideComment[]>(`${base}/guides/${props.slug}/comments/`, {
  key: `guide-comments-${props.slug}`,
  default: () => [],
})

const target = useState<{ element: number; n: number } | null>('gb-comment-target', () => null)
const counts = useState<Record<number, number>>('gb-comment-counts', () => ({}))
watch(comments, (list) => {
  const next: Record<number, number> = {}
  for (const c of list ?? []) if (c.element) next[c.element] = (next[c.element] ?? 0) + 1
  counts.value = next
}, { immediate: true })
onBeforeUnmount(() => { counts.value = {}; target.value = null })

// --- Filters and order -----------------------------------------------------------------
type Filter = 'all' | 'questions' | 'unanswered' | 'steps'
const filter = ref<Filter>('all')
const sort = ref<'newest' | 'oldest' | 'helpful'>('newest')
const onElement = ref<number | null>(null) // set by a click on a comment button in the guide

const repliesOf = computed(() => {
  const map = new Map<number, GuideComment[]>()
  for (const c of comments.value ?? []) {
    if (c.parent) map.set(c.parent, [...(map.get(c.parent) ?? []), c])
  }
  for (const list of map.values()) list.sort((a, b) => Number(b.is_answer) - Number(a.is_answer) || a.created_at.localeCompare(b.created_at))
  return map
})
const topLevel = computed(() => (comments.value ?? []).filter((c) => !c.parent))
const answered = (c: GuideComment) => (repliesOf.value.get(c.id) ?? []).some((r) => r.is_answer)
const visible = computed(() => {
  let list = topLevel.value
  if (onElement.value) list = list.filter((c) => c.element === onElement.value)
  if (filter.value === 'questions') list = list.filter((c) => c.kind === 'question')
  if (filter.value === 'unanswered') list = list.filter((c) => c.kind === 'question' && !answered(c))
  if (filter.value === 'steps') list = list.filter((c) => c.anchor)
  return [...list].sort((a, b) =>
    sort.value === 'oldest' ? a.created_at.localeCompare(b.created_at)
      : sort.value === 'helpful' ? b.helpful_count - a.helpful_count || b.created_at.localeCompare(a.created_at)
        : b.created_at.localeCompare(a.created_at))
})
const counted = computed(() => ({
  all: topLevel.value.length,
  questions: topLevel.value.filter((c) => c.kind === 'question').length,
  unanswered: topLevel.value.filter((c) => c.kind === 'question' && !answered(c)).length,
  steps: topLevel.value.filter((c) => c.anchor).length,
}))
const total = computed(() => (comments.value ?? []).length)

// --- The places a comment can be about ---------------------------------------------------
const places = computed(() => {
  let section = 0
  let step = 0
  return props.guide.elements
    .filter((el) => el.id)
    .map((el) => {
      const number = el.kind === 'section' ? ++section : el.kind === 'step' ? ++step : 0
      const name = TOOL[el.kind].label + (number ? ` ${number}` : '')
      const first = (el.text || '').trim().split('\n')[0] ?? ''
      return { id: el.id!, label: first ? `${name}: ${first.slice(0, 50)}` : name }
    })
})

// A click on a comment button of the guide: show that element's comments and write about it
watch(target, (value) => {
  if (!value) return
  onElement.value = value.element
  filter.value = 'all'
  form.element = value.element
  nextTick(() => document.getElementById('comments-title')?.scrollIntoView({ behavior: 'smooth', block: 'start' }))
})
const onElementLabel = computed(() => places.value.find((p) => p.id === onElement.value)?.label ?? '')

// --- Writing -------------------------------------------------------------------------------
const form = reactive({ body: '', kind: 'comment' as 'comment' | 'question', element: null as number | null })
const errors = ref<string[]>([])
const saving = ref(false)
const preview = ref<string | null>(null)
watch(() => form.body, () => { preview.value = null })

async function guard(fn: () => Promise<unknown>) {
  errors.value = []
  try {
    await fn()
  } catch (e) {
    if ((e as { statusCode?: number }).statusCode === 401) {
      await clearSession()
      await navigateTo({ path: '/login', query: { next: `/guides/${props.slug}` } })
      return false
    }
    errors.value = apiErrorMessages(e)
    return false
  }
  return true
}

async function send() {
  saving.value = true
  const ok = await guard(() => $fetch<unknown>(`/api/guides/${props.slug}/comments/`, {
    method: 'POST',
    body: { body: form.body, kind: form.kind, element_id: form.element },
  }))
  saving.value = false
  if (ok) {
    form.body = ''
    await refresh()
  }
}

async function showPreview(body: string, set: (html: string | null) => void, current: string | null) {
  if (current) return set(null)
  await guard(async () => {
    const result = await $fetch<{ body_html: string }>(`/api/guides/${props.slug}/comments/preview/`, { method: 'POST', body: { body } })
    set(result.body_html)
  })
}

// Reply
const replyTo = ref<number | null>(null)
const replyBody = ref('')
function startReply(c: GuideComment) {
  replyTo.value = c.id
  replyBody.value = ''
  editing.value = null
}
async function sendReply(c: GuideComment) {
  saving.value = true
  const ok = await guard(() => $fetch<unknown>(`/api/guides/${props.slug}/comments/`, { method: 'POST', body: { body: replyBody.value, parent_id: c.id } }))
  saving.value = false
  if (ok) {
    replyTo.value = null
    await refresh()
  }
}

// Edit
const editing = ref<number | null>(null)
const editBody = ref('')
const editPreview = ref<string | null>(null)
function startEdit(c: GuideComment) {
  editing.value = c.id
  editBody.value = c.body
  editPreview.value = null
  replyTo.value = null
}
async function saveEdit(c: GuideComment) {
  saving.value = true
  const ok = await guard(() => $fetch<unknown>(`/api/guides/${props.slug}/comments/${c.id}/`, { method: 'PUT', body: { body: editBody.value } }))
  saving.value = false
  if (ok) {
    editing.value = null
    await refresh()
  }
}

// Helpful, answer, report
async function toggleHelpful(c: GuideComment) {
  if (!loggedIn.value) return navigateTo({ path: '/login', query: { next: `/guides/${props.slug}` } })
  if (await guard(() => $fetch<unknown>(`/api/guides/${props.slug}/comments/${c.id}/helpful/`, { method: c.helpful ? 'DELETE' : 'POST' }))) await refresh()
}
async function toggleAnswer(c: GuideComment) {
  if (await guard(() => $fetch<unknown>(`/api/guides/${props.slug}/comments/${c.id}/answer/`, { method: c.is_answer ? 'DELETE' : 'POST' }))) await refresh()
}
const reporting = ref<number | null>(null)
const reportReason = ref('spam')
const reportRemark = ref('')
const reported = ref('')
async function sendReport(c: GuideComment) {
  const ok = await guard(async () => {
    const result = await $fetch<{ detail: string }>(`/api/guides/${props.slug}/comments/${c.id}/report/`, { method: 'POST', body: { reason: reportReason.value, comment: reportRemark.value } })
    reported.value = result.detail
  })
  if (ok) {
    reporting.value = null
    reportRemark.value = ''
  }
}

const dateOf = (iso: string) => new Date(iso).toLocaleDateString('en-GB')
const mine = (c: GuideComment) => loggedIn.value && c.author === user.value?.username
function jumpTo(c: GuideComment) {
  if (c.element) document.getElementById(`el-${c.element}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}
</script>

<template>
  <aside class="guide-comments gc" aria-labelledby="comments-title">
    <h2 id="comments-title">Comments <span class="gc-count">{{ total }}</span></h2>

    <div v-if="loadError" class="error-box" role="alert">The comments could not be loaded. Please try again later.</div>

    <template v-else>
      <div v-if="total" class="gc-filters" role="group" aria-label="Show">
        <button v-for="f in ([['all', 'All'], ['questions', 'Questions'], ['unanswered', 'Unanswered'], ['steps', 'On the guide']] as const)" :key="f[0]" type="button" class="gc-pill" :aria-pressed="filter === f[0]" @click="filter = f[0]; onElement = null">
          {{ f[1] }} {{ counted[f[0]] }}
        </button>
        <label class="gc-sort"><span class="visually-hidden">Sort by</span>
          <select v-model="sort"><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="helpful">Most helpful</option></select>
        </label>
      </div>
      <p v-if="onElement" class="gc-on">
        <GuideIcon name="eye" :size="14" /> Showing comments on <strong>{{ onElementLabel || 'this element' }}</strong>
        <button type="button" class="link" @click="onElement = null; target = null">Show all</button>
      </p>

      <p v-if="!total" class="muted">No comments yet. Ask a question or share what worked.</p>
      <p v-else-if="!visible.length" class="muted">Nothing matches this filter.</p>

      <ol class="gc-list">
        <li v-for="c in visible" :id="`comment-${c.id}`" :key="c.id" class="gc-item">
          <!-- one comment (top level) -->
          <div class="gc-head">
            <strong>{{ c.author ?? 'Deleted account' }}</strong>
            <span v-if="c.by_guide_author" class="gc-tag gc-tag--author">Author</span>
            <span v-if="c.kind === 'question'" class="gc-tag gc-tag--question">Question</span>
            <time :datetime="c.created_at">{{ dateOf(c.created_at) }}</time>
            <span v-if="c.edited_at" class="muted">(edited)</span>
          </div>
          <button v-if="c.anchor" type="button" class="gc-anchor" :disabled="!c.element" :title="c.element ? 'Show in the guide' : 'This element was removed'" @click="jumpTo(c)">
            <GuideIcon name="link" :size="13" /> {{ c.anchor }}
          </button>

          <form v-if="editing === c.id" class="stack comment-form" @submit.prevent="saveEdit(c)">
            <label :for="`edit-${c.id}`" class="visually-hidden">Edit comment</label>
            <textarea :id="`edit-${c.id}`" v-model="editBody" rows="4" maxlength="5000" required />
            <div v-if="editPreview" class="comment-preview"><div class="prose" v-html="editPreview" /></div>
            <div class="actions">
              <button type="button" class="secondary" @click="showPreview(editBody, (h) => (editPreview = h), editPreview)">{{ editPreview ? 'Hide preview' : 'Preview' }}</button>
              <button type="submit" class="button" :disabled="saving">Save changes</button>
              <button type="button" class="secondary" @click="editing = null">Cancel</button>
            </div>
          </form>
          <!-- body_html is sanitized by the backend. -->
          <!-- eslint-disable-next-line vue/no-v-html -->
          <div v-else class="gc-body prose" v-html="c.body_html" />

          <div class="gc-actions">
            <button type="button" :aria-pressed="c.helpful" :disabled="mine(c)" :title="mine(c) ? 'You cannot rate your own comment' : undefined" @click="toggleHelpful(c)">
              <GuideIcon name="star" :size="14" /> Helpful<span v-if="c.helpful_count" class="gc-n">{{ c.helpful_count }}</span>
            </button>
            <button v-if="loggedIn" type="button" @click="startReply(c)">Reply</button>
            <button v-if="c.can_edit && editing !== c.id" type="button" @click="startEdit(c)">Edit</button>
            <button v-if="loggedIn && !mine(c)" type="button" @click="reporting = reporting === c.id ? null : c.id">Report</button>
            <span v-if="c.kind === 'question' && !answered(c)" class="gc-open">No answer yet</span>
          </div>

          <form v-if="reporting === c.id" class="gc-report stack" @submit.prevent="sendReport(c)">
            <label :for="`reason-${c.id}`">Reason</label>
            <select :id="`reason-${c.id}`" v-model="reportReason">
              <option value="spam">Spam or advertising</option><option value="vandalism">Vandalism</option><option value="illegal">Illegal content</option><option value="other">Other</option>
            </select>
            <label :for="`remark-${c.id}`">Remark <span class="muted">(optional)</span></label>
            <textarea :id="`remark-${c.id}`" v-model="reportRemark" rows="2" maxlength="1000" />
            <div class="actions"><button type="submit" class="button">Send report</button><button type="button" class="secondary" @click="reporting = null">Cancel</button></div>
          </form>

          <!-- replies -->
          <ol v-if="repliesOf.get(c.id)?.length" class="gc-replies">
            <li v-for="r in repliesOf.get(c.id)" :id="`comment-${r.id}`" :key="r.id" class="gc-reply" :class="{ 'is-answer': r.is_answer }">
              <div class="gc-head">
                <strong>{{ r.author ?? 'Deleted account' }}</strong>
                <span v-if="r.by_guide_author" class="gc-tag gc-tag--author">Author</span>
                <span v-if="r.is_answer" class="gc-tag gc-tag--answer"><GuideIcon name="check" :size="12" /> Answer</span>
                <time :datetime="r.created_at">{{ dateOf(r.created_at) }}</time>
                <span v-if="r.edited_at" class="muted">(edited)</span>
              </div>
              <form v-if="editing === r.id" class="stack comment-form" @submit.prevent="saveEdit(r)">
                <label :for="`edit-${r.id}`" class="visually-hidden">Edit reply</label>
                <textarea :id="`edit-${r.id}`" v-model="editBody" rows="3" maxlength="5000" required />
                <div class="actions">
                  <button type="submit" class="button" :disabled="saving">Save changes</button>
                  <button type="button" class="secondary" @click="editing = null">Cancel</button>
                </div>
              </form>
              <!-- eslint-disable-next-line vue/no-v-html -->
              <div v-else class="gc-body prose" v-html="r.body_html" />
              <div class="gc-actions">
                <button type="button" :aria-pressed="r.helpful" :disabled="mine(r)" @click="toggleHelpful(r)">
                  <GuideIcon name="star" :size="14" /> Helpful<span v-if="r.helpful_count" class="gc-n">{{ r.helpful_count }}</span>
                </button>
                <button v-if="r.can_mark_answer" type="button" @click="toggleAnswer(r)">{{ r.is_answer ? 'Unmark answer' : 'Mark as answer' }}</button>
                <button v-if="r.can_edit && editing !== r.id" type="button" @click="startEdit(r)">Edit</button>
                <button v-if="loggedIn && !mine(r)" type="button" @click="reporting = reporting === r.id ? null : r.id">Report</button>
              </div>
              <form v-if="reporting === r.id" class="gc-report stack" @submit.prevent="sendReport(r)">
                <label :for="`reason-${r.id}`">Reason</label>
                <select :id="`reason-${r.id}`" v-model="reportReason">
                  <option value="spam">Spam or advertising</option><option value="vandalism">Vandalism</option><option value="illegal">Illegal content</option><option value="other">Other</option>
                </select>
                <div class="actions"><button type="submit" class="button">Send report</button><button type="button" class="secondary" @click="reporting = null">Cancel</button></div>
              </form>
            </li>
          </ol>

          <form v-if="replyTo === c.id" class="gc-reply-form stack comment-form" @submit.prevent="sendReply(c)">
            <label :for="`reply-${c.id}`" class="visually-hidden">Your reply</label>
            <textarea :id="`reply-${c.id}`" v-model="replyBody" rows="3" maxlength="5000" required placeholder="Write a reply" />
            <div class="actions">
              <button type="submit" class="button" :disabled="saving">Send reply</button>
              <button type="button" class="secondary" @click="replyTo = null">Cancel</button>
            </div>
          </form>
        </li>
      </ol>

      <p v-if="reported" class="ok-box" role="status">{{ reported }}</p>
    </template>

    <!-- write -->
    <form v-if="loggedIn" class="gc-compose stack comment-form" @submit.prevent="send">
      <div v-if="errors.length" class="error-box" role="alert"><ul><li v-for="m in errors" :key="m">{{ m }}</li></ul></div>
      <div>
        <label for="comment-body">Write a comment <span class="muted">(Markdown allowed)</span></label>
        <textarea id="comment-body" v-model="form.body" rows="4" maxlength="5000" required />
      </div>
      <div v-if="preview" class="comment-preview"><strong>Preview</strong><div class="prose" v-html="preview" /></div>
      <div class="gc-row">
        <span class="gc-kind" role="group" aria-label="Kind">
          <button type="button" class="gc-pill" :aria-pressed="form.kind === 'comment'" @click="form.kind = 'comment'">Comment</button>
          <button type="button" class="gc-pill" :aria-pressed="form.kind === 'question'" @click="form.kind = 'question'">Question</button>
        </span>
        <label class="gc-about"><span class="visually-hidden">About</span>
          <select v-model="form.element">
            <option :value="null">About the whole guide</option>
            <option v-for="p in places" :key="p.id" :value="p.id">{{ p.label }}</option>
          </select>
        </label>
        <span class="gc-limit muted">{{ form.body.length }} of 5,000</span>
      </div>
      <div class="actions">
        <button type="submit" class="button" :disabled="saving">{{ saving ? 'Sending …' : 'Send comment' }}</button>
        <button type="button" class="secondary" @click="showPreview(form.body, (h) => (preview = h), preview)">{{ preview ? 'Hide preview' : 'Preview' }}</button>
      </div>
      <p class="muted small">Be kind. Comments can be reported.</p>
    </form>
    <p v-else class="muted">
      <NuxtLink :to="{ path: '/login', query: { next: `/guides/${slug}` } }">Sign in</NuxtLink> to write a comment.
    </p>
  </aside>
</template>
