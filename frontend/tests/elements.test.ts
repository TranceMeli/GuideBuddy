import { describe, expect, it } from 'vitest'
import {
  ELEMENT_PLACEHOLDERS, MARKDOWN_KINDS, TOOL, TOOLS, howToTemplate, isBlank, newElement, numbering, payloadFromDraft,
} from '../app/utils/elements'
import type { ElementKind } from '../app/types/guide'

const KINDS = Object.keys(ELEMENT_PLACEHOLDERS) as ElementKind[]

describe('the tools of the builder', () => {
  it('has one tool for every kind of element, plus Select', () => {
    expect(TOOLS.map((t) => t.id).sort()).toEqual(['select', ...KINDS].sort())
  })

  it('gives every tool a unique shortcut', () => {
    const keys = TOOLS.map((t) => t.shortcut).filter(Boolean)
    expect(new Set(keys).size).toBe(keys.length)
  })

  it('explains every tool: what it does, how to use it, what readers see', () => {
    for (const tool of TOOLS) {
      expect(tool.what, tool.id).toBeTruthy()
      expect(tool.how, tool.id).toBeTruthy()
      expect(tool.readers, tool.id).toBeTruthy()
    }
  })

  it('offers the four notice levels', () => {
    for (const id of ['important', 'warning', 'danger', 'error', 'tip', 'note', 'result'] as const) {
      expect(TOOL[id].group, id).toBe('Notices')
      expect(MARKDOWN_KINDS).toContain(id)
    }
  })
})

describe('blank elements', () => {
  it('are not saved', () => {
    const { payload } = payloadFromDraft([newElement('text'), newElement('table'), newElement('image'), newElement('step')])
    expect(payload.elements).toEqual([])
  })

  it('keep a divider, which has no text', () => {
    expect(isBlank(newElement('divider'))).toBe(false)
  })

  it('count as written once there is text or a cell', () => {
    const table = newElement('table')
    table.data.rows![1]![1] = 'x'
    expect(isBlank(table)).toBe(false)
    expect(isBlank({ ...newElement('text'), text: '  ' })).toBe(true)
  })
})

describe('payloadFromDraft', () => {
  it('sends kind, text, data and the image id, and the id of an existing element', () => {
    const step = { ...newElement('step'), text: 'Open the page', id: 7 }
    const link = { ...newElement('link'), text: 'The downloads page', data: { url: 'https://python.org' } }
    const { payload, problems } = payloadFromDraft([step, link])
    expect(problems).toEqual([])
    expect(payload.elements).toEqual([
      { id: 7, kind: 'step', text: 'Open the page', data: {}, image_id: null },
      { kind: 'link', text: 'The downloads page', data: { url: 'https://python.org' }, image_id: null },
    ])
  })

  it('drops read-only html keys from the data', () => {
    const compare = { ...newElement('compare'), text: 'x', data: { wrong: 'a', right: 'b', language: '', wrong_html: '<p>a</p>', right_html: '<p>b</p>' } }
    const data = (payloadFromDraft([compare]).payload.elements as { data: Record<string, unknown> }[])[0]!.data
    expect(data).not.toHaveProperty('wrong_html')
    expect(data).not.toHaveProperty('right_html')
  })

  it('reports more than 300 elements', () => {
    const many = Array.from({ length: 301 }, () => ({ ...newElement('text'), text: 'x' }))
    expect(payloadFromDraft(many).problems).toHaveLength(1)
  })
})

describe('numbering', () => {
  it('counts sections and steps separately, as readers see them', () => {
    const kinds = ['section', 'step', 'text', 'step', 'section', 'step'].map((kind) => ({ kind })) as { kind: ElementKind }[]
    expect(numbering(kinds)).toEqual([1, 1, null, 2, 2, 3])
  })
})

describe('the how-to template', () => {
  const template = howToTemplate()

  it('follows the order of a good guide', () => {
    const kinds = template.map((e) => e.kind)
    expect(kinds[0]).toBe('text') // the goal first
    expect(kinds.indexOf('warning')).toBeLessThan(kinds.indexOf('step')) // safety before step 1
    expect(kinds.indexOf('checklist')).toBeLessThan(kinds.indexOf('step')) // materials before step 1
    expect(kinds.filter((k) => k === 'step').length).toBeGreaterThanOrEqual(2)
    expect(kinds.at(-1)).toBe('link') // related guides last
  })

  it('gives every part a hint', () => {
    expect(template.every((e) => e.hint)).toBe(true)
  })

  it('costs nothing when left unused: all parts are blank, so nothing is saved', () => {
    expect(payloadFromDraft(template).payload.elements).toEqual([])
  })

  it('saves its table once the author changes it', () => {
    const parts = howToTemplate()
    const table = parts.find((e) => e.kind === 'table')!
    table.data.rows![1] = ['“python” is not recognised', 'Run the installer again.']
    expect((payloadFromDraft(parts).payload.elements as unknown[]).length).toBe(1)
  })

  it('creates fresh elements with unique keys every time', () => {
    const keys = [...howToTemplate(), ...howToTemplate()].map((e) => e.key)
    expect(new Set(keys).size).toBe(keys.length)
  })
})
