/**
 * A short message that survives a page change ("Guide published"). The state lives in useState,
 * so a message set just before navigateTo() appears on the next page; AppToast.vue shows it and
 * hides it again after a few seconds.
 */
export interface ToastMessage {
  text: string
  /** Optional link, for example back to the guide */
  link?: { to: string; label: string }
  id: number
}

let counter = 0

export function useToast() {
  const current = useState<ToastMessage | null>('gb-toast', () => null)
  return {
    current,
    show: (text: string, link?: ToastMessage['link']) => {
      current.value = { text, link, id: ++counter }
    },
    dismiss: () => {
      current.value = null
    },
  }
}
