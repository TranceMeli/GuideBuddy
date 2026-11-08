<script setup lang="ts">
import type { Guide, GuideElement } from '~/types/guide'

/**
 * Reading view of a guide built from elements: one element after the other, in the order the
 * author chose. Sections get a label and a rule, steps a numbered badge that readers can tick
 * off (kept in this browser only), notices a coloured bar with icon and word.
 */
const props = defineProps<{ guide: Guide; preview?: boolean }>()
const t = useGuideLabels()

const numbers = computed(() => {
  let section = 0
  let step = 0
  return props.guide.elements.map((el) => (el.kind === 'section' ? ++section : el.kind === 'step' ? ++step : 0))
})

// End of a section: where to go next, and back to the top (not in the preview)
const feet = computed(() => {
  const els = props.guide.elements
  const hasSections = els.some((e) => e.kind === 'section')
  return els.map((_, i) => {
    if (props.preview || !hasSections) return null
    const next = els[i + 1]
    if (!next) return { title: '', id: 0 }
    return next.kind === 'section' && next.id ? { title: next.text, id: next.id } : null
  })
})

// --- Steps readers tick off (this browser only) ------------------------------------------
const done = ref<Set<string>>(new Set())
const storageKey = computed(() => `guidebuddy:done:${props.guide.slug}`)
const stepKey = (el: GuideElement, index: number) => String(el.id ?? `n${numbers.value[index]}`)

onMounted(() => {
  if (props.preview) return
  try {
    const saved = JSON.parse(localStorage.getItem(storageKey.value) ?? '[]')
    if (Array.isArray(saved)) done.value = new Set(saved.map(String))
  } catch {
    // Storage may be blocked; ticks then last only for this visit
  }
})
function toggle(key: string) {
  const next = new Set(done.value)
  if (!next.delete(key)) next.add(key)
  done.value = next
  if (props.preview) return
  try {
    localStorage.setItem(storageKey.value, JSON.stringify([...next]))
  } catch {
    // see above
  }
}

// Comment buttons on every element (only on the guide page, see GuideComments.vue)
const commentsOn = useState<boolean>('gb-comments-on', () => false)
const counts = useState<Record<number, number>>('gb-comment-counts', () => ({}))
const target = useState<{ element: number; n: number } | null>('gb-comment-target', () => null)
function openComments(el: GuideElement) {
  if (el.id) target.value = { element: el.id, n: (target.value?.n ?? 0) + 1 }
}

const NOTICE: Record<string, 'tip' | 'note' | 'important' | 'warning' | 'danger' | 'error' | 'result'> = {
  important: 'important', warning: 'warning', danger: 'danger', error: 'error', tip: 'tip', note: 'note', result: 'result',
}

function figure(el: GuideElement) {
  const image = el.image
  if (!image) return ''
  return [image.kind ? t.value.imageKinds[image.kind] : '', image.caption].filter(Boolean).join(': ')
}
const items = (text: string) => text.split('\n').map((l) => l.trim()).filter(Boolean)
</script>

