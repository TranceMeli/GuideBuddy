<script setup lang="ts">
/**
 * Fixed reading bars of a guide, like the Lernskripte: a slim bar under the site header
 * (title, contents, "Aa" with text size and dark mode) with a thin progress line, and a status
 * bar at the bottom ("Section 2 of 6 · title" and the percentage read). Sections are the
 * h2 headings of the guide; the text size is kept in the cookie "gb_fs".
 */
const props = defineProps<{ title: string }>()
const { mode } = useTheme()

const SIZES = [1.0625, 1.125, 1.1875, 1.3125, 1.4375, 1.5625] // rem; 1.1875 = 19px is the default
const fsIndex = useCookie<number>('gb_fs', { default: () => 2, maxAge: 60 * 60 * 24 * 365, sameSite: 'lax', path: '/' })
if (!(fsIndex.value >= 0 && fsIndex.value < SIZES.length)) fsIndex.value = 2
useHead({ htmlAttrs: { style: computed(() => (fsIndex.value === 2 ? undefined : `--text-size:${SIZES[fsIndex.value]}rem`)) } })

const sections = ref<{ id: string; title: string }[]>([])
const current = ref(0)
const percent = ref(0)
const panel = ref<'' | 'toc' | 'aa'>('')
const root = ref<HTMLElement | null>(null)

function collect() {
  // guides mark their sections; other guides use every h2
  const marked = document.querySelectorAll<HTMLElement>('.reader .section-title')
  const heads = marked.length ? [...marked] : [...document.querySelectorAll<HTMLElement>('.reader h2')].filter((h) => !h.closest('aside'))
  sections.value = heads.map((h, i) => {
    if (!h.id) h.id = `reading-section-${i + 1}`
    return { id: h.id, title: (h.textContent ?? '').trim() }
  })
  update()
}

function update() {
  const doc = document.documentElement
  const max = doc.scrollHeight - window.innerHeight
  percent.value = max > 0 ? Math.min(100, Math.max(0, Math.round((window.scrollY / max) * 100))) : 100
  let index = 0
  sections.value.forEach((s, i) => {
    const el = document.getElementById(s.id)
    if (el && el.getBoundingClientRect().top < window.innerHeight * 0.4) index = i
  })
  current.value = index
}

function go(id: string) {
  panel.value = ''
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const dark = computed(() => mode.value === 'dark')
function toggleDark() {
  mode.value = dark.value ? 'light' : 'dark'
}
function size(delta: number) {
  fsIndex.value = Math.min(SIZES.length - 1, Math.max(0, fsIndex.value + delta))
}

function onDocClick(event: MouseEvent) {
  if (panel.value && !root.value?.contains(event.target as Node)) panel.value = ''
}
function onKey(event: KeyboardEvent) {
  if (event.key === 'Escape') panel.value = ''
}

let timer: ReturnType<typeof setTimeout> | undefined
onMounted(() => {
  timer = setTimeout(collect, 30) // headings render after the page; requestAnimationFrame does not run in hidden panes
  window.addEventListener('scroll', update, { passive: true })
  window.addEventListener('resize', update)
  document.addEventListener('click', onDocClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  clearTimeout(timer)
  window.removeEventListener('scroll', update)
  window.removeEventListener('resize', update)
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('keydown', onKey)
})
watch(() => props.title, () => setTimeout(collect, 30))
</script>

<template>
  <ClientOnly>
    <div ref="root" class="rbars">
      <div class="rbar">
        <div class="rbar-in">
          <p class="rbar-title">{{ title }}</p>
          <div class="rbar-btns">
            <button type="button" :aria-pressed="dark" @click="toggleDark">{{ dark ? 'Light' : 'Dark' }}</button>
            <button type="button" :aria-expanded="panel === 'aa'" aria-controls="rbar-aa" @click.stop="panel = panel === 'aa' ? '' : 'aa'">Aa</button>
            <button v-if="sections.length > 1" type="button" :aria-expanded="panel === 'toc'" aria-controls="rbar-toc" @click.stop="panel = panel === 'toc' ? '' : 'toc'">Contents</button>
          </div>
        </div>
        <span class="rbar-prog" :style="{ width: `${percent}%` }" aria-hidden="true" />

        <div v-if="panel === 'toc'" id="rbar-toc" class="rbar-panel" role="dialog" aria-label="Contents">
          <ol>
            <li v-for="(s, i) in sections" :key="s.id">
              <a :href="`#${s.id}`" :class="{ 'is-current': i === current }" @click.prevent="go(s.id)">{{ s.title }}</a>
            </li>
          </ol>
        </div>
        <div v-if="panel === 'aa'" id="rbar-aa" class="rbar-panel" role="dialog" aria-label="Display">
          <h4>Text size</h4>
          <div class="rbar-opts">
            <button type="button" :disabled="fsIndex === 0" aria-label="Smaller text" @click="size(-1)">A−</button>
            <button type="button" :disabled="fsIndex === SIZES.length - 1" aria-label="Larger text" @click="size(1)">A+</button>
            <button type="button" :disabled="fsIndex === 2" @click="fsIndex = 2">Reset</button>
          </div>
        </div>
      </div>

      <div class="rstatus" role="status">
        <div class="rstatus-in">
          <span>{{ sections.length ? `Section ${current + 1} of ${sections.length} · ${sections[current]?.title}` : title }}</span>
          <span>{{ percent }} %</span>
        </div>
      </div>
    </div>
  </ClientOnly>
</template>
