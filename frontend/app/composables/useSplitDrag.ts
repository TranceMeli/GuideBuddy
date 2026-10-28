/**
 * Draggable divider between two columns: mouse, touch or arrow keys; double-click resets.
 * `split` is the width of the first column in percent. The chosen value is remembered per
 * browser under `storageKey` (a convenience only, so failures are ignored).
 */
export function useSplitDrag(options: { storageKey: string; min: number; max: number; initial: number }) {
  const { storageKey, min, max, initial } = options
  const split = ref(initial)
  const dragging = ref(false)
  const root = ref<HTMLElement | null>(null)

  const clamp = (value: number) => Math.min(max, Math.max(min, Math.round(value)))

  onMounted(() => {
    try {
      const saved = Number(localStorage.getItem(storageKey))
      if (saved) split.value = clamp(saved)
    } catch {
      // storage blocked (private mode): keep the default
    }
  })

  function remember() {
    try {
      localStorage.setItem(storageKey, String(split.value))
    } catch {
      // not important enough to report
    }
  }

  function moveTo(clientX: number) {
    const rect = root.value?.getBoundingClientRect()
    if (!rect || !rect.width) return
    split.value = clamp(((clientX - rect.left) / rect.width) * 100)
  }

  function onPointerDown(event: PointerEvent) {
    if (event.button !== 0) return
    event.preventDefault()
    ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
    dragging.value = true
  }
  function onPointerMove(event: PointerEvent) {
    if (dragging.value) moveTo(event.clientX)
  }
  function onPointerUp(event: PointerEvent) {
    if (!dragging.value) return
    dragging.value = false
    ;(event.currentTarget as HTMLElement).releasePointerCapture(event.pointerId)
    remember()
  }

  function onKey(event: KeyboardEvent) {
    const steps: Record<string, number> = { ArrowLeft: -2, ArrowRight: 2, PageDown: -10, PageUp: 10 }
    if (event.key in steps) split.value = clamp(split.value + steps[event.key]!)
    else if (event.key === 'Home') split.value = min
    else if (event.key === 'End') split.value = max
    else return
    event.preventDefault()
    remember()
  }

  function reset() {
    split.value = initial
    remember()
  }

  /** Attributes and listeners for the handle element (role="separator"). */
  const handleProps = computed(() => ({
    role: 'separator',
    tabindex: 0,
    'aria-orientation': 'vertical' as const,
    'aria-valuemin': min,
    'aria-valuemax': max,
    'aria-valuenow': split.value,
    title: 'Drag to resize · double-click to reset',
    onPointerdown: onPointerDown,
    onPointermove: onPointerMove,
    onPointerup: onPointerUp,
    onPointercancel: onPointerUp,
    onKeydown: onKey,
    onDblclick: reset,
  }))

  return { split, dragging, root, handleProps }
}
