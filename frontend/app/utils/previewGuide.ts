import type { Category, Difficulty, ElementKind, Guide, GuideElement, GuideImage, GuideType, Step } from '~/types/guide'
import type { ElementDraft } from '~/utils/elements'
import { ELEMENT_PLACEHOLDERS, MARKDOWN_KINDS } from '~/utils/elements'
import { PLACEHOLDERS as P, PLACEHOLDER_IMAGE, ph, phHtml } from '~/utils/placeholders'

/**
 * Builds a Guide object from the editor state for the live preview, so the real reading
 * templates (GuideReader) can show it. `md` renders Markdown to sanitized HTML.
 * Nothing here is validated: the preview shows half-finished drafts as they are. An element
 * the author placed but has not filled yet shows its placeholder in grey (see
 * utils/placeholders.ts); an empty field of a filled element stays empty.
 */

export type RenderMarkdown = (text: string | null | undefined) => string

export interface CommonFields {
  title: string
  cover?: GuideImage | null
  language: string
  subtitle: string
  summary: string
  categoryId: number | null
  difficulty: Difficulty | ''
  duration: number | ''
}

/** The text, or its placeholder when empty */
const orPh = (text: string, placeholder: string) => text.trim() || ph(placeholder)

function baseGuide(type: GuideType, common: CommonFields, categories: Category[], saved?: Guide): Guide {
  const duration = common.duration === '' ? null : Number(common.duration)
  return {
    slug: saved?.slug ?? 'vorschau',
    guide_type: type,
    title: orPh(common.title, P.guideTitle),
    subtitle: common.subtitle.trim(),
    summary: common.summary.trim(),
    language: common.language || 'en',
    difficulty: common.difficulty,
    duration_minutes: duration && Number.isFinite(duration) && duration > 0 ? duration : null,
    category: categories.find((c) => c.id === common.categoryId) ?? null,
    steps: [],
    elements: [],
    images: [],
    cover_image: common.cover ?? null,
    attachment_info: null,
    is_locked: false,
    created_by: saved?.created_by ?? null,
    created_at: saved?.created_at ?? new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
}

const fence = (text: string, language: string) => {
  const longest = Math.max(0, ...(text.match(/`+/g) ?? []).map((run) => run.length))
  const ticks = '`'.repeat(Math.max(3, longest + 1))
  return `${ticks}${language}\n${text}\n${ticks}`
}

/** One element of the draft as the reading view shows it, with placeholders where it is empty */
function previewElement(el: ElementDraft, md: RenderMarkdown): GuideElement {
  const kind: ElementKind = el.kind
  const placeholder = ELEMENT_PLACEHOLDERS[kind]
  const data = structuredClone(toRaw(el.data))
  let text = el.text
  let html = ''
  const blank = !el.text.trim()

  if (MARKDOWN_KINDS.includes(kind)) {
    text = blank ? ph(placeholder) : text
    html = blank ? phHtml(placeholder) : md(text)
  } else if (kind === 'list') {
    const lines = el.text.split('\n').map((l) => l.trim()).filter(Boolean)
    text = lines.length ? el.text : ph(placeholder)
    html = lines.length ? md(lines.map((l) => `- ${l}`).join('\n')) : phHtml(placeholder)
  } else if (kind === 'checklist') {
    text = el.text.trim() ? el.text : ph(placeholder)
  } else if (kind === 'terminal' || kind === 'code') {
    const language = kind === 'terminal' ? 'console' : data.language || 'text'
    text = blank ? ph(placeholder) : el.text
    html = blank ? phHtml(placeholder) : md(fence(el.text, language))
  } else if (kind === 'collapsible') {
    text = orPh(el.text, placeholder)
    html = (data.body ?? '').trim() ? md(data.body) : phHtml('The text that opens')
  } else if (kind === 'compare') {
    const language = data.language || 'text'
    data.wrong_html = (data.wrong ?? '').trim() ? md(fence(data.wrong!, language)) : phHtml('The wrong example')
    data.right_html = (data.right ?? '').trim() ? md(fence(data.right!, language)) : phHtml('The right example')
  } else if (kind === 'diagram') {
    if (!(data.nodes ?? []).some((n) => n.trim())) data.nodes = [ph('First box'), ph('Second box')]
    else data.nodes = (data.nodes ?? []).filter((n) => n.trim())
  } else if (kind === 'table') {
    if (!(data.rows ?? []).some((row) => row.some((cell) => cell.trim()))) data.rows = [[ph('Column'), ph('Column')], [ph('Cell'), ph('Cell')]]
  } else if (kind === 'quote') {
    text = blank ? ph(placeholder) : el.text
  } else if (kind !== 'divider') {
    text = orPh(el.text, placeholder) // section, step, heading, link, download
  }
  const image = kind === 'image' ? el.image ?? PLACEHOLDER_IMAGE : null
  return { id: el.id, kind, text, data, html, image }
}

export function buildPreviewGuide(common: CommonFields, elements: ElementDraft[], categories: Category[], md: RenderMarkdown, saved?: Guide): Guide {
  const guide = baseGuide('page', common, categories, saved)
  guide.elements = elements.map((el) => previewElement(el, md))
  return guide
}

/** Preview of a free guide: rich-text steps (already split and converted to Markdown). */
export function buildFreePreviewGuide(
  common: Pick<CommonFields, 'title' | 'summary' | 'categoryId' | 'language' | 'cover'>,
  steps: { title: string; body: string }[],
  categories: Category[],
  md: RenderMarkdown,
  saved?: Guide,
): Guide {
  const guide = baseGuide('free', { ...common, subtitle: '', difficulty: '', duration: '' }, categories, saved)
  guide.steps = steps.map((step, i): Step => ({
    id: -(i + 1),
    order: i + 1,
    title: step.title,
    body: step.body,
    body_html: md(step.body),
  }))
  return guide
}
