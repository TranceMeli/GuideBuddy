import { styleClassesOf, withStyle, type StyleKind } from '~/utils/textStyles'

/**
 * Pure helpers of the Markdown field toolbar: each takes the text and the selection and
 * returns the new text with the selection to restore. Text styles are written as
 * <span class="c-teal">…</span>, the only HTML the server keeps (see textStyles.ts).
 */
export interface Edit { text: string; start: number; end: number }

/** **bold**, *italic*, `code`: wraps the selection, or inserts the placeholder selected */
export function wrap(text: string, start: number, end: number, before: string, after: string, placeholder: string): Edit {
  const selected = text.slice(start, end)
  // a second click on the same format takes it off again
  if (selected.startsWith(before) && selected.endsWith(after) && selected.length >= before.length + after.length) {
    const inner = selected.slice(before.length, selected.length - after.length)
    return { text: text.slice(0, start) + inner + text.slice(end), start, end: start + inner.length }
  }
  const inner = selected || placeholder
  const next = text.slice(0, start) + before + inner + after + text.slice(end)
  return { text: next, start: start + before.length, end: start + before.length + inner.length }
}

/** Lists: puts "- " in front of every selected line (or takes it off again) */
export function toggleList(text: string, start: number, end: number): Edit {
  const lineStart = text.lastIndexOf('\n', start - 1) + 1
  const nextBreak = text.indexOf('\n', end)
  const lineEnd = nextBreak === -1 ? text.length : nextBreak
  const lines = text.slice(lineStart, lineEnd).split('\n')
  const allListed = lines.every((l) => /^\s*[-*] /.test(l))
  const changed = lines.map((l) => (allListed ? l.replace(/^(\s*)[-*] /, '$1') : `- ${l}`)).join('\n')
  return { text: text.slice(0, lineStart) + changed + text.slice(lineEnd), start: lineStart, end: lineStart + changed.length }
}

/** [text](https://): the address part is selected afterwards, ready to type over */
export function link(text: string, start: number, end: number): Edit {
  const label = text.slice(start, end) || 'link text'
  const url = 'https://'
  const next = `${text.slice(0, start)}[${label}](${url})${text.slice(end)}`
  const urlStart = start + label.length + 3
  return { text: next, start: urlStart, end: urlStart + url.length }
}

const SPAN = /^<span class="([^"]*)">([\s\S]*)<\/span>$/

/** The text styles on the selected text (when it is wrapped in a style span) */
export function stylesOf(selected: string): Partial<Record<StyleKind, string | null>> {
  const match = SPAN.exec(selected)
  const result: Partial<Record<StyleKind, string | null>> = {}
  if (!match) return result
  for (const name of styleClassesOf(match[1])) {
    if (name.startsWith('c-')) result.color = name
    else if (name.startsWith('h-')) result.highlight = name
    else if (name.startsWith('f-')) result.font = name
  }
  return result
}

/** Sets (or, with null, removes) one kind of style on the selection; other styles stay */
export function applyStyle(text: string, start: number, end: number, kind: StyleKind, value: string | null): Edit {
  const selected = text.slice(start, end)
  const match = SPAN.exec(selected)
  const inner = match ? match[2]! : selected || (value ? 'styled text' : '')
  const classes = withStyle(match ? styleClassesOf(match[1]) : [], kind, value)
  const wrapped = classes.length ? `<span class="${classes.join(' ')}">${inner}</span>` : inner
  const next = text.slice(0, start) + wrapped + text.slice(end)
  return { text: next, start, end: start + wrapped.length }
}
