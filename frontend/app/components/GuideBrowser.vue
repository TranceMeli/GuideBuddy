<script setup lang="ts">
import type { Category, GuideListItem, Paginated, Suggestions } from '~/types/guide'

const props = defineProps<{ categorySlug?: string; heading: string }>()

const route = useRoute()
const router = useRouter()
const base = useApiBase()

// Search field: copied into the URL (?q=) after a short delay,
// then the list reloads automatically. This keeps searches shareable.
const q = ref(String(route.query.q ?? ''))
let timer: ReturnType<typeof setTimeout> | undefined

/** Changes some URL parameters and goes back to page 1. */
function setQuery(changes: Record<string, string | undefined>) {
  const next: Record<string, string> = {}
  for (const [key, value] of Object.entries({ ...route.query, ...changes, page: undefined })) {
    if (typeof value === 'string' && value) next[key] = value
  }
  router.replace({ query: next })
}

function applySearch() {
  clearTimeout(timer)
  setQuery({ q: q.value.trim() || undefined })
}
watch(q, () => {
  clearTimeout(timer)
  timer = setTimeout(applySearch, 300)
})
onBeforeUnmount(() => clearTimeout(timer))

// Suggestions while typing: guides, categories, or the closest title after a typo
const NO_SUGGESTIONS: Suggestions = { guides: [], categories: [], did_you_mean: '' }
const suggestions = ref<Suggestions>(NO_SUGGESTIONS)
const listOpen = ref(false)
const active = ref(-1)
let suggestTimer: ReturnType<typeof setTimeout> | undefined

interface Option { key: string; label: string; hint: string; to?: string; fix?: string }
const options = computed<Option[]>(() => [
  ...suggestions.value.guides.map((g) => ({ key: `g-${g.slug}`, label: g.title, hint: 'Guide', to: `/guides/${g.slug}` })),
  ...suggestions.value.categories.map((c) => ({ key: `c-${c.slug}`, label: c.name, hint: 'Category', to: `/category/${c.slug}` })),
  ...(suggestions.value.did_you_mean
    ? [{ key: 'did-you-mean', label: `Did you mean “${suggestions.value.did_you_mean}”?`, hint: 'Spelling', fix: suggestions.value.did_you_mean }]
    : []),
])

watch(q, (value) => {
  clearTimeout(suggestTimer)
  active.value = -1
  const text = value.trim()
  if (text.length < 2) {
    suggestions.value = NO_SUGGESTIONS
    return
  }
  suggestTimer = setTimeout(async () => {
    try {
      const result = await $fetch<Suggestions>(`${base}/guides/suggest/`, { query: { q: text } })
      if (q.value.trim() === text) suggestions.value = result // ignore an answer to older text
    } catch {
      suggestions.value = NO_SUGGESTIONS // suggestions are a help only; the search itself still works
    }
  }, 200)
})
onBeforeUnmount(() => clearTimeout(suggestTimer))

function choose(option: Option) {
  listOpen.value = false
  if (option.to) return navigateTo(option.to)
  if (option.fix) {
    q.value = option.fix
    applySearch()
  }
}
function onKey(event: KeyboardEvent) {
  const count = options.value.length
  if (event.key === 'Escape') {
    listOpen.value = false
  } else if (event.key === 'ArrowDown' && count) {
    event.preventDefault()
    listOpen.value = true
    active.value = (active.value + 1) % count
  } else if (event.key === 'ArrowUp' && count) {
    event.preventDefault()
    active.value = (active.value - 1 + count) % count
  } else if (event.key === 'Enter' && listOpen.value && active.value >= 0) {
    event.preventDefault()
    choose(options.value[active.value]!)
  }
}
const showList = computed(() => listOpen.value && options.value.length > 0)

const page = computed(() => Number(route.query.page ?? 1) || 1)
const param = (name: string) => (typeof route.query[name] === 'string' ? (route.query[name] as string) : '')

const DURATIONS = [
  { value: '15', label: 'up to 15 min' },
  { value: '30', label: 'up to 30 min' },
  { value: '60', label: 'up to 1 h' },
  { value: '120', label: 'up to 2 h' },
]

const query = computed(() => ({
  q: param('q') || undefined,
  category: props.categorySlug,
  difficulty: param('level') || undefined,
  max_duration: param('duration') || undefined,
  has_pdf: param('pdf') === '1' ? '1' : undefined,
  page: page.value > 1 ? page.value : undefined,
}))
const filtered = computed(() => Boolean(param('level') || param('duration') || param('pdf')))

const { data: list, status, error } = await useFetch<Paginated<GuideListItem>>(
  `${base}/guides/`,
  { query, key: `guides-${props.categorySlug ?? 'all'}` },
)
const { data: categories } = await useFetch<Category[]>(`${base}/categories/`, {
  key: 'categories',
})

function pageLink(target: number) {
  return { query: { ...route.query, page: target > 1 ? target : undefined } }
}
// Category links keep the other filters
const categoryLink = (slug?: string) => ({ path: slug ? `/category/${slug}` : '/', query: { ...route.query, page: undefined } })
/** Quick filter pills (aria-pressed); "All" clears them. */
const quick = computed(() => [
  { label: 'Beginner', active: param('level') === 'beginner', toggle: () => setQuery({ level: param('level') === 'beginner' ? undefined : 'beginner' }) },
  { label: 'Under 15 min', active: param('duration') === '15', toggle: () => setQuery({ duration: param('duration') === '15' ? undefined : '15' }) },
  { label: 'With PDF', active: param('pdf') === '1', toggle: () => setQuery({ pdf: param('pdf') === '1' ? undefined : '1' }) },
])
function resetFilters() {
  setQuery({ level: undefined, duration: undefined, pdf: undefined })
}
/** Clears the search and every filter (the empty state offers it) */
function clearAll() {
  q.value = ''
  setQuery({ q: undefined, level: undefined, duration: undefined, pdf: undefined })
}
const searching = computed(() => Boolean(param('q') || filtered.value))
</script>

