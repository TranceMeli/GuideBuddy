import { Mark } from '@tiptap/core'
import { STYLE_OPTIONS, type StyleKind } from '~/utils/textStyles'

/**
 * TipTap marks for the text styles (see textStyles.ts): <span class="c-teal">, "h-yellow",
 * "f-serif". One mark per kind, so a text can have a colour, a highlight and a font at once.
 * The marks read their own class out of a span and leave the others alone.
 */
export const MARK_NAME: Record<StyleKind, string> = { color: 'textColor', highlight: 'textHighlight', font: 'textFont' }

function createStyleMark(kind: StyleKind) {
  const allowed = STYLE_OPTIONS[kind].map((o) => o.value)
  const own = (el: HTMLElement) => (el.getAttribute('class') ?? '').split(/\s+/).find((c) => allowed.includes(c)) ?? null
  return Mark.create({
    name: MARK_NAME[kind],
    addAttributes() {
      return {
        value: {
          default: null,
          parseHTML: (el) => own(el),
          renderHTML: (attrs) => (attrs.value ? { class: attrs.value } : {}),
        },
      }
    },
    parseHTML() {
      // consuming: false – a span with two styles ("f-hand c-coral") is read by both marks
      return [{ tag: 'span', consuming: false, getAttrs: (el) => (own(el as HTMLElement) ? null : false) }]
    },
    renderHTML({ HTMLAttributes }) {
      return ['span', HTMLAttributes, 0]
    },
  })
}

export const textStyleMarks = (['color', 'highlight', 'font'] as StyleKind[]).map(createStyleMark)
