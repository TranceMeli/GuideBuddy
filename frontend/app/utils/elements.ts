import type { ElementData, ElementKind, Guide, GuideElement, GuideImage } from '~/types/guide'
import type { IconName } from '~/components/GuideIcon.vue'

/**
 * The elements a guide is built from, and the tools of the guide builder that place them.
 * A guide is an ordered list of elements; nothing is required (see docs/guide-types.md).
 */

export type ToolId = 'select' | ElementKind

export interface ToolInfo {
  id: ToolId
  label: string
  icon: IconName
  group: string
  shortcut: string
  /** One sentence: what the tool does */
  what: string
  /** How to use it */
  how: string
  /** What readers see */
  readers: string
}

export const TOOLS: ToolInfo[] = [
  { id: 'select', label: 'Select', icon: 'pointer', group: 'Select', shortcut: 'V',
    what: 'Chooses an element so you can edit it.', how: 'Click an element in the guide. Its properties open on the right.', readers: 'Nothing, it only selects.' },
  { id: 'section', label: 'Section', icon: 'menu', group: 'Structure', shortcut: 'A',
    what: 'Starts a new chapter with a title.', how: 'Choose the tool, then click “Place here” where the chapter starts.', readers: 'A small label (Section 2) and a heading with a thin line. It also appears in the contents.' },
  { id: 'step', label: 'Step', icon: 'steps', group: 'Structure', shortcut: 'S',
    what: 'One action readers do. Steps are numbered automatically.', how: 'Choose the tool, place it, type the title on the right. Add text, images and notices below it.', readers: 'A numbered badge with the title. Readers can tick a step off.' },
  { id: 'heading', label: 'Heading', icon: 'heading', group: 'Structure', shortcut: 'H',
    what: 'A smaller heading inside a section, without a number.', how: 'Place it and type the heading.', readers: 'A bold line that divides the text.' },
  { id: 'divider', label: 'Divider', icon: 'minus', group: 'Structure', shortcut: 'X',
    what: 'A thin line that separates two parts.', how: 'Place it. It has no settings.', readers: 'A horizontal line.' },
  { id: 'text', label: 'Text', icon: 'document', group: 'Text', shortcut: 'T',
    what: 'A paragraph of text.', how: 'Place it, then write in the text field on the right. Bold, links, lists and colours are in the toolbar.', readers: 'A paragraph in the reading font.' },
  { id: 'list', label: 'List', icon: 'bullets', group: 'Text', shortcut: 'L',
    what: 'A bulleted list. One line is one item.', how: 'Place it, then write one item per line.', readers: 'A bulleted list.' },
  { id: 'checklist', label: 'Checklist', icon: 'list', group: 'Text', shortcut: 'K',
    what: 'Items readers can tick off, for example “Before you start”.', how: 'Place it, then write one item per line.', readers: 'A list with checkboxes.' },
  { id: 'quote', label: 'Quote', icon: 'quote', group: 'Text', shortcut: 'Q',
    what: 'A quotation or a remark, with its source.', how: 'Place it, write the quote and, if you like, the source.', readers: 'An indented quote with the source below.' },
  { id: 'link', label: 'Link', icon: 'link', group: 'Text', shortcut: 'U',
    what: 'A link with words that say where it leads.', how: 'Place it, then write the link text and the address.', readers: 'A link on its own line.' },
  { id: 'table', label: 'Table', icon: 'table', group: 'Text', shortcut: 'B',
    what: 'A table. The first row is the heading.', how: 'Place it, then fill the cells and add rows or columns.', readers: 'A table that becomes cards on a phone.' },
  { id: 'collapsible', label: 'Collapsible', icon: 'chevron-down', group: 'Text', shortcut: 'O',
    what: 'A question or title that opens to show more.', how: 'Place it, then write the title and the text that opens.', readers: 'A line readers can open and close.' },
  { id: 'important', label: 'Important', icon: 'alert', group: 'Notices', shortcut: 'W',
    what: 'Draws attention to something that matters.', how: 'Place it near the step it belongs to and write one or two sentences.', readers: 'A yellow box labelled Important, with an icon.' },
  { id: 'warning', label: 'Warning', icon: 'alert', group: 'Notices', shortcut: 'Y',
    what: 'A risk of injury or damage. Put it before the step it belongs to, or at the start of the guide.', how: 'Place it, say what can happen and how to avoid it.', readers: 'A coral box labelled Warning, with an icon.' },
  { id: 'danger', label: 'Danger', icon: 'stop', group: 'Notices', shortcut: 'D',
    what: 'An immediate threat to life or health. Use it rarely.', how: 'Place it at the start of the guide or right before the step.', readers: 'A dark red box labelled Danger, with an icon.' },
  { id: 'error', label: 'Error', icon: 'close', group: 'Notices', shortcut: 'E',
    what: 'Shows an error readers may meet, and how to avoid it.', how: 'Place it, write the message first, then the fix.', readers: 'A red box labelled Error, with an icon.' },
  { id: 'tip', label: 'Tip', icon: 'tip', group: 'Notices', shortcut: 'P',
    what: 'A faster or easier way to do something.', how: 'Place it and keep it short.', readers: 'A blue box labelled Tip.' },
  { id: 'note', label: 'Note', icon: 'info', group: 'Notices', shortcut: 'N',
    what: 'Good to know, but not required.', how: 'Place it and write the remark.', readers: 'A blue box labelled Note.' },
  { id: 'result', label: 'Expected result', icon: 'check-circle', group: 'Notices', shortcut: 'R',
    what: 'Tells readers what they should see when a step worked.', how: 'Place it right after the step.', readers: 'A green box labelled Expected result.' },
  { id: 'image', label: 'Image', icon: 'photo', group: 'Media', shortcut: 'I',
    what: 'A screenshot, mockup, diagram or photo, with a description.', how: 'Place it, upload the file on the right, say what kind of image it is and describe it.', readers: 'The picture with a numbered caption (Figure 1).' },
  { id: 'diagram', label: 'Diagram', icon: 'diagram', group: 'Media', shortcut: 'G',
    what: 'Boxes connected by arrows, for an order of things.', how: 'Place it and type one box per line.', readers: 'Boxes with arrows between them.' },
  { id: 'terminal', label: 'Terminal', icon: 'terminal', group: 'Media', shortcut: 'C',
    what: 'Commands and what the computer answers.', how: 'Place it and paste the lines. Start a command with “$ ”. Lines with an error turn red, successes green.', readers: 'A dark block, one line per command or answer.' },
  { id: 'code', label: 'Code', icon: 'code', group: 'Media', shortcut: 'F',
    what: 'The content of a file, with colours for the language.', how: 'Place it, type the language (for example python) and paste the code.', readers: 'A code block with a language label.' },
  { id: 'compare', label: 'Wrong and right', icon: 'compare', group: 'Media', shortcut: 'M',
    what: 'Two examples side by side: what goes wrong and how it is done right.', how: 'Place it, then fill both examples. A short explanation is optional.', readers: 'Two blocks marked Wrong and Right.' },
  { id: 'download', label: 'Download', icon: 'download', group: 'Media', shortcut: 'J',
    what: 'A button that leads to a file readers can download.', how: 'Place it, then write the label and the address of the file.', readers: 'A button with a download icon.' },
]

