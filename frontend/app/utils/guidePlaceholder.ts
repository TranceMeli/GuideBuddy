import type { IconName } from '~/components/GuideIcon.vue'
import type { GuideType } from '~/types/guide'

/**
 * Placeholder of a guide without a cover image: a line illustration for its category on
 * one of three tints. Without a category, the icon comes from a small set per guide type
 * and the tint varies, both picked from the slug, so neighbouring cards differ but a guide
 * always keeps its placeholder. The tints come from the design tokens only; coral is left
 * out because it is reserved for warnings.
 */
export type PlaceholderTint = 'blue' | 'teal' | 'slate'

const BY_CATEGORY: Record<string, { icon: IconName; tint: PlaceholderTint }> = {
  'cars-bikes': { icon: 'bike', tint: 'slate' },
  'computers-technology': { icon: 'monitor', tint: 'blue' },
  'cooking-baking': { icon: 'pot', tint: 'teal' },
  'diy-home-improvement': { icon: 'hammer', tint: 'slate' },
  garden: { icon: 'sprout', tint: 'teal' },
  health: { icon: 'heart', tint: 'blue' },
  household: { icon: 'home', tint: 'teal' },
  'leisure-hobbies': { icon: 'dice', tint: 'blue' },
  'money-paperwork': { icon: 'document', tint: 'slate' },
  'phones-apps': { icon: 'phone', tint: 'blue' },
  other: { icon: 'compass', tint: 'slate' },
}

const BY_TYPE: Record<GuideType, IconName[]> = {
  page: ['steps', 'check-circle', 'tip'],
  free: ['pen', 'document', 'tip', 'star', 'compass'],
}
const TINTS: PlaceholderTint[] = ['blue', 'teal', 'slate']

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