<template>
  <div class="elements-reader">
    <p v-if="!guide.elements.length" class="muted" :lang="t.lang">{{ t.noContent }}</p>

    <div v-for="(el, i) in guide.elements" :id="el.id && !preview ? `el-${el.id}` : undefined" :key="el.id ?? i" class="el-row">
      <!-- structure -->
      <template v-if="el.kind === 'section'">
        <p class="section-chip" :lang="t.lang">{{ t.section }} {{ numbers[i] }}</p>
        <h2 class="section-title">{{ el.text }}</h2>
      </template>
      <div v-else-if="el.kind === 'step'" class="el-step">
        <button type="button" class="el-badge" :class="{ 'is-done': done.has(stepKey(el, i)) }" :aria-pressed="done.has(stepKey(el, i))" :aria-label="`${t.step} ${numbers[i]}: ${t.stepDone}`" @click="toggle(stepKey(el, i))">
          <GuideIcon v-if="done.has(stepKey(el, i))" name="check" :size="20" />
          <template v-else>{{ numbers[i] }}</template>
        </button>
        <h3 class="step-title"><span class="visually-hidden">{{ t.step }} {{ numbers[i] }}: </span>{{ el.text }}</h3>
        <span v-if="done.has(stepKey(el, i))" class="step-done-word" :lang="t.lang">Done</span>
      </div>
      <h3 v-else-if="el.kind === 'heading'" class="el-heading">{{ el.text }}</h3>
      <hr v-else-if="el.kind === 'divider'" class="el-divider">

      <!-- text -->
      <!-- html is sanitized by the backend (nh3) -->
      <!-- eslint-disable vue/no-v-html -->
      <div v-else-if="el.kind === 'text'" class="prose reading el-block" v-html="el.html" />
      <div v-else-if="el.kind === 'list'" class="prose reading el-block" v-html="el.html" />
      <ul v-else-if="el.kind === 'checklist'" class="el-checklist el-block">
        <li v-for="(item, k) in items(el.text)" :key="k">
          <label><input type="checkbox"> <span>{{ item }}</span></label>
        </li>
      </ul>
      <blockquote v-else-if="el.kind === 'quote'" class="el-quote el-block">
        <div class="prose" v-html="el.html" />
        <footer v-if="el.data.source">{{ el.data.source }}</footer>
      </blockquote>
      <p v-else-if="el.kind === 'link'" class="el-link el-block">
        <a v-if="el.data.url" :href="el.data.url" rel="noopener noreferrer" target="_blank">{{ el.text || el.data.url }}<GuideIcon name="arrow-right" :size="14" /></a>
        <template v-else>{{ el.text }}</template>
      </p>
      <p v-else-if="el.kind === 'download'" class="el-block">
        <a v-if="el.data.url" class="btn btn-secondary" :href="el.data.url" rel="noopener noreferrer" download><GuideIcon name="download" :size="18" /> {{ el.text || el.data.url }}</a>
        <span v-else class="btn btn-secondary">{{ el.text }}</span>
      </p>
      <div v-else-if="el.kind === 'table'" class="prose el-block">
        <table v-if="el.data.rows?.length">
          <thead><tr><th v-for="(cell, c) in el.data.rows[0]" :key="c">{{ cell }}</th></tr></thead>
          <tbody><tr v-for="(row, r) in el.data.rows.slice(1)" :key="r"><td v-for="(cell, c) in row" :key="c">{{ cell }}</td></tr></tbody>
        </table>
      </div>
      <details v-else-if="el.kind === 'collapsible'" class="el-collapsible el-block">
        <summary>{{ el.text }}</summary>
        <div class="prose" v-html="el.html" />
      </details>

      <!-- notices -->
      <Callout v-else-if="NOTICE[el.kind]" class="el-block" :kind="NOTICE[el.kind]!" :html="el.html" />

      <!-- media -->
      <figure v-else-if="el.kind === 'image' && el.image" class="el-image el-block">
        <img :src="el.image.url" :alt="el.image.alt" :width="el.image.width" :height="el.image.height" loading="lazy">
        <figcaption v-if="figure(el)" class="figure-caption" :data-figure="t.figure" :lang="t.lang">{{ figure(el) }}</figcaption>
      </figure>
      <figure v-else-if="el.kind === 'diagram'" class="el-diagram el-block">
        <ol>
          <li v-for="(node, k) in el.data.nodes ?? []" :key="k"><span>{{ node }}</span></li>
        </ol>
        <figcaption v-if="el.text" class="figure-caption" :data-figure="t.figure" :lang="t.lang">{{ el.text }}</figcaption>
      </figure>
      <div v-else-if="el.kind === 'terminal' || el.kind === 'code'" class="prose el-code el-block" v-html="el.html" />
      <div v-else-if="el.kind === 'compare'" class="el-compare el-block">
        <p v-if="el.text" class="el-compare-note">{{ el.text }}</p>
        <div class="el-compare-grid">
          <div class="el-wrong"><p class="el-compare-label"><GuideIcon name="close" :size="16" /> {{ t.wrong }}</p><div class="prose" v-html="el.data.wrong_html" /></div>
          <div class="el-right"><p class="el-compare-label"><GuideIcon name="check" :size="16" /> {{ t.right }}</p><div class="prose" v-html="el.data.right_html" /></div>
        </div>
      </div>
      <!-- eslint-enable vue/no-v-html -->
      <p v-if="feet[i]" class="section-foot">
        <a href="#main" class="foot-top"><GuideIcon name="arrow-up" :size="16" /> Back to top</a>
        <a v-if="feet[i]!.id" :href="`#el-${feet[i]!.id}`" class="btn btn-primary btn-small">Next: {{ feet[i]!.title }} <GuideIcon name="arrow-right" :size="16" /></a>
      </p>
      <button v-if="commentsOn && !preview && el.id" type="button" class="el-comment" :class="{ 'has-comments': counts[el.id] }" :aria-label="counts[el.id] ? `${counts[el.id]} comments on this element` : 'Comment on this element'" @click="openComments(el)">
        <GuideIcon name="info" :size="14" /><span v-if="counts[el.id]">{{ counts[el.id] }}</span><span v-else class="el-comment-add">Comment</span>
      </button>
    </div>
  </div>
</template>
