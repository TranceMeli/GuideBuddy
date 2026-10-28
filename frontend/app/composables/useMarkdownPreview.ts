/**
 * Markdown rendering for the live preview.
 *
 * `md(text)` returns the server-rendered, sanitized HTML for a text. Texts that were not
 * rendered yet are collected and sent in one request after a short typing pause; until the
 * answer arrives the text is shown escaped as plain paragraphs. Rendered results are cached,
 * so unchanged fields are never sent again.
 */
const DEBOUNCE_MS = 300
const MAX_CACHE = 600
const BATCH = 100

const escapeHtml = (value: string) =>
  value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** Safe stand-in while the server renders: escaped text, paragraphs and line breaks kept */
function plainHtml(text: string): string {
  return text
    .trim()
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, '<br>')}</p>`)
    .join('')
}

export function useMarkdownPreview() {
  const cache = shallowReactive(new Map<string, string>())
  const pending = new Set<string>()
  const failed = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null
  let inflight = false

  function schedule() {
    if (import.meta.server || timer) return
    timer = setTimeout(flush, DEBOUNCE_MS)
  }

  async function flush() {
    timer = null
    if (inflight || !pending.size) return
    const texts = [...pending].slice(0, BATCH)
    texts.forEach((text) => pending.delete(text))
    inflight = true
    try {
      const { html } = await $fetch<{ html: string[] }>('/api/markdown/render/', {
        method: 'POST',
        body: { texts },
      })
      texts.forEach((text, i) => cache.set(text, html[i] ?? ''))
      failed.value = false
      // Keep the cache bounded: drop the oldest entries (Map keeps insertion order)
      for (const key of cache.keys()) {
        if (cache.size <= MAX_CACHE) break
        cache.delete(key)
      }
    } catch {
      failed.value = true // keep showing the plain stand-in
    } finally {
      inflight = false
      if (pending.size) schedule()
    }
  }

  /** Sanitized HTML for a Markdown text (plain stand-in until the server answered). */
  function md(text: string | null | undefined): string {
    if (!text || !text.trim()) return ''
    const html = cache.get(text)
    if (html !== undefined) return html
    // After a failed request this retries on the next change, at typing pace (debounced)
    pending.add(text)
    schedule()
    return plainHtml(text)
  }

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
  })

  return { md, failed }
}
