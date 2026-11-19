<script setup lang="ts">
import type { BuilderGroup, BuilderPart } from '~/composables/useBuilder'
import type { ElementKind } from '~/types/guide'
import type { Check } from '~/utils/publishChecks'
import type { ElementDraft, ToolId } from '~/utils/elements'

/**
 * Guide builder, laid out like a design tool. Top: edit buttons (undo, redo, duplicate, move,
 * delete) and the options of the chosen tool. Left: the tools. Middle: the guide as a list of
 * cards, one per element, in the order readers see them. Right: a panel with the properties of
 * the selected element, an outline, the writing suggestions and help for the chosen tool.
 *
 * The page starts blank and nothing is required. A tool is chosen by click or key (the keys
 * are shown next to the tools); an element is placed by clicking "Place here" between the
 * cards, or by dragging the tool onto the guide. Select (V, or Esc) is the tool for editing.
 * Empty elements show their placeholder, in the guide and in the live preview.
 */
const elements = defineModel<ElementDraft[]>({ required: true })
const props = defineProps<{ checks?: Check[]; savedAt?: string }>()
const { say, removed, removeFromList, reveal, newPart, moving, dropTarget, over } = useBuilder()

const tool = ref<ToolId>('select')
const hover = ref<ToolId | null>(null)
const selKey = ref<string | null>(null)
const panelTab = ref<'props' | 'outline' | 'checks' | 'help'>('props')

const PALETTE: BuilderGroup[] = TOOL_GROUPS.map((group) => ({
  group,
  parts: TOOLS.filter((t) => t.group === group).map((t): BuilderPart => ({
    id: t.id, label: t.label, icon: t.icon, hint: `${t.what} ${t.how}`, shortcut: t.shortcut,
  })),
}))

const numbers = computed(() => numbering(elements.value))
const selIndex = computed(() => elements.value.findIndex((e) => e.key === selKey.value))
const selected = computed(() => (selIndex.value >= 0 ? elements.value[selIndex.value]! : null))
const info = computed(() => TOOL[hover.value ?? tool.value])
const armed = computed(() => tool.value !== 'select')

function label(el: ElementDraft, index: number) {
  const n = numbers.value[index]
  return n ? `${TOOL[el.kind].label} ${n}` : TOOL[el.kind].label
}

/** The line a card shows: the text, or what is in the element */
function summary(el: ElementDraft): string {
  const d = el.data
  const first = (text: string) => text.trim().split('\n')[0] ?? ''
  switch (el.kind) {
    case 'divider': return ''
    case 'image': return el.image ? [el.image.kind, el.image.caption || el.image.alt].filter(Boolean).join(': ') : ''
    case 'table': return (d.rows ?? []).flat().filter((c) => c.trim()).slice(0, 4).join(', ')
    case 'diagram': return (d.nodes ?? []).filter((n) => n.trim()).join(' → ')
    case 'compare': return first(el.text) || first(d.wrong ?? '')
    case 'collapsible': return first(el.text)
    case 'link':
    case 'download': return first(el.text) || (d.url ?? '')
    default: return first(el.text)
  }
}
const cardPlaceholder = (el: ElementDraft) => el.hint ?? (el.kind === 'divider' ? 'A line between two parts' : ELEMENT_PLACEHOLDERS[el.kind])
const placeholderOf = (el: ElementDraft) => el.hint ?? ELEMENT_PLACEHOLDERS[el.kind]

function select(key: string | null) {
  selKey.value = key
}
const cardId = (key: string) => `bd-card-${key}`

// Tools
function chooseTool(id: string) {
  const next = id as ToolId
  tool.value = next === 'select' || next === tool.value ? 'select' : next
  if (tool.value !== 'select') panelTab.value = 'help'
}

// The tools used last, kept in this browser
const recent = ref<string[]>([])
onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem('guidebuddy:recent-tools') ?? '[]')
    if (Array.isArray(saved)) recent.value = saved.filter((id) => typeof id === 'string' && id in TOOL).slice(0, 3)
  } catch {
    // storage may be blocked; the list then lasts for this visit
  }
})
function rememberTool(kind: string) {
  recent.value = [kind, ...recent.value.filter((id) => id !== kind)].slice(0, 3)
  try {
    localStorage.setItem('guidebuddy:recent-tools', JSON.stringify(recent.value))
  } catch {
    // see above
  }
}

