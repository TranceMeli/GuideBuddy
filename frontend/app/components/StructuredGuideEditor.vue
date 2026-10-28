<script setup lang="ts">
import type { Category, Difficulty, Guide } from '~/types/guide'

/**
 * Editor of a guide built from elements: a head that looks like the guide (big title, the
 * key facts as chips, optional fields folded away), the builder with its tools below, and a
 * live preview that uses the real reading templates (docs/guide-types.md).
 */
const props = defineProps<{ guide?: Guide; categories: Category[] }>()

const base = useApiBase()
const route = useRoute()
const { clearSession, user } = useAuth()

const form = reactive({
  title: props.guide?.title ?? '',
  subtitle: props.guide?.subtitle ?? '',
  summary: props.guide?.summary ?? '',
  language: props.guide?.language ?? 'en',
  cover: props.guide?.cover_image ?? null,
  categoryId: (props.guide?.category?.id ?? null) as number | null,
  difficulty: (props.guide?.difficulty ?? '') as Difficulty | '',
  // v-model on a number input yields a number, or '' when empty
  duration: (props.guide?.duration_minutes ?? '') as number | '',
  changeComment: '',
})
// The elements of the guide. Keys start at k1 on server and client alike (see resetLocalKeys).
resetLocalKeys()
const elements = ref(draftFromGuide(props.guide))
// Optional fields folded away under "More details"; the toggle shows how many are filled
const moreOpen = ref(false)
const moreFilled = computed(() => [form.summary.trim(), form.cover].filter(Boolean).length)
const checks = computed(() => publishChecks(form, elements.value))
// Set on the first publish attempt, so missing required chips are marked from then on
const tried = ref(false)

// Asks before leaving with unsaved changes
const { dirty, markSaved } = useUnsavedChanges(() => [form, elements.value])

const errors = ref<string[]>([])
const saving = ref(false)
const errorBox = ref<HTMLElement | null>(null)

// Live preview: rebuilt on every change; Markdown is rendered by the server (sanitized)
const { md, failed: previewFailed } = useMarkdownPreview()
const livePreview = computed(() =>
  buildPreviewGuide(form, elements.value, props.categories, md, props.guide),
)

async function showErrors(messages: string[]) {
  errors.value = messages
  await nextTick()
  errorBox.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  errorBox.value?.focus()
}

async function handleError(e: unknown) {
  if ((e as { statusCode?: number }).statusCode === 401) {
    await clearSession()
    await navigateTo({ path: '/login', query: { next: route.fullPath } })
    return
  }
  await showErrors(apiErrorMessages(e))
}

/** Checks the form and builds the API payload. null = invalid (messages are shown). */
async function buildPayload() {
  tried.value = true
  const problems: string[] = []
  if (!form.title.trim()) problems.push('Please enter a title.')
  if (props.categories.length && form.categoryId === null) problems.push('Please choose a category.')
  const duration = form.duration === '' ? null : Number(form.duration)
  if (duration !== null && (!Number.isInteger(duration) || duration < 1 || duration > 1440)) {
    problems.push('The duration must be between 1 and 1440 minutes.')
  }
  const content = payloadFromDraft(elements.value)
  problems.push(...content.problems)
  if (problems.length) {
    await showErrors(problems)
    return null
  }
  errors.value = []
  return {
    ...(props.guide ? {} : { guide_type: 'page' }),
    title: form.title.trim(),
    subtitle: form.subtitle.trim(),
    summary: form.summary.trim(),
    language: form.language,
    cover_image_id: form.cover?.id ?? null,
    category_id: form.categoryId,
    difficulty: form.difficulty,
    duration_minutes: duration,
    change_comment: form.changeComment,
    ...content.payload,
  }
}

