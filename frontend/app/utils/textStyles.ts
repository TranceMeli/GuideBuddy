/**
 * Text styles authors can pick: a text colour, a highlight and a font. Content only carries
 * the class names below (never hex values or font names); the stylesheet decides how they
 * look (lighter variants in dark mode). The same list lives in
 * guides/templatetags/guide_extras.py (TEXT_STYLE_CLASSES), which strips everything else.
 */
export type StyleKind = 'color' | 'highlight' | 'font'
export interface StyleOption { value: string; label: string; swatch?: string }

export const STYLE_LABELS: Record<StyleKind, string> = { color: 'Colour', highlight: 'Highlight', font: 'Font' }
export const STYLE_PREFIX: Record<StyleKind, string> = { color: 'c-', highlight: 'h-', font: 'f-' }

/** swatch = the colour in the standard look, only for the picker */
export const STYLE_OPTIONS: Record<StyleKind, StyleOption[]> = {
  color: [
    { value: 'c-blue', label: 'Blue', swatch: '#2f4fd0' },
    { value: 'c-teal', label: 'Teal', swatch: '#0e7c74' },
    { value: 'c-coral', label: 'Coral', swatch: '#b93a26' },
    { value: 'c-violet', label: 'Violet', swatch: '#6b3fb5' },
    { value: 'c-gray', label: 'Gray', swatch: '#5b6478' },
  ],
  highlight: [
    { value: 'h-yellow', label: 'Yellow', swatch: '#fdf0b8' },
    { value: 'h-teal', label: 'Teal', swatch: '#d2f1ee' },
    { value: 'h-blue', label: 'Blue', swatch: '#dfe6fb' },
    { value: 'h-pink', label: 'Pink', swatch: '#fbdce3' },
  ],
  font: [
    { value: 'f-serif', label: 'Serif' },
    { value: 'f-hand', label: 'Handwriting' },
    { value: 'f-code', label: 'Code style' },
  ],
}

export const ALL_STYLE_CLASSES = Object.values(STYLE_OPTIONS).flatMap((list) => list.map((o) => o.value))
export const isStyleClass = (name: string) => ALL_STYLE_CLASSES.includes(name)

export const styleKindOf = (name: string): StyleKind | null =>
  (Object.keys(STYLE_PREFIX) as StyleKind[]).find((kind) => name.startsWith(STYLE_PREFIX[kind]) && isStyleClass(name)) ?? null

/** The classes of a class attribute that are text styles */
export const styleClassesOf = (classAttr: string | null | undefined) =>
  (classAttr ?? '').split(/\s+/).filter(isStyleClass)

/** Replaces the class of one kind in a list of classes (value null removes it) */
export function withStyle(classes: string[], kind: StyleKind, value: string | null): string[] {
  const rest = classes.filter((c) => styleKindOf(c) !== kind)
  return value ? [...rest, value] : rest
}
