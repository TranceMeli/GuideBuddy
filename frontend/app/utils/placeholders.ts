import type { GuideImage } from '~/types/guide'

/**
 * Placeholder texts of the building-block editors. One list feeds three places: the grey
 * hint in an empty field, the italic line on a card, and the live preview, where an empty
 * field shows its placeholder in grey (never saved, readers never see it).
 *
 * In the preview a placeholder travels inside ordinary text between two invisible marks
 * (U+2063, "invisible separator"). usePlaceholderHighlights() finds the marked ranges and
 * greys them with the CSS Custom Highlight API, without touching the page structure.
 */
export const PH_MARK = '⁣'
export const ph = (text: string) => `${PH_MARK}${text}${PH_MARK}`
export const phHtml = (text: string) => `<p>${ph(text)}</p>`

export const PLACEHOLDERS = {
  guideTitle: 'Title of your guide',
  imageCaption: 'Your image and its caption',
} as const

const svg = (body: string) =>
  `data:image/svg+xml;charset=utf-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 220">${body}</svg>`)}`

/** Stand-in for an image part that has no file yet, shown in the preview only */
export const PLACEHOLDER_IMAGE: GuideImage = {
  id: -9,
  width: 640,
  height: 220,
  alt: '',
  caption: ph(PLACEHOLDERS.imageCaption),
  kind: '',
  url: svg(
    '<rect width="640" height="220" fill="#f1f4f9"/><rect x="2" y="2" width="636" height="216" rx="12" fill="none" stroke="#9aa6c2" stroke-width="3" stroke-dasharray="10 8"/>' +
      '<text x="320" y="118" text-anchor="middle" fill="#6b7589" font-family="sans-serif" font-size="26">Image goes here</text>',
  ),
}
