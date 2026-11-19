/** Moves an item of an editor list one place up or down. */
export function moveItem<T>(list: T[], index: number, delta: -1 | 1) {
  const target = index + delta
  if (target < 0 || target >= list.length) return
  const [item] = list.splice(index, 1)
  list.splice(target, 0, item!)
}
