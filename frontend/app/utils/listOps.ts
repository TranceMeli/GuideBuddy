/** Small helpers for the editor lists (move an item, remove it). */
export function moveItem<T>(list: T[], index: number, delta: -1 | 1) {
  const target = index + delta
  if (target < 0 || target >= list.length) return
  const [item] = list.splice(index, 1)
  list.splice(target, 0, item!)
}

// Bookkeeping fields that do not count as content the author wrote
const META_FIELDS = new Set(['key', 'qkey', 'block_type', 'outcome'])

function hasText(value: unknown): boolean {
  if (typeof value === 'string') return value.trim() !== ''
  if (Array.isArray(value)) return value.some(hasText)
  if (value && typeof value === 'object') {
    return Object.entries(value).some(([name, inner]) => !META_FIELDS.has(name) && hasText(inner))
  }
  return false
}

/** Removes an item; asks first when the author already wrote something in it. */
export function removeItem<T>(list: T[], index: number, what = 'this entry') {
  if (hasText(list[index]) && !confirm(`Do you really want to remove ${what}?`)) return
  list.splice(index, 1)
}
