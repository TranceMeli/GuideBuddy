import type { Difficulty, GuideType, ImageKind } from '~/types/guide'

/** Labels and descriptions of the guide types (see docs/guide-types.md). */
/** Kinds of images, shown in the caption (same list as ImageKind in guides/models.py) */
export const IMAGE_KINDS: { value: Exclude<ImageKind, ''>; label: string }[] = [
  { value: 'photo', label: 'Photo' },
  { value: 'screenshot', label: 'Screenshot' },
  { value: 'mockup', label: 'Mockup (schematic)' },
  { value: 'diagram', label: 'Diagram' },
]

/** `sample`: slug of the sample guide of this type (python manage.py seed_samples) */
export const GUIDE_TYPES: { value: GuideType; label: string; icon: string; description: string; example: string; sample: string }[] = [
  {
    value: 'page',
    label: 'Guide',
    icon: '①',
    description: 'Built from elements: sections, steps, text, images, notices and more.',
    example: 'e.g. “Change a bike inner tube”',
    sample: 'install-python-on-windows',
  },
  {
    value: 'free',
    label: 'File or text',
    icon: '✎',
    description: 'Free text with headings as steps, or simply upload a file.',
    example: 'e.g. an existing PDF manual',
    sample: 'notes-you-can-find-again',
  },
]

export const guideTypeLabel = (type: GuideType) => GUIDE_TYPES.find((t) => t.value === type)?.label ?? type

export const DIFFICULTIES: { value: Difficulty; label: string; level: number }[] = [
  { value: 'beginner', label: 'Beginner', level: 1 },
  { value: 'intermediate', label: 'Intermediate', level: 2 },
  { value: 'advanced', label: 'Advanced', level: 3 },
]

export const difficultyOf = (value: string) => DIFFICULTIES.find((d) => d.value === value)

/**
 * Languages a guide can be written in (same list as GUIDE_LANGUAGES in guides/models.py).
 * English only for now, so the editors and the overview show no language choice.
 */
export const GUIDE_LANGUAGES: { value: string; label: string }[] = [
  { value: 'en', label: 'English' },
]

export const languageLabel = (value: string) => GUIDE_LANGUAGES.find((l) => l.value === value)?.label ?? value

/** "90" -> "1 h 30 min" */
export function formatDuration(minutes: number | null | undefined): string {
  if (!minutes) return ''
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  if (!hours) return `${rest} min`
  return rest ? `${hours} h ${rest} min` : `${hours} h`
}

/** Text lines of a textarea -> list items (empty lines dropped). */
export const linesToList = (text: string) =>
  text.split('\n').map((line) => line.trim()).filter(Boolean)

let uid = 0
/** Local key for v-for in the editors (also part of element ids); never sent to the API. */
export const localKey = () => `k${++uid}`
/**
 * Starts the keys again at k1. An editor calls this before it builds its draft, so the
 * server (whose counter runs on across requests) and the browser create the same keys
 * and the element ids built from them match when the page hydrates.
 */
export function resetLocalKeys() {
  uid = 0
}
