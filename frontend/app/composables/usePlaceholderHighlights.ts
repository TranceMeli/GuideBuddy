import type { Ref } from 'vue'
import { PH_MARK } from '~/utils/placeholders'

/**
 * Greys the placeholders in the live preview. Placeholder text sits between two invisible marks
 * (see utils/placeholders.ts); this finds the marked ranges and registers them with the CSS
 * Custom Highlight API (`::highlight(gb-placeholder)` in the stylesheet), so the page itself
 * stays untouched and Vue can keep updating its text nodes. Browsers without the API show the
 * placeholders as normal text.
 */
interface HighlightRegistry { set(name: string, highlight: unknown): void; delete(name: string): void }

export function usePlaceholderHighlights(root: Ref<HTMLElement | null>) {
  let observer: MutationObserver | null = null
  let timer: ReturnType<typeof setTimeout> | undefined

  const registry = () => (typeof CSS !== 'undefined' ? (CSS as unknown as { highlights?: HighlightRegistry }).highlights : undefined)

  function scan() {
    const highlights = registry()
    const container = root.value
    const HighlightClass = (globalThis as unknown as { Highlight?: new (...ranges: Range[]) => unknown }).Highlight
    if (!highlights || !container || !HighlightClass) return
    const ranges: Range[] = []
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT)
    for (let node = walker.nextNode(); node; node = walker.nextNode()) {
      const text = node.nodeValue ?? ''
      let from = 0
      for (;;) {
        const start = text.indexOf(PH_MARK, from)
        if (start < 0) break
        const end = text.indexOf(PH_MARK, start + 1)
        if (end < 0) break
        const range = document.createRange()
        range.setStart(node, start + 1)
        range.setEnd(node, end)
        ranges.push(range)
        from = end + 1
      }
    }
    if (ranges.length) highlights.set('gb-placeholder', new HighlightClass(...ranges))
    else highlights.delete('gb-placeholder')
  }

  function schedule() {
    clearTimeout(timer)
    timer = setTimeout(scan, 30) // a timer, not requestAnimationFrame: it also runs in background tabs
  }

  onMounted(() => {
    if (!root.value) return
    observer = new MutationObserver(schedule)
    observer.observe(root.value, { childList: true, subtree: true, characterData: true })
    scan()
  })
  onBeforeUnmount(() => {
    observer?.disconnect()
    clearTimeout(timer)
    registry()?.delete('gb-placeholder')
  })
}