function insertAt(at: number, kind: ElementKind) {
  if (elements.value.length >= MAX_ELEMENTS) return say(`A guide has at most ${MAX_ELEMENTS} elements.`)
  rememberTool(kind)
  const el = newElement(kind)
  elements.value.splice(at, 0, el)
  select(el.key)
  reveal(cardId(el.key))
}

function place(at: number) {
  if (tool.value === 'select') return
  insertAt(at, tool.value)
  tool.value = 'select'
}

function remove(index: number) {
  const el = elements.value[index]!
  if (selKey.value === el.key) selKey.value = null
  removeFromList(elements.value, index, `${TOOL[el.kind].label}`)
}

function move(index: number, delta: -1 | 1) {
  const to = index + delta
  if (to < 0 || to >= elements.value.length) return
  const list = elements.value
  ;[list[index], list[to]] = [list[to]!, list[index]!]
}

/** Copies an element right below itself (the copy is new: no id, own key) */
function duplicate(index = selIndex.value) {
  const el = elements.value[index]
  if (!el) return
  if (elements.value.length >= MAX_ELEMENTS) return say(`A guide has at most ${MAX_ELEMENTS} elements.`)
  const copy = JSON.parse(JSON.stringify(el)) as ElementDraft
  copy.key = localKey()
  delete copy.id
  elements.value.splice(index + 1, 0, copy)
  select(copy.key)
  reveal(cardId(copy.key))
  say('Duplicated.')
}

// Undo and redo for the whole guide
// Snapshots of the list, taken half a second after the last change, so typing counts as one step.
const past = ref<string[]>([])
const future = ref<string[]>([])
const snapshot = () => JSON.stringify(elements.value)
let current = snapshot()
let applying = false
let historyTimer: ReturnType<typeof setTimeout> | undefined

function commit() {
  clearTimeout(historyTimer)
  const now = snapshot()
  if (now === current) return
  past.value.push(current)
  if (past.value.length > 100) past.value.shift()
  current = now
  future.value = []
}
watch(elements, () => {
  if (applying) return
  clearTimeout(historyTimer)
  historyTimer = setTimeout(commit, 500)
}, { deep: true })
onBeforeUnmount(() => clearTimeout(historyTimer))

async function applySnapshot(json: string) {
  applying = true
  elements.value = JSON.parse(json) as ElementDraft[]
  if (selKey.value && !elements.value.some((e) => e.key === selKey.value)) selKey.value = null
  await nextTick()
  applying = false
}
function undo() {
  commit()
  const before = past.value.pop()
  if (before === undefined) return say('Nothing to undo.')
  future.value.push(current)
  current = before
  applySnapshot(before)
  say('Undone.')
}
function redo() {
  commit()
  const after = future.value.pop()
  if (after === undefined) return say('Nothing to redo.')
  past.value.push(current)
  current = after
  applySnapshot(after)
  say('Redone.')
}
const canUndo = computed(() => past.value.length > 0 || snapshot() !== current)

// Outline and numbers for the status bar
const outline = computed(() =>
  elements.value
    .map((el, i) => ({ el, i }))
    .filter(({ el }) => ['section', 'step', 'heading'].includes(el.kind))
    .map(({ el, i }) => ({ key: el.key, kind: el.kind, label: label(el, i), text: el.text.trim() })),
)
function jump(key: string) {
  select(key)
  reveal(cardId(key))
}
const wordCount = (text?: string) => (text?.trim() ? text.trim().split(/\s+/).length : 0)
const words = computed(() =>
  elements.value.reduce((sum, el) => {
    const d = el.data
    const cells = (d.rows ?? []).flat().reduce((n, c) => n + wordCount(c), 0)
    const nodes = (d.nodes ?? []).reduce((n, c) => n + wordCount(c), 0)
    return sum + wordCount(el.text) + wordCount(d.body) + wordCount(d.wrong) + wordCount(d.right) + cells + nodes
  }, 0),
)
const readMinutes = computed(() => Math.max(1, Math.round(words.value / 200)))
const suggestions = computed(() => (props.checks ?? []).filter((c) => !c.ok).length)

