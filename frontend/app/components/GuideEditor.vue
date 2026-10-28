<script setup lang="ts">
import type { AttachmentKind, Category, Guide } from '~/types/guide'

const props = defineProps<{ guide?: Guide; categories: Category[] }>()

const base = useApiBase()
const route = useRoute()
const { clearSession, user } = useAuth()

type Mode = 'write' | 'upload'

const existingSteps = props.guide?.steps ?? []
const form = reactive({
  title: props.guide?.title ?? '',
  summary: props.guide?.summary ?? '',
  language: props.guide?.language ?? 'en',
  cover: props.guide?.cover_image ?? null,
  categoryId: (props.guide?.category?.id ?? null) as number | null,
  changeComment: '',
  // Guides that consist of a file only open in upload mode
  mode: (props.guide && !existingSteps.length && props.guide.attachment_info ? 'upload' : 'write') as Mode,
  content: props.guide ? stepsToHtml(existingSteps, props.guide.title) : '',
})

const errors = ref<string[]>([])
const saving = ref(false)
const createdGuide = ref<Guide | null>(null)

// Live preview of the written text (the rich text is split into steps in the browser,
// Markdown is rendered by the server). Upload mode shows the chosen file instead.
const { md, failed: previewFailed } = useMarkdownPreview()
const livePreview = computed(() => {
  const steps = form.mode === 'write' && import.meta.client ? htmlToSteps(form.content, form.title, form.language).steps : []
  return buildFreePreviewGuide(form, steps, props.categories, md, props.guide)
})

// --- File -------------------------------------------------------------------

const ALLOWED = /\.(pdf|docx|xlsx|pptx|png|jpe?g|gif|webp|md|txt|csv)$/i
const MAX_BYTES = 10 * 1024 * 1024
const fileInput = ref<HTMLInputElement | null>(null)
const selectedFile = ref<File | null>(null)
// Asks before leaving with unsaved changes (a chosen file that is not uploaded yet counts)
const { dirty, markSaved } = useUnsavedChanges(() => [form, selectedFile.value])
const attachmentInfo = ref(props.guide?.attachment_info ?? null)
const fileError = ref('')
const dragging = ref(false)

const formatSize = (bytes: number) =>
  bytes < 1024 * 1024 ? `${Math.max(1, Math.round(bytes / 1024))} KB` : `${(bytes / 1024 / 1024).toFixed(1)} MB`

// Preview of the chosen (not yet uploaded) file
const filePreview = reactive({ kind: 'none' as AttachmentKind, src: '', html: '', loading: false })
let previewRequest = 0

function kindOf(name: string): AttachmentKind {
  if (/.pdf$/i.test(name)) return 'pdf'
  if (/.(png|jpe?g|gif|webp)$/i.test(name)) return 'image'
  if (/.(docx|md|txt|csv)$/i.test(name)) return 'html'
  return 'none'
}

function resetPreview() {
  if (filePreview.src) URL.revokeObjectURL(filePreview.src)
  Object.assign(filePreview, { kind: 'none', src: '', html: '', loading: false })
  previewRequest++
}
onBeforeUnmount(resetPreview)

async function loadPreview(file: File) {
  resetPreview()
  filePreview.kind = kindOf(file.name)
  if (filePreview.kind === 'pdf' || filePreview.kind === 'image') {
    filePreview.src = URL.createObjectURL(file) // shown by the browser directly, without uploading
  } else if (filePreview.kind === 'html') {
    // Word, Markdown, text and CSV are converted by the server (nothing is stored)
    const request = ++previewRequest
    filePreview.loading = true
    const body = new FormData()
    body.append('file', file)
    try {
      const result = await $fetch<{ preview_html: string }>(`${base}/guides/attachment-preview/`, {
        method: 'POST',
        body,
      })
      if (request === previewRequest) filePreview.html = result.preview_html
    } catch (e) {
      if (request === previewRequest) fileError.value = apiErrorMessages(e).join(' ')
    } finally {
      if (request === previewRequest) filePreview.loading = false
    }
  }
}

function selectFile(file?: File | null) {
  fileError.value = ''
  selectedFile.value = null
  resetPreview()
  if (fileInput.value) fileInput.value.value = ''
  if (!file) return
  if (!ALLOWED.test(file.name)) {
    fileError.value = 'This format is not supported. Allowed: PDF, Word, Excel, PowerPoint, images, text.'
    return
  }
  if (file.size > MAX_BYTES) {
    fileError.value = 'The file must be 10 MB or smaller.'
    return
  }
  selectedFile.value = file
  void loadPreview(file)
}

