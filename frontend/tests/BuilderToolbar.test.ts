// @vitest-environment happy-dom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import BuilderToolbar from '../app/components/BuilderToolbar.vue'

const mountBar = (props: Record<string, unknown> = {}) =>
  mount(BuilderToolbar, {
    props: { canUndo: false, canRedo: false, hasSelection: false, canUp: false, canDown: false, ...props },
    global: { stubs: { GuideIcon: true } },
  })
const button = (wrapper: ReturnType<typeof mountBar>, label: string) => wrapper.findAll('button').find((b) => b.text() === label)!
const LABELS = ['Undo', 'Redo', 'Duplicate', 'Up', 'Down', 'Delete']

describe('BuilderToolbar', () => {
  it('has the six edit buttons, each with a text and a shortcut in its title', () => {
    const buttons = mountBar().findAll('button')
    expect(buttons.map((b) => b.text())).toEqual(LABELS)
    expect(buttons[0]!.attributes('title')).toContain('Ctrl+Z')
  })

  it('disables what cannot be done now', () => {
    const wrapper = mountBar()
    for (const label of LABELS) expect(button(wrapper, label).attributes('disabled'), label).toBeDefined()
  })

  it('enables the buttons that fit the state', () => {
    const wrapper = mountBar({ canUndo: true, hasSelection: true, canDown: true })
    expect(button(wrapper, 'Undo').attributes('disabled')).toBeUndefined()
    expect(button(wrapper, 'Duplicate').attributes('disabled')).toBeUndefined()
    expect(button(wrapper, 'Down').attributes('disabled')).toBeUndefined()
    expect(button(wrapper, 'Redo').attributes('disabled')).toBeDefined()
    expect(button(wrapper, 'Up').attributes('disabled')).toBeDefined()
  })

  it('tells what a button does when it is pressed', async () => {
    const wrapper = mountBar({ canUndo: true, canRedo: true, hasSelection: true, canUp: true, canDown: true })
    for (const label of LABELS) await button(wrapper, label).trigger('click')
    expect(Object.keys(wrapper.emitted()).filter((name) => name !== 'click')).toEqual(['undo', 'redo', 'duplicate', 'up', 'down', 'remove'])
  })

  it('shows when the draft was saved', () => {
    expect(mountBar({ savedAt: '14:32' }).text()).toContain('Draft saved 14:32')
    expect(mountBar().text()).not.toContain('Draft saved')
  })
})
