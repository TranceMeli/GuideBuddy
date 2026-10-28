<script setup lang="ts">
/**
 * Small enhancements for everything that is shown as guide content (reading templates, live
 * preview, focus mode), mounted once in the layout. Renders only the image dialog.
 *
 * - Tables in guide text get the label of their column on every cell, so on phones the CSS
 *   can stack each row instead of cutting the table off at the side.
 * - Output lines of terminal blocks (console code with a prompt) are marked by meaning: red for
 *   errors, yellow for warnings, green for success. The class only; the look is in templates.css.
 * - Images in guide text and steps can be enlarged: click, tap, Enter or Space opens a dialog;
 *   Esc or a click outside closes it and the focus returns to the image.
 *
 * Content arrives as sanitized HTML (v-html), so this works on the rendered DOM; a
 * MutationObserver repeats it whenever the content changes (for example while typing).
 */
const dialog = ref<HTMLDialogElement | null>(null)
const view = reactive({ src: '', alt: '', caption: '' })
const ERROR = /\b(error|traceback|exception|fatal|failed|not recognised|not recognized|denied|cannot|no such)\b/i
const WARN = /\b(warning|warn|deprecated|caution)\b/i
const OK = /^\s*(ok\b|success|done\b|passed|✓)|\b(successful|successfully|installed)\b/i
let observer: MutationObserver | null = null
let scheduled = false

function enhance() {
  scheduled = false
  for (const table of document.querySelectorAll<HTMLTableElement>('.prose table')) {
    const heads = Array.from(table.querySelectorAll('thead th'), (th) => th.textContent?.trim() ?? '')
    if (!heads.length) continue
    table.classList.add('is-stackable')
    table.querySelectorAll('tbody tr').forEach((row) => {
      Array.from(row.children).forEach((cell, i) => {
        const label = heads[i] ?? ''
        if (cell.getAttribute('data-label') !== label) cell.setAttribute('data-label', label)
      })
    })
  }
  for (const line of document.querySelectorAll<HTMLElement>('.codehilite:has(.gp) .go:not([data-tone])')) {
    const text = line.textContent ?? ''
    const tone = ERROR.test(text) ? 'err' : WARN.test(text) ? 'warn' : OK.test(text) ? 'ok' : 'none'
    line.dataset.tone = tone
  }
  for (const img of document.querySelectorAll<HTMLImageElement>('.prose img:not([data-zoom]), .step-image img:not([data-zoom])')) {
    if (img.closest('a')) continue // an image that is a link keeps its link
    img.dataset.zoom = '1'
    img.tabIndex = 0
    img.setAttribute('role', 'button')
    img.setAttribute('aria-label', `Enlarge image: ${img.alt}`)
  }
}
// A short timer instead of requestAnimationFrame: it also runs in background tabs
function schedule() {
  if (scheduled) return
  scheduled = true
  setTimeout(enhance, 30)
}

function open(img: HTMLImageElement) {
  view.src = img.currentSrc || img.src
  view.alt = img.alt
  view.caption = img.closest('figure')?.querySelector('figcaption')?.textContent?.trim() ?? ''
  dialog.value?.showModal()
}
function onClick(event: MouseEvent) {
  const img = (event.target as Element | null)?.closest?.('img[data-zoom]')
  if (img) open(img as HTMLImageElement)
}
function onKey(event: KeyboardEvent) {
  const target = event.target as HTMLElement | null
  if ((event.key === 'Enter' || event.key === ' ') && target?.matches?.('img[data-zoom]')) {
    event.preventDefault()
    open(target as HTMLImageElement)
  }
}
function onDialogClick(event: MouseEvent) {
  if (event.target === dialog.value) dialog.value?.close() // a click on the backdrop
}

onMounted(() => {
  enhance()
  observer = new MutationObserver(schedule)
  observer.observe(document.body, { childList: true, subtree: true })
  document.addEventListener('click', onClick)
  document.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  observer?.disconnect()
  document.removeEventListener('click', onClick)
  document.removeEventListener('keydown', onKey)
})
</script>

<template>
  <dialog ref="dialog" class="lightbox" aria-label="Enlarged image" @click="onDialogClick">
    <figure class="lightbox-inner">
      <img v-if="view.src" :src="view.src" :alt="view.alt">
      <figcaption v-if="view.caption" class="lightbox-caption">{{ view.caption }}</figcaption>
      <form method="dialog"><button class="btn btn-secondary btn-small lightbox-close">Close</button></form>
    </figure>
  </dialog>
</template>