export const TOOL: Record<ToolId, ToolInfo> = Object.fromEntries(TOOLS.map((t) => [t.id, t])) as Record<ToolId, ToolInfo>
export const TOOL_GROUPS = [...new Set(TOOLS.map((t) => t.group))]

/** Kinds whose main text is Markdown (with the formatting bar) */
export const MARKDOWN_KINDS: ElementKind[] = ['text', 'important', 'warning', 'danger', 'error', 'tip', 'note', 'result', 'quote']

/** Placeholder of an empty element: card line, field hint and grey text in the live preview */
export const ELEMENT_PLACEHOLDERS: Record<ElementKind, string> = {
  section: 'Section title, e.g. Preparation',
  step: 'Step title as an instruction, e.g. Remove the wheel',
  heading: 'Heading',
  divider: '',
  text: 'Write your text here',
  list: 'One item per line',
  checklist: 'One item per line',
  quote: 'The quote',
  link: 'Link text that says where it leads',
  table: 'Table',
  collapsible: 'Question or title',
  important: 'What matters here, and what to watch out for',
  warning: 'What can go wrong (injury or damage), and how to avoid it',
  danger: 'What can cause serious harm, and what to do instead',
  error: 'The error readers will see, and how to get rid of it',
  tip: 'A faster or easier way to do it',
  note: 'Good to know, but not required',
  result: 'What it looks like when the step worked',
  image: 'Your image and its caption',
  diagram: 'One box per line',
  terminal: '$ command',
  code: 'Paste the code',
  compare: 'Wrong and right examples',
  download: 'Label of the download button',
}

// --- Drafts -------------------------------------------------------------------------

