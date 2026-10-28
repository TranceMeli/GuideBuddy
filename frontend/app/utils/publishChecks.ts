import type { ElementDraft } from '~/utils/elements'

/**
 * Checks before publishing, taken from what makes a guide easy to follow: clear headings,
 * steps that say what to do, a way to check the result and links with words that say where
 * they lead. They only advise; publishing is never blocked, and an
 * empty guide passes (nothing is required).
 */
export interface Check {
  id: string
  label: string
  ok: boolean
  /** What to do when the check fails */
  hint: string
}

interface Fields {
  title: string
}

const GENERIC_HEADING = /^(introduction|intro|overview|summary|conclusion|section \d+|step \d+|untitled)$/i
const VAGUE_LINK = /^\s*(here|click here|this link|link|more|read more)\s*$/i
const VAGUE_MARKDOWN_LINK = /\[\s*(here|click here|this link|link|more|read more)\s*\]\(/i

export function publishChecks(form: Fields, elements: ElementDraft[]): Check[] {
  const titles = elements.filter((e) => ['section', 'step', 'heading'].includes(e.kind)).map((e) => e.text.trim()).filter(Boolean)
  const steps = elements.map((e, i) => ({ e, i })).filter(({ e }) => e.kind === 'step')
  const emptySteps = steps.filter(({ i }) => {
    const next = elements[i + 1]
    return !next || next.kind === 'step' || next.kind === 'section'
  }).length
  const vagueLinks = elements.filter((e) => {
    if (e.kind === 'link' || e.kind === 'download') return VAGUE_LINK.test(e.text)
    return ['text', 'important', 'error', 'tip', 'note', 'result', 'quote'].includes(e.kind) && VAGUE_MARKDOWN_LINK.test(e.text)
  }).length

  return [
    {
      id: 'headings',
      label: 'Title and headings describe the content',
      ok: !titles.concat(form.title.trim() ? [form.title.trim()] : []).some((h) => GENERIC_HEADING.test(h)),
      hint: 'Avoid headings like “Introduction” or “Step 2”; say what the part is about.',
    },
    {
      id: 'steps',
      label: 'Every step says what to do',
      ok: emptySteps === 0,
      hint: `${emptySteps} ${emptySteps === 1 ? 'step has' : 'steps have'} nothing after the title. Add a text, an image or a notice.`,
    },
    {
      id: 'result',
      label: 'Readers can check that it worked',
      ok: steps.length === 0 || elements.some((e) => e.kind === 'result'),
      hint: 'Add an expected result after an important step.',
    },
    {
      id: 'links',
      label: 'Links have meaningful text',
      ok: vagueLinks === 0,
      hint: 'Replace “here” or “click here” by words that say where the link goes.',
    },
  ]
}