// Keyboard shortcuts of the tools (not while typing); Esc returns to Select
function onKeydown(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  const typing = Boolean(target && (target.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)))
  const mod = event.ctrlKey || event.metaKey
  if (mod && !event.altKey) {
    if (typing) return // text fields keep their own undo
    const k = event.key.toLowerCase()
    if (k === 'z' && !event.shiftKey) { event.preventDefault(); undo() } else if (k === 'y' || (k === 'z' && event.shiftKey)) { event.preventDefault(); redo() } else if (k === 'd' && selected.value) { event.preventDefault(); duplicate() }
    return
  }
  if (event.altKey && !mod) {
    if (typing || !selected.value || !['ArrowUp', 'ArrowDown'].includes(event.key)) return
    event.preventDefault()
    move(selIndex.value, event.key === 'ArrowUp' ? -1 : 1)
    return
  }
  if (typing) return
  if (event.key === 'Delete' && selected.value) {
    event.preventDefault()
    remove(selIndex.value)
    return
  }
  if (event.key === 'Escape') {
    tool.value = 'select'
    return
  }
  const key = event.key.toUpperCase()
  const found = TOOLS.find((t) => t.shortcut === key)
  if (found) {
    event.preventDefault()
    chooseTool(found.id)
  }
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

// Drag and drop (mouse; touch and keyboard place with the tool)
const gapAccepts = computed(() => Boolean(moving('element')) || Boolean(newPart.value))

function dropAt(at: number) {
  const key = moving('element')
  if (newPart.value) {
    insertAt(at, newPart.value as ElementKind)
  } else if (key) {
    const from = elements.value.findIndex((e) => e.key === key)
    if (from >= 0) moveWithin(elements.value, from, at)
  }
}
/** Fills a blank page with the parts of a how-to guide (empty, so nothing has to be kept) */
function startFromTemplate() {
  commit()
  elements.value = howToTemplate()
  select(elements.value[0]!.key)
  say('Template added. Write into the parts you need and remove the rest.')
}
const canvasTarget = dropTarget('canvas', () => Boolean(newPart.value), () => insertAt(elements.value.length, newPart.value as ElementKind))

// Properties
const panelTitle = computed(() => (selected.value ? label(selected.value, selIndex.value) : ''))
const NOTICE_HINT: Partial<Record<ElementKind, string>> = {
  important: 'Yellow box. What matters, or what to watch out for.',
  warning: 'Coral box. A risk of injury or damage, and how to avoid it.',
  danger: 'Dark red box. An immediate threat to life or health.',
  error: 'Red box. An error, data loss or something that cannot be undone, and how to avoid it.',
  tip: 'A faster or easier way to do it.',
  note: 'Good to know, but not required.',
  result: 'What it looks like when the step worked.',
}

// Lines of a textarea <-> list in the data (diagram boxes)
const nodesText = computed({
  get: () => (selected.value?.data.nodes ?? []).join('\n'),
  set: (value: string) => {
    if (selected.value) selected.value.data.nodes = value.split('\n')
  },
})

// Table: the cells of the selected element
const rows = computed(() => selected.value?.data.rows ?? [])
function addRow() {
  const width = rows.value[0]?.length ?? 2
  if (rows.value.length >= 20) return say('A table has at most 20 rows.')
  selected.value!.data.rows = [...rows.value, Array(width).fill('')]
}
function addColumn() {
  if ((rows.value[0]?.length ?? 0) >= 8) return say('A table has at most 8 columns.')
  selected.value!.data.rows = rows.value.map((row) => [...row, ''])
}
function removeRow(i: number) {
  if (rows.value.length > 1) selected.value!.data.rows = rows.value.filter((_, k) => k !== i)
}
function removeColumn(c: number) {
  if ((rows.value[0]?.length ?? 0) > 1) selected.value!.data.rows = rows.value.map((row) => row.filter((_, k) => k !== c))
}
</script>

