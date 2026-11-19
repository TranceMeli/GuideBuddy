/**
 * A confirmation dialog that names the consequence, instead of the browser's confirm(). Use it
 * only for what cannot be undone: `if (!(await ask({ title, body, confirmLabel, danger: true }))) return`.
 * ConfirmDialog.vue (in the layout) shows it; the promise resolves with the answer.
 */
export interface ConfirmOptions {
  title: string
  body?: string
  confirmLabel?: string
  cancelLabel?: string
  danger?: boolean
}

// Only the browser asks and answers, so one pending question at a time is enough
let resolver: ((ok: boolean) => void) | null = null

export function useConfirm() {
  const state = useState<ConfirmOptions | null>('gb-confirm', () => null)
  return {
    state,
    ask(options: ConfirmOptions): Promise<boolean> {
      resolver?.(false)
      return new Promise((resolve) => {
        resolver = resolve
        state.value = options
      })
    },
    answer(ok: boolean) {
      state.value = null
      resolver?.(ok)
      resolver = null
    },
  }
}
