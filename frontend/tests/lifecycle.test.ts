import { describe, expect, it } from 'vitest'
import { COMMENT_KINDS, COMMENT_REPORT_REASONS, GUIDE_REPORT_REASONS, STATUS, byLine, kindLabel, outdatedNote } from '../app/utils/lifecycle'

describe('status', () => {
  it('names every status in words', () => {
    expect(Object.keys(STATUS)).toEqual(['published', 'outdated', 'archived'])
    expect(Object.values(STATUS).every((s) => s.label.length > 3)).toBe(true)
  })
})

describe('comment kinds', () => {
  it('offers feedback, question, error and addition, each with a hint', () => {
    expect(COMMENT_KINDS.map((k) => k.label)).toEqual(['Feedback', 'Question', 'Error', 'Addition'])
    expect(COMMENT_KINDS.every((k) => k.hint.endsWith('.'))).toBe(true)
  })

  it('tags every kind except plain feedback', () => {
    expect(kindLabel('comment')).toBe('')
    expect(kindLabel('error')).toBe('Error')
    expect(kindLabel('addition')).toBe('Addition')
  })
})

describe('report reasons', () => {
  it('lets readers report a guide as outdated, but not a comment', () => {
    expect(GUIDE_REPORT_REASONS.map((r) => r.value)).toContain('outdated')
    expect(COMMENT_REPORT_REASONS.map((r) => r.value)).not.toContain('outdated')
  })

  it('has no reason twice and no empty label', () => {
    for (const list of [GUIDE_REPORT_REASONS, COMMENT_REPORT_REASONS]) {
      expect(new Set(list.map((r) => r.value)).size).toBe(list.length)
      expect(list.every((r) => r.label)).toBe(true)
    }
  })
})

describe('byLine', () => {
  it('names the author alone', () => expect(byLine('anna', [])).toBe('By anna'))
  it('counts contributors with the right plural', () => {
    expect(byLine('anna', ['tom'])).toBe('By anna and 1 contributor')
    expect(byLine('anna', ['tom', 'eva'])).toBe('By anna and 2 contributors')
  })
  it('copes with a deleted author', () => expect(byLine(null, [])).toBe('By a deleted account'))
})

describe('outdatedNote', () => {
  it('says nothing about a healthy guide', () => expect(outdatedNote('published', 0)).toBe(''))
  it('counts the readers who reported', () => {
    expect(outdatedNote('published', 1)).toContain('1 reader says')
    expect(outdatedNote('published', 3)).toContain('3 readers say')
  })
  it('explains a guide marked as outdated without reports', () => expect(outdatedNote('outdated', 0)).toContain('marked as outdated'))
  it('leaves archived guides to their own banner', () => expect(outdatedNote('archived', 4)).toBe(''))
})
