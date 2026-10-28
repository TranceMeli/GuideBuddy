/**
 * Base address of the API.
 * - On the server (rendering the page): the internal Django address directly.
 * - In the browser: "/api" - the Nuxt server, which forwards the request to Django and
 *   adds the login token from the HttpOnly cookie.
 */
export function useApiBase(): string {
  if (import.meta.server) {
    return String(useRuntimeConfig().apiBase).replace(/\/$/, '')
  }
  return '/api'
}

/** Address of the API as seen by the browser (e.g. for the PDF download link). */
export function usePublicApiBase(): string {
  return '/api'
}

const FIELD_LABELS: Record<string, string> = {
  username: 'User name',
  email: 'E-mail',
  password: 'Password',
  accept_terms: 'Consent',
  captcha_token: 'Captcha',
  title: 'Title',
  summary: 'Summary',
  steps: 'Steps',
  body: 'Content',
  change_comment: 'Change comment',
  reason: 'Reason',
  comment: 'Comment',
  note: 'Note',
  subtitle: 'Subtitle',
  intro: 'Introduction',
  category_id: 'Category',
  difficulty: 'Level',
  duration_minutes: 'Duration',
  prerequisites: 'Prerequisites',
  materials: 'Materials',
  learning_goals: 'Learning goals',
  conclusion: 'Conclusion',
  warning: 'Warning',
  tip: 'Tip',
  expected_result: 'Expected result',
  image_id: 'Image',
  mistake: 'Mistake',
  solution: 'Solution',
  symptom: 'Symptom',
  cause: 'Cause',
  code_language: 'Code language',
  code_wrong: 'Wrong code',
  code_right: 'Right code',
  key: 'Key',
  text: 'Text',
  help_text: 'Explanation',
  label: 'Answer',
  next_question_key: 'Next question',
  recommendation: 'Recommendation',
  recommended_guide: 'Recommended guide',
  block_type: 'Block type',
  content: 'Content',
  term: 'Term',
  definition: 'Definition',
  left_label: 'Left heading',
  right_label: 'Right heading',
  left: 'Left',
  right: 'Right',
  language: 'Language',
  code: 'Code',
  file: 'File',
  alt: 'Alt text',
  guide_type: 'Guide type',
}

/** Names of single list items, so nested errors say where they are ("Section 2 › Step 1") */
const ITEM_LABELS: Record<string, string> = {
  sections: 'Section',
  steps: 'Step',
  common_mistakes: 'Common mistake',
  entries: 'Problem',
  solution_steps: 'Solution step',
  questions: 'Question',
  options: 'Answer',
  blocks: 'Block',
  rows: 'Row',
  content: 'Row', // list blocks of a cheat sheet (terms, checklist)
  prerequisites: 'Prerequisite',
  materials: 'Material',
  learning_goals: 'Learning goal',
}

/** Turns a DRF error response into readable messages. */
export function apiErrorMessages(error: unknown): string[] {
  const err = error as { data?: unknown; statusCode?: number }
  const data = err?.data
  if (err?.statusCode === 429) return ['Too many attempts. Please wait a moment and try again.']
  if (data === undefined || data === null) return ['The server cannot be reached.']
  if (typeof data === 'string') return [data]
  const maybeNuxt = data as { statusMessage?: string; message?: string; detail?: unknown }
  if (maybeNuxt.statusMessage && !maybeNuxt.detail) return [maybeNuxt.statusMessage]

  const messages: string[] = []
  const join = (path: string, part: string) => (path ? `${path} › ${part}` : part)
  // field: the API name of the collection being walked, to number its items
  const walk = (value: unknown, label: string, field = '') => {
    if (typeof value === 'string') {
      messages.push(label ? `${label}: ${value}` : value)
    } else if (Array.isArray(value)) {
      value.forEach((item, index) => {
        // Errors of a nested list come as one object per item (empty for valid items)
        const numbered = item && typeof item === 'object' && !Array.isArray(item) && ITEM_LABELS[field]
        walk(item, numbered ? join(stripField(label, field), `${ITEM_LABELS[field]} ${index + 1}`) : label)
      })
    } else if (value && typeof value === 'object') {
      for (const [key, inner] of Object.entries(value)) {
        if (key === 'code' && typeof inner === 'string') continue
        if (key === 'non_field_errors' || key === 'detail') {
          walk(inner, label)
        } else if (/^\d+$/.test(key) && ITEM_LABELS[field]) {
          // Errors of a list of plain values: {"2": ["..."]}
          walk(inner, join(stripField(label, field), `${ITEM_LABELS[field]} ${Number(key) + 1}`))
        } else {
          walk(inner, join(label, FIELD_LABELS[key] ?? key), key)
        }
      }
    }
  }
  // "Section 1 › Steps › Step 2" reads better as "Section 1 › Step 2"
  const stripField = (label: string, field: string) => {
    const name = FIELD_LABELS[field] ?? field
    return label.endsWith(name) ? label.slice(0, -name.length).replace(/ › $/, '') : label
  }
  walk(data, '')
  return messages.length ? messages : ['An unknown error occurred.']
}

/** Error code from a Django response (e.g. "email_not_verified"). */
export function apiErrorCode(error: unknown): string {
  return String((error as { data?: { code?: string } })?.data?.code ?? '')
}