export interface ElementDraft {
  key: string
  id?: number
  kind: ElementKind
  text: string
  data: ElementData
  image: GuideImage | null
  /** Template guidance shown instead of the generic placeholder; never saved */
  hint?: string
}

export const MAX_ELEMENTS = 300

function defaultData(kind: ElementKind): ElementData {
  switch (kind) {
    case 'quote': return { source: '' }
    case 'link':
    case 'download': return { url: '' }
    case 'collapsible': return { body: '' }
    case 'code': return { language: '' }
    case 'compare': return { wrong: '', right: '', language: '' }
    case 'diagram': return { nodes: ['', ''] }
    case 'table': return { rows: [['', ''], ['', '']] }
    default: return {}
  }
}

export const newElement = (kind: ElementKind): ElementDraft => ({ key: localKey(), kind, text: '', data: defaultData(kind), image: null })

/**
 * Starting point "How-to guide": the parts of a good guide, in order, as empty elements with
 * a hint each. Empty elements are not saved, so what stays unused costs nothing. The parts come
 * from the guide-writing research (goal, materials, warning first, steps with results, outcome,
 * troubleshooting, related guides).
 */
const HOW_TO: [ElementKind, string, ElementData?][] = [
  ['text', 'Goal: what will readers have achieved at the end, and who is this guide for?'],
  ['warning', 'Safety first (optional): what can go wrong before step 1, and how to avoid it'],
  ['section', 'What you need'],
  ['checklist', 'Materials and tools with quantities, one per line'],
  ['section', 'Part 1: name the first phase of the task'],
  ['step', 'One action, starting with a verb'],
  ['text', 'Where to do it and how, with exact values (time, temperature, size)'],
  ['result', 'What readers should see now'],
  ['step', 'The next action'],
  ['text', 'Explain it in short sentences'],
  ['result', 'What readers should see now'],
  ['section', 'Outcome'],
  ['result', 'What the finished result looks like, and how readers check that it worked'],
  ['section', 'If something goes wrong'],
  ['table', 'Symptom and solution', { rows: [['If you see …', 'Then …'], ['', '']] }],
  ['section', 'Related guides'],
  ['link', 'Title of a related guide'],
]

export function howToTemplate(): ElementDraft[] {
  return HOW_TO.map(([kind, hint, data]) => ({ ...newElement(kind), hint, data: { ...defaultData(kind), ...data } }))
}

/** Data as the API wants it: no read-only *_html keys */
function plainData(data: ElementData): ElementData {
  const copy = structuredClone(toRaw(data)) as ElementData
  delete copy.wrong_html
  delete copy.right_html
  return copy
}

export function draftFromGuide(guide?: Guide): ElementDraft[] {
  return (guide?.elements ?? []).map((el: GuideElement) => ({
    key: localKey(), id: el.id, kind: el.kind, text: el.text, data: { ...defaultData(el.kind), ...plainData(el.data) }, image: el.image,
  }))
}

/** An element nobody wrote anything into is not saved */
export function isBlank(el: ElementDraft): boolean {
  if (el.kind === 'divider') return false
  const d = el.data
  if (el.kind === 'image') return !el.image
  if (el.kind === 'table') return !(d.rows ?? []).some((row) => row.some((cell) => cell.trim()))
  if (el.kind === 'diagram') return !(d.nodes ?? []).some((n) => n.trim())
  if (el.kind === 'compare') return !el.text.trim() && !d.wrong?.trim() && !d.right?.trim()
  if (el.kind === 'collapsible') return !el.text.trim() && !d.body?.trim()
  if (el.kind === 'link' || el.kind === 'download') return !el.text.trim() && !d.url?.trim()
  return !el.text.trim()
}

export function payloadFromDraft(elements: ElementDraft[]): { payload: Record<string, unknown>; problems: string[] } {
  const problems: string[] = []
  const kept = elements.filter((el) => !isBlank(el))
  if (kept.length > MAX_ELEMENTS) problems.push(`A guide has at most ${MAX_ELEMENTS} elements.`)
  return {
    problems,
    payload: {
      elements: kept.map((el) => ({
        ...(el.id !== undefined ? { id: el.id } : {}),
        kind: el.kind,
        text: el.text,
        data: plainData(el.data),
        image_id: el.kind === 'image' ? el.image?.id ?? null : null,
      })),
    },
  }
}

/** Numbers of sections and steps as the reader sees them */
export function numbering(elements: { kind: ElementKind }[]): (number | null)[] {
  let section = 0
  let step = 0
  return elements.map((el) => (el.kind === 'section' ? ++section : el.kind === 'step' ? ++step : null))
}