<template>
  <div class="overview">
    <section class="overview-hero" aria-labelledby="overview-title">
      <h1 id="overview-title">{{ heading }}</h1>
      <p class="hero-sub">Step by step, from the first click to the finished result.</p>
      <form role="search" class="search" @submit.prevent="applySearch">
        <label for="q" class="field-label">Search guides</label>
        <div class="search-row">
          <div class="search-box">
            <input
              id="q"
              v-model="q"
              type="search"
              placeholder="Guide, step or keyword …"
              autocomplete="off"
              role="combobox"
              aria-autocomplete="list"
              aria-controls="search-suggestions"
              :aria-expanded="showList"
              :aria-activedescendant="active >= 0 && showList ? `suggest-${active}` : undefined"
              @focus="listOpen = true"
              @blur="listOpen = false"
              @input="listOpen = true"
              @keydown="onKey"
            >
            <ul v-show="showList" id="search-suggestions" class="suggest" role="listbox" aria-label="Suggestions">
              <li
                v-for="(option, i) in options"
                :id="`suggest-${i}`"
                :key="option.key"
                role="option"
                :aria-selected="i === active"
                :class="{ active: i === active }"
                @mousedown.prevent
                @click="choose(option)"
              >
                <span>{{ option.label }}</span><span class="suggest-hint">{{ option.hint }}</span>
              </li>
            </ul>
          </div>
          <button type="submit" class="btn hero-btn"><GuideIcon name="search" :size="18" /> Search</button>
        </div>
      </form>
    </section>

    <FirstVisitTip v-if="!categorySlug" />

    <div class="filter-pills" role="group" aria-label="Quick filters">
      <button type="button" class="pill-btn" :aria-pressed="!filtered" @click="resetFilters">All</button>
      <button v-for="f in quick" :key="f.label" type="button" class="pill-btn" :aria-pressed="f.active" @click="f.toggle">{{ f.label }}</button>
    </div>

    <nav aria-label="Categories" class="filter-pills">
      <NuxtLink :to="categoryLink()" class="pill-btn" :aria-current="!categorySlug ? 'page' : undefined">All categories</NuxtLink>
      <NuxtLink
        v-for="c in categories ?? []"
        :key="c.id"
        :to="categoryLink(c.slug)"
        class="pill-btn pill-cat"
        :class="`tint-${placeholderFor(c.slug, 'page', c.slug).tint}`"
        :aria-current="categorySlug === c.slug ? 'page' : undefined"
      >
        <GuideIcon :name="placeholderFor(c.slug, 'page', c.slug).icon" :size="16" /> {{ c.name }}
      </NuxtLink>
    </nav>

    <details class="more-filters" :open="Boolean((param('level') && param('level') !== 'beginner') || (param('duration') && param('duration') !== '15'))">
      <summary>More filters</summary>
      <div class="filters" role="group" aria-label="More filters">
        <div>
          <label for="filter-level">Level</label>
          <select id="filter-level" :value="param('level')" @change="setQuery({ level: ($event.target as HTMLSelectElement).value })">
            <option value="">All levels</option>
            <option v-for="d in DIFFICULTIES" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>
        <div>
          <label for="filter-duration">Duration</label>
          <select id="filter-duration" :value="param('duration')" @change="setQuery({ duration: ($event.target as HTMLSelectElement).value })">
            <option value="">Any</option>
            <option v-for="d in DURATIONS" :key="d.value" :value="d.value">{{ d.label }}</option>
          </select>
        </div>
      </div>
    </details>

    <div aria-live="polite">
      <p v-if="error" class="error-box">The guides could not be loaded. Is the backend running?</p>
      <template v-else-if="list">
        <p class="result-count">{{ status === 'pending' ? 'Loading guides …' : `${list.count} ${list.count === 1 ? 'guide' : 'guides'}` }}</p>
        <ul v-if="status === 'pending'" class="guide-cards" aria-hidden="true">
          <li v-for="n in Math.min(Math.max(list.results.length, 3), 6)" :key="n" class="guide-card guide-skeleton">
            <div class="sk sk-image" />
            <div class="card-body"><div class="sk sk-line sk-short" /><div class="sk sk-line" /><div class="sk sk-line sk-medium" /></div>
          </li>
        </ul>
        <ul v-else-if="list.results.length" class="guide-cards">
          <GuideCard v-for="guide in list.results" :key="guide.slug" :guide="guide" />
        </ul>
        <div v-else class="empty-state">
          <GuideIcon name="compass" :size="32" />
          <h2>No guides found</h2>
          <p v-if="searching">Nothing matches your search and filters. Try fewer words or clear the filters.</p>
          <p v-else>There are no guides here yet. Write the first one.</p>
          <button v-if="searching" type="button" class="btn btn-primary" @click="clearAll">Clear search and filters</button>
          <NuxtLink v-else to="/guides/new" class="btn btn-primary">Write a guide</NuxtLink>
        </div>

        <nav v-if="list.previous || list.next" aria-label="Pages" class="pager">
          <NuxtLink v-if="list.previous" :to="pageLink(page - 1)" class="btn btn-secondary btn-small">← Previous</NuxtLink>
          <span class="muted">Page {{ page }}</span>
          <NuxtLink v-if="list.next" :to="pageLink(page + 1)" class="btn btn-secondary btn-small">Next →</NuxtLink>
        </nav>
      </template>
    </div>
  </div>
</template>
