export interface Category {
  id: number
  name: string
  slug: string
}

export type GuideType = 'page' | 'free'
export type Difficulty = 'beginner' | 'intermediate' | 'advanced'

export interface GuideListItem {
  slug: string
  title: string
  subtitle: string
  summary: string
  /** Language of the content (BCP 47 tag, e.g. "en"), used as the lang attribute */
  language: string
  guide_type: GuideType
  difficulty: Difficulty | ''
  duration_minutes: number | null
  category: Category | null
  step_count: number
  has_pdf: boolean
  cover_image: GuideImage | null
  updated_at: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface Step {
  id: number
  order: number
  title: string
  body: string
  body_html: string
}

/** pdf/image: the browser shows the file; html: ready-made preview; none: download only */
export type AttachmentKind = 'pdf' | 'image' | 'html' | 'none'

export interface AttachmentInfo {
  name: string
  size: number
  download_url: string
  kind: AttachmentKind
  view_url: string | null
  preview_html: string
}

export type ImageKind = '' | 'photo' | 'screenshot' | 'mockup' | 'diagram'

export interface GuideImage {
  id: number
  url: string
  /** Caption and kind are shown under the image: a mockup is never passed off as a screenshot */
  caption: string
  kind: ImageKind
  alt: string
  width: number
  height: number
}

export type ElementKind =
  | 'section' | 'step' | 'heading' | 'divider'
  | 'text' | 'list' | 'checklist' | 'quote' | 'link' | 'table' | 'collapsible'
  | 'important' | 'error' | 'tip' | 'note' | 'result'
  | 'image' | 'diagram' | 'terminal' | 'code' | 'compare' | 'download'

/** What a kind needs besides its text (see guides/api/content.py); *_html is read only */
export interface ElementData {
  source?: string
  url?: string
  body?: string
  language?: string
  wrong?: string
  right?: string
  wrong_html?: string
  right_html?: string
  nodes?: string[]
  rows?: string[][]
}

/** One element of a guide, in the order of the guide */
export interface GuideElement {
  id?: number
  kind: ElementKind
  /** Main text: title of a section, step or heading, Markdown of a text or notice, ... */
  text: string
  data: ElementData
  /** Sanitized HTML of the main text where the kind has one (text, notices, list, terminal, code, collapsible body) */
  html: string
  image: GuideImage | null
}

/** Detail response (also returned by the preview endpoints) */
export interface Guide extends Omit<GuideListItem, 'step_count' | 'has_pdf'> {
  is_locked: boolean
  /** Steps of a free guide (guides built from elements use `elements`) */
  steps: Step[]
  elements: GuideElement[]
  images: GuideImage[]
  cover_image: GuideImage | null
  attachment_info: AttachmentInfo | null
  created_by: string | null
  created_at: string
}

export interface GuideComment {
  id: number
  author: string | null
  body: string
  body_html: string
  created_at: string
  edited_at: string | null
  can_edit: boolean
  kind: 'comment' | 'question'
  /** The element the comment is about (null: the whole guide, or the element was removed) */
  element: number | null
  /** Name of that element, kept even if it is removed later */
  anchor: string
  /** The comment this one replies to (replies are one level deep) */
  parent: number | null
  /** A reply to a question that answered it */
  is_answer: boolean
  by_guide_author: boolean
  helpful_count: number
  /** The signed-in viewer marked it helpful */
  helpful: boolean
  can_mark_answer: boolean
}

export interface HistoryEntry {
  date: string
  user: string | null
  type: 'created' | 'changed' | 'deleted'
  title: string
  reason?: string
  attachment?: string | null
  order?: number
}

export interface GuideHistory {
  guide: HistoryEntry[]
  steps: HistoryEntry[]
}

export interface AuthUser {
  username: string
  email: string
  is_moderator: boolean
  can_write: boolean
  write_hint: string
}

export interface Report {
  id: number
  guide: string
  guide_title: string
  guide_locked: boolean
  reported_comment: number | null
  reported_comment_body: string | null
  reporter: string | null
  reason: string
  reason_label: string
  comment: string
  created_at: string
  resolved_at: string | null
  resolved_by: string | null
  resolution_note: string
}
