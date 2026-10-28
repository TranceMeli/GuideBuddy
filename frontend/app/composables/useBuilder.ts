import type { InjectionKey, Ref } from 'vue'
import type { IconName } from '~/components/GuideIcon.vue'

/**
 * Shared state of a building-block editor (one per editor): what is being dragged, which
 * drop target is under the pointer, the short notice line (with "Undo" after a removal),
 * and the palette sheet on narrow panes. The editor calls useBuilder(); BuilderPalette,
 * BuilderGap and BuilderNotice inside it read the same state with useBuilderContext().
 */
export interface BuilderPart { id: string; label: string; icon: IconName; hint: string; shortcut?: string }
export interface BuilderGroup { group: string; parts: BuilderPart[] }
/** A new part from the palette, or an item of the guide being moved */
export type BuilderDrag = { kind: 'new'; part: string } | { kind: 'move'; what: string; key: string }

export interface BuilderState {
  drag: Ref<BuilderDrag | null>
  over: Ref<string>
  notice: Ref<string>
  /** Puts back what was just removed; null when there is nothing to undo */
  undoAction: Ref<(() => void) | null>
  sheetOpen: Ref<boolean>
  startDrag: (event: DragEvent, value: BuilderDrag, image?: Element | null) => void
  endDrag: () => void
  say: (message: string) => void
  /** Reports a removal and offers "Undo" for a few seconds (instead of asking first) */
  removed: (message: string, restore: () => void) => void
  undo: () => void
  /** Removes list[index] with "Undo"; returns the removed item */
  removeFromList: <T>(list: T[], index: number, label: string) => T | undefined
  reveal: (id: string, focusSelector?: string) => Promise<void>
  /** The part being dragged from the palette, if any */
  newPart: Ref<string | null>
  /** The item being moved, if it is of this kind */
  moving: (what: string) => string | null
  /** Listeners (for v-bind="…") that make an element a drop target with the given id */
  dropTarget: (id: string, accepts: () => boolean, onDrop: () => void) => Record<string, (event: DragEvent) => void>
}

const KEY: InjectionKey<BuilderState> = Symbol('builder')

export function useBuilder(): BuilderState {
  const drag = ref<BuilderDrag | null>(null)
  const over = ref('')
  const notice = ref('')
  const undoAction = ref<(() => void) | null>(null)
  const sheetOpen = ref(false)
  let timer: ReturnType<typeof setTimeout> | undefined

  function startDrag(event: DragEvent, value: BuilderDrag, image?: Element | null) {
    drag.value = value
    const transfer = event.dataTransfer
    if (!transfer) return
    transfer.setData('text/plain', value.kind === 'new' ? value.part : value.key)
    transfer.effectAllowed = value.kind === 'new' ? 'copy' : 'move'
    if (image) transfer.setDragImage(image, 20, 20)
  }
  function endDrag() {
    drag.value = null
    over.value = ''
  }
  function say(message: string, restore: (() => void) | null = null, ms = 4000) {
    notice.value = message
    undoAction.value = restore
    clearTimeout(timer)
    timer = setTimeout(() => {
      notice.value = ''
      undoAction.value = null
    }, ms)
  }
  function removed(message: string, restore: () => void) {
    say(message, restore, 8000)
  }
  function undo() {
    const restore = undoAction.value
    if (!restore) return
    restore()
    say('Restored.')
  }
  function removeFromList<T>(list: T[], index: number, label: string): T | undefined {
    const [item] = list.splice(index, 1)
    if (item !== undefined) removed(`${label} removed.`, () => list.splice(Math.min(index, list.length), 0, item))
    return item
  }
  async function reveal(id: string, focusSelector?: string) {
    await nextTick()
    const el = document.getElementById(id)
    el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    if (focusSelector) el?.querySelector<HTMLElement>(focusSelector)?.focus({ preventScroll: true })
  }
  const newPart = computed(() => (drag.value?.kind === 'new' ? drag.value.part : null))
  const moving = (what: string) => (drag.value?.kind === 'move' && drag.value.what === what ? drag.value.key : null)

  function dropTarget(id: string, accepts: () => boolean, onDrop: () => void) {
    return {
      onDragover(event: DragEvent) {
        if (!drag.value || !accepts()) return
        event.preventDefault()
        event.stopPropagation()
        over.value = id
      },
      onDragleave() {
        if (over.value === id) over.value = ''
      },
      onDrop(event: DragEvent) {
        if (!drag.value || !accepts()) return
        event.preventDefault()
        event.stopPropagation()
        onDrop()
        endDrag()
      },
    }
  }

  const state: BuilderState = {
    drag, over, notice, undoAction, sheetOpen, startDrag, endDrag, say: (message: string) => say(message), removed, undo, removeFromList,
    reveal, newPart, moving, dropTarget,
  }
  provide(KEY, state)
  return state
}

export function useBuilderContext(): BuilderState {
  const state = inject(KEY)
  if (!state) throw new Error('useBuilderContext() needs a parent that called useBuilder()')
  return state
}

/** Moves an item to `at` within the same list (at = index before which it lands) */
export function moveWithin<T>(list: T[], from: number, at: number) {
  const [item] = list.splice(from, 1)
  list.splice(from < at ? at - 1 : at, 0, item!)
}