<template>
  <BuilderShell v-model:tab="panelTab" :editing="Boolean(selected)">
    <template #options>
      <BuilderToolbar
        :can-undo="canUndo"
        :can-redo="future.length > 0"
        :has-selection="Boolean(selected)"
        :can-up="selIndex > 0"
        :can-down="selIndex >= 0 && selIndex < elements.length - 1"
        :saved-at="savedAt"
        @undo="undo"
        @redo="redo"
        @duplicate="duplicate()"
        @up="move(selIndex, -1)"
        @down="move(selIndex, 1)"
        @remove="remove(selIndex)"
      />
      <span class="bd-opt-sep" aria-hidden="true" />
      <span class="bd-opt-tool"><GuideIcon :name="TOOL[tool].icon" :size="16" /> {{ TOOL[tool].label }}</span>
      <span class="bd-opt-sep" aria-hidden="true" />
      <span v-if="armed" class="bd-opt-hint">{{ TOOL[tool].what }} Click “Place here” in the guide. Esc cancels.</span>
      <span v-else class="bd-opt-hint">Click an element to edit it. Choose a tool (or press its key) to add something. Nothing is required.</span>
    </template>

    <template #palette>
      <BuilderPalette :groups="PALETTE" :armed="tool" :recent="recent" @add="chooseTool" @hover="hover = ($event as ToolId | null)" />
    </template>

    <template #help>
      <p class="bd-help-title">
        <GuideIcon :name="info.icon" :size="16" /> {{ info.label }}
        <kbd class="bd-key bd-help-key">{{ info.shortcut }}</kbd>
      </p>
      <p style="margin: 0">{{ info.what }}</p>
      <dl>
        <div><dt>How to use</dt><dd>{{ info.how }}</dd></div>
        <div><dt>What readers see</dt><dd>{{ info.readers }}</dd></div>
      </dl>
    </template>

    <template #outline>
      <p v-if="!outline.length" class="muted small">Sections, steps and headings appear here. Click one to jump to it.</p>
      <ol v-else class="bd-outline-list">
        <li v-for="item in outline" :key="item.key" :class="`is-${item.kind}`">
          <button type="button" :class="{ 'is-current': selKey === item.key }" @click="jump(item.key)">
            <span class="bd-outline-kind">{{ item.label }}</span>
            <span class="bd-outline-text">{{ item.text || 'Untitled' }}</span>
          </button>
        </li>
      </ol>
    </template>

    <template v-if="checks" #checks>
      <ul class="publish-checks-list">
        <li v-for="check in checks" :key="check.id" :class="check.ok ? 'is-ok' : 'is-open'">
          <span class="publish-checks-mark" aria-hidden="true">{{ check.ok ? '✓' : '!' }}</span>
          <span>
            {{ check.label }}<span class="visually-hidden">: {{ check.ok ? 'done' : 'to do' }}</span>
            <small v-if="!check.ok">{{ check.hint }}</small>
          </span>
        </li>
      </ul>
      <p class="muted small">These only advise; you can always publish.</p>
    </template>

    <template #panel>
      <BuilderPanel v-if="selected" :title="panelTitle" @done="select(null)" @remove="remove(selIndex)">
        <div class="bd-type-row">
          <span class="muted small">Position</span>
          <ItemTools :index="selIndex" :count="elements.length" :min="0" :name="panelTitle" @up="move(selIndex, -1)" @down="move(selIndex, 1)" @remove="remove(selIndex)" />
        </div>

        <!-- section, step, heading -->
        <div v-if="['section', 'step', 'heading'].includes(selected.kind)">
          <label for="f-title">Title</label>
          <input id="f-title" v-model="selected.text" type="text" maxlength="160" :placeholder="placeholderOf(selected)">
        </div>

        <!-- text, notices, quote -->
        <template v-else-if="MARKDOWN_KINDS.includes(selected.kind)">
          <MarkdownField id="f-text" v-model="selected.text" :label="TOOL[selected.kind].label" :hint="NOTICE_HINT[selected.kind]" :maxlength="selected.kind === 'text' ? 5000 : 1000" :rows="selected.kind === 'text' ? 8 : 5" :placeholder="placeholderOf(selected)" />
          <div v-if="selected.kind === 'quote'">
            <label for="f-source">Source <span class="muted">(optional)</span></label>
            <input id="f-source" v-model="selected.data.source" type="text" maxlength="120">
          </div>
        </template>

        <!-- list, checklist -->
        <div v-else-if="selected.kind === 'list' || selected.kind === 'checklist'">
          <label for="f-lines">{{ selected.kind === 'list' ? 'List' : 'Checklist' }} <span class="muted">(one item per line)</span></label>
          <textarea id="f-lines" v-model="selected.text" rows="6" maxlength="2000" placeholder="First item&#10;Second item" />
        </div>

        <!-- link, download -->
        <template v-else-if="selected.kind === 'link' || selected.kind === 'download'">
          <div>
            <label for="f-label">{{ selected.kind === 'link' ? 'Link text' : 'Button label' }}</label>
            <input id="f-label" v-model="selected.text" type="text" maxlength="120" :placeholder="selected.kind === 'link' ? 'Say where it leads, e.g. The Python downloads page' : 'e.g. Download the template'">
            <p class="muted small">Avoid “here” and “click here”: the words alone should say where the link goes.</p>
          </div>
          <div>
            <label for="f-url">Address</label>
            <input id="f-url" v-model="selected.data.url" type="url" maxlength="500" placeholder="https://…">
          </div>
        </template>

        <!-- table -->
        <template v-else-if="selected.kind === 'table'">
          <p class="muted small">The first row is the heading.</p>
          <div class="tbl-edit">
            <div v-for="(row, r) in rows" :key="r" class="tbl-row">
              <input v-for="(_, c) in row" :key="c" v-model="rows[r]![c]" type="text" maxlength="200" :aria-label="`Row ${r + 1}, column ${c + 1}`">
              <button type="button" class="icon-button danger" :disabled="rows.length <= 1" :aria-label="`Remove row ${r + 1}`" @click="removeRow(r)">✕</button>
            </div>
            <div class="tbl-row">
              <button v-for="(_, c) in rows[0] ?? []" :key="c" type="button" class="ed-add-link" :aria-label="`Remove column ${c + 1}`" @click="removeColumn(c)">Remove column {{ c + 1 }}</button>
            </div>
          </div>
          <button type="button" class="ed-add-link" @click="addRow">+ Row</button>
          <button type="button" class="ed-add-link" @click="addColumn">+ Column</button>
        </template>

        <!-- collapsible -->
        <template v-else-if="selected.kind === 'collapsible'">
          <div>
            <label for="f-q">Title</label>
            <input id="f-q" v-model="selected.text" type="text" maxlength="200" :placeholder="ELEMENT_PLACEHOLDERS.collapsible">
          </div>
          <MarkdownField id="f-body" :model-value="selected.data.body ?? ''" label="Text that opens" :maxlength="3000" :rows="6" @update:model-value="selected.data.body = $event" />
        </template>

        <!-- image -->
        <template v-else-if="selected.kind === 'image'">
          <div><span class="field-label">Image</span></div>
          <ImagePicker id="f-image" v-model="selected.image" />
        </template>

        <!-- diagram -->
        <template v-else-if="selected.kind === 'diagram'">
          <div>
            <label for="f-nodes">Boxes <span class="muted">(one per line, in order)</span></label>
            <textarea id="f-nodes" v-model="nodesText" rows="6" placeholder="Open the installer&#10;Tick the PATH box&#10;Click Install Now" />
          </div>
          <div>
            <label for="f-dcap">Caption <span class="muted">(optional)</span></label>
            <input id="f-dcap" v-model="selected.text" type="text" maxlength="200">
          </div>
        </template>

        <!-- terminal, code -->
        <template v-else-if="selected.kind === 'terminal' || selected.kind === 'code'">
          <div v-if="selected.kind === 'code'">
            <label for="f-lang">Language <span class="muted">(for example python)</span></label>
            <input id="f-lang" v-model="selected.data.language" type="text" maxlength="30">
          </div>
          <div>
            <label for="f-code">{{ selected.kind === 'terminal' ? 'Commands and answers' : 'Code' }}</label>
            <textarea id="f-code" v-model="selected.text" class="code-input" rows="8" maxlength="4000" spellcheck="false" :placeholder="selected.kind === 'terminal' ? '$ python --version\nPython 3.13.0' : ''" />
            <p v-if="selected.kind === 'terminal'" class="muted small">Start a command with “$ ”. Lines with an error turn red, successes green.</p>
          </div>
        </template>

        <!-- wrong and right -->
        <template v-else-if="selected.kind === 'compare'">
          <div>
            <label for="f-cmp">Explanation <span class="muted">(optional)</span></label>
            <input id="f-cmp" v-model="selected.text" type="text" maxlength="1000">
          </div>
          <div>
            <label for="f-clang">Language <span class="muted">(optional)</span></label>
            <input id="f-clang" v-model="selected.data.language" type="text" maxlength="30">
          </div>
          <div>
            <label for="f-wrong">Wrong</label>
            <textarea id="f-wrong" v-model="selected.data.wrong" class="code-input" rows="4" maxlength="3000" spellcheck="false" />
          </div>
          <div>
            <label for="f-right">Right</label>
            <textarea id="f-right" v-model="selected.data.right" class="code-input" rows="4" maxlength="3000" spellcheck="false" />
          </div>
        </template>

        <p v-else-if="selected.kind === 'divider'" class="muted small">A divider has no settings.</p>
      </BuilderPanel>
    </template>

    <div class="bd-canvas" v-bind="canvasTarget">
      <p class="bd-status">
        <span>{{ elements.length }} {{ elements.length === 1 ? 'element' : 'elements' }}</span>
        <span>{{ words }} {{ words === 1 ? 'word' : 'words' }}</span>
        <span>about {{ readMinutes }} min read</span>
        <button v-if="checks" type="button" class="bd-status-link" :class="{ 'is-open': suggestions }" @click="panelTab = 'checks'">
          {{ suggestions ? `${suggestions} ${suggestions === 1 ? 'suggestion' : 'suggestions'}` : 'No suggestions' }}
        </button>
      </p>
      <BuilderNotice />

      <div v-if="!elements.length && !armed" class="bd-empty">
        <strong>A blank page</strong>
        Choose a tool to start. Nothing is required: build the guide you want.
        <span class="bd-empty-or">or</span>
        <button type="button" class="btn btn-secondary btn-small" @click="startFromTemplate">Start from the how-to template</button>
        <small>Goal, materials, steps with results, outcome and troubleshooting, as empty parts you fill in or delete.</small>
      </div>

      <template v-for="(el, i) in elements" :key="el.key">
        <BuilderGap :id="`g-${el.key}`" :accepts="gapAccepts" :place="armed ? `Place ${TOOL[tool].label.toLowerCase()} here` : undefined" @drop="dropAt(i)" @place="place(i)" />
        <BuilderCard
          :id="cardId(el.key)"
          :class="{ 'is-over': over === `e-${el.key}` }"
          :icon="TOOL[el.kind].icon"
          :label="label(el, i)"
          :number="el.kind === 'step' ? numbers[i]! : undefined"
          :summary="summary(el)"
          :placeholder="cardPlaceholder(el)"
          :selected="selKey === el.key"
          :child="!['section', 'step', 'heading', 'divider'].includes(el.kind)"
          :drag="{ what: 'element', key: el.key }"
          :remove-label="`Remove ${label(el, i).toLowerCase()}`"
          @select="select(el.key)"
          @remove="remove(i)"
        />
      </template>
      <BuilderGap v-if="elements.length || armed" id="g-end" :accepts="gapAccepts" :place="armed ? `Place ${TOOL[tool].label.toLowerCase()} here` : undefined" @drop="dropAt(elements.length)" @place="place(elements.length)" />
    </div>
  </BuilderShell>
</template>