function onDrop(event: DragEvent) {
  dragging.value = false
  const files = event.dataTransfer?.files
  if (!files || files.length !== 1) {
    fileError.value = 'Please drop exactly one file here.'
    return
  }
  selectFile(files[0])
}

async function removeAttachment() {
  if (!props.guide || !confirm('Really remove the attached file?')) return
  try {
    await $fetch<unknown>(`${base}/guides/${props.guide.slug}/attachment/`, { method: 'DELETE' })
    attachmentInfo.value = null
    clearNuxtData((key) => key.startsWith('guide'))
  } catch (e) {
    await handleError(e)
  }
}

// --- Saving -----------------------------------------------------------------

async function handleError(e: unknown) {
  if ((e as { statusCode?: number }).statusCode === 401) {
    await clearSession()
    await navigateTo({ path: '/login', query: { next: route.fullPath } })
    return
  }
  errors.value = apiErrorMessages(e)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** Checks the form and builds the API payload. null = invalid (messages are in errors). */
function buildPayload() {
  const problems: string[] = []
  if (!form.title.trim()) problems.push('Please enter a title.')
  if (props.categories.length && form.categoryId === null) problems.push('Please choose a category.')

  let steps: { id?: number; order: number; title: string; body: string }[] = []
  if (form.mode === 'write') {
    const result = htmlToSteps(form.content, form.title, form.language)
    problems.push(...result.errors)
    // Reuse existing steps in order, so the history stays readable
    steps = result.steps.map((step, i) => ({
      ...(existingSteps[i] ? { id: existingSteps[i]!.id } : {}),
      order: i + 1,
      ...step,
    }))
  } else if (!selectedFile.value && !attachmentInfo.value) {
    problems.push('Please choose a file to upload.')
  }

  errors.value = problems
  if (problems.length) {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    return null
  }
  return {
    title: form.title.trim(),
    summary: form.summary.trim(),
    language: form.language,
    cover_image_id: form.cover?.id ?? null,
    category_id: form.categoryId,
    change_comment: form.changeComment,
    steps,
  }
}

async function save() {
  const payload = buildPayload()
  if (!payload) return
  if (
    form.mode === 'upload' && existingSteps.length &&
    !confirm('The current text of this guide will be replaced by the file. Continue?')
  ) return

  saving.value = true
  try {
    const existing = props.guide ?? createdGuide.value
    const saved = await $fetch<Guide>(existing ? `${base}/guides/${existing.slug}/` : `${base}/guides/`, {
      method: existing ? 'PUT' : 'POST',
      body: payload,
    })
    if (!props.guide) createdGuide.value = saved

    if (form.mode === 'upload' && selectedFile.value) {
      const upload = new FormData()
      upload.append('file', selectedFile.value)
      const withFile = await $fetch<Guide>(`${base}/guides/${saved.slug}/attachment/`, {
        method: 'POST',
        body: upload,
      })
      attachmentInfo.value = withFile.attachment_info
      selectFile(null)
    }

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
    <div v-if="errors.length" class="error-box" role="alert">
      <ul><li v-for="message in errors" :key="message">{{ message }}</li></ul>
    </div>

    <div>
      <label for="title">Title</label>
      <input id="title" v-model="form.title" type="text" maxlength="160" placeholder="e.g. Change a bike inner tube" required>
    </div>

    <div v-if="categories.length" role="radiogroup" aria-labelledby="category-label">
      <span id="category-label" class="field-label">Category</span>
      <div class="chips">
        <label v-for="c in categories" :key="c.id" class="chip" :class="{ 'is-selected': form.categoryId === c.id }">
          <input v-model="form.categoryId" type="radio" name="category" :value="c.id">
          {{ c.name }}
        </label>
      </div>
    </div>

    <div>
      <label for="summary">Summary</label>
      <textarea
        id="summary"
        v-model="form.summary"
        rows="2"
        maxlength="300"
        placeholder="What is it about? One or two sentences."
      />
    </div>

    <div>
      <span class="field-label">Preview image <span class="muted">(optional, shown on the overview cards)</span></span>
      <ImagePicker id="cover-image" v-model="form.cover" />
    </div>

    <div>
      <span id="content-label" class="field-label">Content</span>
      <div class="mode-switch" role="tablist" aria-labelledby="content-label">
        <button
          type="button"
          role="tab"
          :aria-selected="form.mode === 'write'"
          :class="{ 'is-active': form.mode === 'write' }"
          @click="form.mode = 'write'"
        >
          <GuideIcon name="pen" :size="16" /> Write it
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="form.mode === 'upload'"
          :class="{ 'is-active': form.mode === 'upload' }"
          @click="form.mode = 'upload'"
        >
          <GuideIcon name="file" :size="16" /> Upload a file
        </button>
      </div>

      <div v-if="form.mode === 'write'" role="tabpanel">
        <ClientOnly>
          <RichTextEditor v-model="form.content" labelledby="content-label" />
          <template #fallback><div class="rte rte-loading">Loading the editor …</div></template>
        </ClientOnly>
        <p class="muted small">
          Tip: <strong>“Step”</strong> in the toolbar starts a new step of the guide.
        </p>
        <p v-if="attachmentInfo" class="hint-box small">
          Attached file: <a :href="attachmentInfo.download_url">{{ attachmentInfo.name }}</a>
          <button type="button" class="link-button danger" @click="removeAttachment">remove</button>
        </p>
      </div>

      <div v-else role="tabpanel">
        <label
          class="dropzone"
          :class="{ 'is-dragging': dragging, 'has-file': selectedFile || attachmentInfo }"
          @dragenter.prevent="dragging = true"
          @dragover.prevent
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <input
            ref="fileInput"
            type="file"
            class="visually-hidden"
            accept=".pdf,.docx,.xlsx,.pptx,.png,.jpg,.jpeg,.gif,.webp,.md,.txt,.csv"
            @change="selectFile(($event.target as HTMLInputElement).files?.[0])"
          >
          <template v-if="selectedFile">
            <strong>{{ selectedFile.name }}</strong>
            <span class="muted">{{ formatSize(selectedFile.size) }} · Click to choose another file</span>
          </template>
          <template v-else-if="attachmentInfo">
            <strong>{{ attachmentInfo.name }}</strong>
            <span class="muted">{{ formatSize(attachmentInfo.size) }} · Click to replace the file</span>
          </template>
          <template v-else>
            <strong>{{ dragging ? 'Drop to upload' : 'Drag a file here or click' }}</strong>
            <span class="muted">PDF, Word, Excel, PowerPoint, image or text · max. 10 MB</span>
          </template>
        </label>
        <p v-if="selectedFile || attachmentInfo" class="small">
          <button v-if="selectedFile" type="button" class="link-button danger" @click="selectFile(null)">Remove the chosen file</button>
          <button v-else type="button" class="link-button danger" @click="removeAttachment">Delete the uploaded file</button>
        </p>
        <p v-if="fileError" class="error-box" role="alert">{{ fileError }}</p>
        <p class="muted small">Readers can download the file right on the guide page.</p>
      </div>
    </div>

    <div v-if="guide">
      <label for="comment">What did you change? <span class="muted">(optional)</span></label>
      <input id="comment" v-model="form.changeComment" type="text" maxlength="200" placeholder="e.g. Fixed a typo">
    </div>

    <p class="muted small">
      By publishing, you license your contribution under
      <NuxtLink to="/license">CC BY-SA 4.0</NuxtLink> and confirm that you wrote it yourself
      or hold the rights to it.
    </p>

    <p class="actions">
      <button type="submit" class="button" :disabled="saving">
        {{ saving ? 'Publishing …' : 'Publish' }}
      </button>
      <NuxtLink :to="guide ? `/guides/${guide.slug}` : '/'">Cancel</NuxtLink>
      <span v-if="dirty" class="unsaved-hint muted small" role="status">Unsaved changes</span>
    </p>
  </form>

    <template #preview>
      <GuideReader v-if="form.mode === 'write'" :guide="livePreview" preview />
      <article v-else class="reader reader-free">
        <GuideHeader :guide="livePreview" :count="0" />
        <div v-if="selectedFile" class="file-preview">
          <p class="field-label">Preview</p>
          <p v-if="filePreview.loading" class="muted">Creating the preview …</p>
          <AttachmentViewer
            v-else
            :kind="filePreview.kind"
            :name="selectedFile.name"
            :src="filePreview.src"
            :html="filePreview.html"
          />
        </div>
        <div v-else-if="attachmentInfo" class="file-preview">
          <p class="field-label">Current file</p>
          <AttachmentViewer
            :kind="attachmentInfo.kind"
            :name="attachmentInfo.name"
            :src="attachmentInfo.view_url"
            :html="attachmentInfo.preview_html"
            :download-url="attachmentInfo.download_url"
          />
        </div>
        <p v-else class="muted">Choose a file on the left to see it here.</p>
      </article>
    </template>
  </LivePreviewLayout>
</template>
