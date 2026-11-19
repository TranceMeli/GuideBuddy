import { describe, expect, it } from 'vitest'
import { newElement, type ElementDraft } from '../app/utils/elements'
import { publishChecks } from '../app/utils/publishChecks'
import type { ElementKind } from '../app/types/guide'

const el = (kind: ElementKind, text = '', extra: Partial<ElementDraft> = {}): ElementDraft => ({ ...newElement(kind), text, ...extra })
const failed = (title: string, elements: ElementDraft[], summary = '') =>
  publishChecks({ title, summary }, elements).filter((c) => !c.ok).map((c) => c.id)

// A guide that follows every rule of the writing check
const good = (): ElementDraft[] => [
  el('text', 'You will install Python on Windows.'),
  el('section', 'Download the installer'),
  el('step', 'Open the download page'),
  el('text', 'Click the blue button.'),
  el('result', 'A file appears in your Downloads folder.'),
  el('step', 'Start the installer'),
  el('result', 'A progress bar appears.'),
  el('section', 'Outcome'),
  el('result', 'Python answers with its version number.'),
]

describe('publishChecks', () => {
  it('has ten checks with a hint each', () => {
    const checks = publishChecks({ title: 'How to install Python' }, good())
    expect(checks).toHaveLength(10)
    expect(checks.every((c) => c.label && c.hint)).toBe(true)
  })

  it('passes a guide that follows the rules', () => {
    expect(failed('How to install Python', good())).toEqual([])
  })

  it('passes an empty guide: nothing is required', () => {
    expect(failed('', [])).toEqual([])
  })

  it('asks for a title that says what readers do', () => {
    expect(failed('About Python', good())).toContain('title')
    expect(failed('Install Python', good())).not.toContain('title')
  })

  it('asks for an introduction before the first step, or a summary', () => {
    const noIntro = good().slice(1)
    expect(failed('Install Python', noIntro)).toContain('goal')
    expect(failed('Install Python', noIntro, 'Install Python on Windows.')).not.toContain('goal')
  })

  it('flags generic headings', () => {
    const elements = good()
    elements[1] = el('section', 'Introduction')
    expect(failed('Install Python', elements)).toContain('headings')
  })

  it('flags steps with nothing after the title', () => {
    const elements = [...good(), el('step', 'A step without content')]
    expect(failed('Install Python', elements)).toContain('steps')
  })

  it('wants an expected result for most steps', () => {
    const elements = [el('text', 'Intro'), el('step', 'One'), el('text', 'x'), el('step', 'Two'), el('text', 'y'), el('step', 'Three'), el('text', 'z'), el('result', 'Done')]
    const result = publishChecks({ title: 'Install Python' }, elements).find((c) => c.id === 'step-results')!
    expect(result.ok).toBe(false)
    expect(result.hint).toContain('1 of 3')
  })

  it('flags a step that names two actions, but not a list of things', () => {
    const two = [...good(), el('step', 'Add the salt and fold'), el('text', 'x')]
    expect(failed('Install Python', two)).toContain('one-action')
    const list = good().map((e) => (e.kind === 'step' ? { ...e, text: 'Mix flour and water' } : e))
    expect(failed('Install Python', list)).not.toContain('one-action')
  })

  it('wants a final result after the last step', () => {
    const elements = good().slice(0, 6) // the last step has no expected result after it
    expect(failed('Install Python', elements)).toContain('outcome')
  })

  it('flags images without a caption', () => {
    const image = el('image', '', { image: { id: 1, url: '/x.png', alt: 'x', caption: '', kind: '', width: 1, height: 1 } })
    expect(failed('Install Python', [...good(), image])).toContain('captions')
    const captioned = { ...image, image: { ...image.image!, caption: 'The installer window' } }
    expect(failed('Install Python', [...good(), captioned])).not.toContain('captions')
  })

  it('flags links without meaningful text', () => {
    expect(failed('Install Python', [...good(), el('link', 'click here', { data: { url: 'https://python.org' } })])).toContain('links')
    expect(failed('Install Python', [...good(), el('text', 'See [here](https://python.org).')])).toContain('links')
  })
})
