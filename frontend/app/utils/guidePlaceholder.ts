import type { IconName } from '~/components/GuideIcon.vue'
import type { GuideType } from '~/types/guide'

/**
 * Colour of a guide card and of its category chip, and the line illustration of a guide without
 * a cover image: one of six tints from the design tokens (--c-<tint>-fg, -bg and -ink). Without
 * a category, the icon comes from a small set per guide type and the tint varies, both picked
 * from the slug, so neighbouring cards differ but a guide always keeps its look.
 */
export type PlaceholderTint = 'blue' | 'teal' | 'coral' | 'amber' | 'violet' | 'slate'

const BY_CATEGORY: Record<string, { icon: IconName; tint: PlaceholderTint }> = {
  'cars-bikes': { icon: 'bike', tint: 'slate' },
  'computers-technology': { icon: 'monitor', tint: 'blue' },
  'cooking-baking': { icon: 'pot', tint: 'teal' },
  'diy-home-improvement': { icon: 'hammer', tint: 'amber' },
  garden: { icon: 'sprout', tint: 'teal' },
  health: { icon: 'heart', tint: 'coral' },
  household: { icon: 'home', tint: 'coral' },
  'leisure-hobbies': { icon: 'dice', tint: 'violet' },
  'money-paperwork': { icon: 'document', tint: 'amber' },
  'phones-apps': { icon: 'phone', tint: 'violet' },
  other: { icon: 'compass', tint: 'slate' },
}

const BY_TYPE: Record<GuideType, IconName[]> = {
  page: ['steps', 'check-circle', 'tip'],
  free: ['pen', 'document', 'tip', 'star', 'compass'],
}
const TINTS: PlaceholderTint[] = ['blue', 'teal', 'coral', 'amber', 'violet', 'slate']

/** Small stable string hash (djb2) */
function hash(text: string) {
  let h = 5381
  for (let i = 0; i < text.length; i++) h = ((h << 5) + h + text.charCodeAt(i)) >>> 0
  return h
}

export function placeholderFor(categorySlug: string | null | undefined, guideType: GuideType, slug = '') {
  const byCategory = categorySlug ? BY_CATEGORY[categorySlug] : undefined
  if (byCategory) return byCategory
  const icons = BY_TYPE[guideType] ?? BY_TYPE.free
  const h = hash(slug)
  return { icon: icons[h % icons.length]!, tint: TINTS[Math.floor(h / icons.length) % TINTS.length]! }
}
