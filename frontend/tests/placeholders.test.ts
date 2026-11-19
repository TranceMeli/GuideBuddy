import { describe, expect, it } from 'vitest'
import { placeholderFor } from '../app/utils/guidePlaceholder'
import { moveItem } from '../app/utils/listOps'

describe('placeholderFor', () => {
  it('gives each category its own colour and icon', () => {
    expect(placeholderFor('computers-technology', 'page')).toEqual({ icon: 'monitor', tint: 'blue' })
    expect(placeholderFor('cooking-baking', 'page')).toEqual({ icon: 'pot', tint: 'teal' })
    expect(placeholderFor('household', 'page')).toEqual({ icon: 'home', tint: 'coral' })
  })

  it('keeps the look of a guide without a category stable', () => {
    expect(placeholderFor(null, 'page', 'my-guide')).toEqual(placeholderFor(null, 'page', 'my-guide'))
  })

  it('lets neighbouring guides differ', () => {
    const looks = new Set(['a', 'b', 'c', 'd', 'e', 'f'].map((slug) => JSON.stringify(placeholderFor(undefined, 'page', slug))))
    expect(looks.size).toBeGreaterThan(1)
  })

  it('only uses the six tints', () => {
    const tints = new Set(['blue', 'teal', 'coral', 'amber', 'violet', 'slate'])
    for (const slug of ['x', 'y', 'z', 'guide-1', 'guide-2']) {
      expect(tints.has(placeholderFor(undefined, 'free', slug).tint)).toBe(true)
    }
  })
})

describe('moveItem', () => {
  it('moves an item up or down', () => {
    const list = ['a', 'b', 'c']
    moveItem(list, 1, -1)
    expect(list).toEqual(['b', 'a', 'c'])
    moveItem(list, 1, 1)
    expect(list).toEqual(['b', 'c', 'a'])
  })

  it('stays put at the ends', () => {
    const list = ['a', 'b']
    moveItem(list, 0, -1)
    moveItem(list, 1, 1)
    expect(list).toEqual(['a', 'b'])
  })
})
