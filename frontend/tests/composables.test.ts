import { beforeEach, describe, expect, it } from 'vitest'
import { useConfirm } from '../app/composables/useConfirm'
import { useToast } from '../app/composables/useToast'
import { resetState } from './setup'

beforeEach(resetState)

describe('useToast', () => {
  it('shows a message and hides it again', () => {
    const toast = useToast()
    expect(toast.current.value).toBeNull()
    toast.show('Guide published.')
    expect(toast.current.value?.text).toBe('Guide published.')
    toast.dismiss()
    expect(toast.current.value).toBeNull()
  })

  it('keeps an optional link', () => {
    const toast = useToast()
    toast.show('Saved.', { to: '/guides/x', label: 'View guide' })
    expect(toast.current.value?.link).toEqual({ to: '/guides/x', label: 'View guide' })
  })

  it('gives every message its own id, so the same text appears again', () => {
    const toast = useToast()
    toast.show('Saved.')
    const first = toast.current.value!.id
    toast.show('Saved.')
    expect(toast.current.value!.id).not.toBe(first)
  })

  it('shares the message between callers, so it survives a page change', () => {
    useToast().show('Deleted.')
    expect(useToast().current.value?.text).toBe('Deleted.')
  })
})

describe('useConfirm', () => {
  const options = { title: 'Delete the guide?', confirmLabel: 'Delete', danger: true }

  it('opens the question and resolves with the answer', async () => {
    const confirm = useConfirm()
    const pending = confirm.ask(options)
    expect(confirm.state.value?.title).toBe('Delete the guide?')
    confirm.answer(true)
    await expect(pending).resolves.toBe(true)
    expect(confirm.state.value).toBeNull()
  })

  it('resolves with false when cancelled', async () => {
    const confirm = useConfirm()
    const pending = confirm.ask(options)
    confirm.answer(false)
    await expect(pending).resolves.toBe(false)
  })

  it('cancels an open question when a new one is asked', async () => {
    const confirm = useConfirm()
    const first = confirm.ask(options)
    const second = confirm.ask({ title: 'Another question' })
    await expect(first).resolves.toBe(false)
    confirm.answer(true)
    await expect(second).resolves.toBe(true)
  })
})