async function save() {
  const payload = await buildPayload()
  if (!payload) return
  saving.value = true
  try {
    const saved = await $fetch<Guide>(props.guide ? `${base}/guides/${props.guide.slug}/` : `${base}/guides/`, {
      method: props.guide ? 'PUT' : 'POST',
      body: payload,
    })
    clearNuxtData((key) => key.startsWith('guide'))
    markSaved()
    await navigateTo(`/guides/${saved.slug}`)
  } catch (e) {
    await handleError(e)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <LivePreviewLayout :status="previewFailed ? 'formatting currently unavailable' : ''">
  <form class="stack editor" novalidate @submit.prevent="save">
    <div v-if="user && !user.can_write" class="hint-box" role="status">{{ user.write_hint }}</div>
    <div v-if="errors.length" ref="errorBox" class="error-box" role="alert" tabindex="-1">
      <ul><li v-for="message in errors" :key="message">{{ message }}</li></ul>
    </div>

    <!-- Head: the title as it will be read, the key facts as chips, the rest folded away -->
    <header class="ed-head">
      <label for="title" class="visually-hidden">Title</label>
      <input id="title" v-model="form.title" class="ed-title" type="text" maxlength="160" placeholder="Name the result, e.g. Change a bike inner tube" required>
      <label for="subtitle" class="visually-hidden">Subtitle (optional)</label>
      <input id="subtitle" v-model="form.subtitle" class="ed-subtitle" type="text" maxlength="200" placeholder="Subtitle (optional): one line below the title">

      <div class="ed-chips" role="group" aria-label="Guide details">
        <label v-if="categories.length" class="ed-chip" :class="{ 'is-empty': form.categoryId === null, 'is-missing': tried && form.categoryId === null }">
          <GuideIcon name="file" :size="16" />
          <span class="visually-hidden">Category</span>
          <select v-model="form.categoryId">
            <option :value="null" disabled>Category</option>
            <option v-for="c in categories" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
        </label>
        <label class="ed-chip" :class="{ 'is-empty': !form.difficulty }">
          <GuideIcon name="level" :size="16" />
          <span class="visually-hidden">Level</span>
          <select v-model="form.difficulty">
            <option value="">Level</option>
            <option v-for="d in DIFFICULTIES" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </label>
        <label class="ed-chip" :class="{ 'is-empty': form.duration === '' }">
          <GuideIcon name="clock" :size="16" />
          <span class="visually-hidden">Duration in minutes</span>
          <input v-model="form.duration" type="number" min="1" max="1440" inputmode="numeric" placeholder="Duration">
          <span aria-hidden="true">min</span>
        </label>
        <button type="button" class="ed-chip ed-more-toggle" :aria-expanded="moreOpen" aria-controls="ed-more" @click="moreOpen = !moreOpen">
          <GuideIcon :name="moreOpen ? 'close' : 'menu'" :size="16" />
          {{ moreOpen ? 'Hide details' : 'More details' }}
          <span v-if="!moreOpen && moreFilled" class="ed-count">{{ moreFilled }}</span>
        </button>
      </div>

      <div v-show="moreOpen" id="ed-more" class="ed-more">
        <div>
          <label for="summary">Summary <span class="muted">(optional, for the overview)</span></label>
          <textarea id="summary" v-model="form.summary" rows="2" maxlength="300" placeholder="What is it about? One or two sentences." />
        </div>
        <div>
          <span class="field-label">Preview image <span class="muted">(optional, shown on the overview cards)</span></span>
          <ImagePicker id="cover-image" v-model="form.cover" />
        </div>
      </div>
    </header>

    <ElementsEditor v-model="elements" />

    <div v-if="guide">
      <label for="comment">What did you change? <span class="muted">(optional)</span></label>
      <input id="comment" v-model="form.changeComment" type="text" maxlength="200" placeholder="e.g. Added step 3">
    </div>

    <PublishChecklist :checks="checks" />

    <p class="muted small">
      By publishing, you license your contribution under
      <NuxtLink to="/license">CC BY-SA 4.0</NuxtLink> and confirm that you wrote it yourself
      or hold the rights to it.
    </p>

    <p class="actions editor-actions">
      <button type="submit" class="button" :disabled="saving">
        {{ saving ? 'Publishing …' : 'Publish' }}
      </button>
      <NuxtLink :to="guide ? `/guides/${guide.slug}` : '/'">Cancel</NuxtLink>
      <span v-if="dirty" class="unsaved-hint muted small" role="status">Unsaved changes</span>
    </p>
  </form>

    <template #preview>
      <GuideReader :guide="livePreview" preview />
    </template>
  </LivePreviewLayout>
</template>
