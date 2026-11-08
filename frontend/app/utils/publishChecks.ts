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
  summary?: string
}

const GENERIC_HEADING = /^(introduction|intro|overview|summary|conclusion|section \d+|step \d+|untitled)$/i
// "and" followed by a common action word: "Add the salt and fold" (two actions), not "Mix flour and water"
const TWO_ACTIONS = /\band\s+(then\s+)?(add|mix|stir|fold|press|click|open|close|cut|wait|rest|heat|cook|bake|boil|pour|remove|turn|select|choose|install|save|run|check|tighten|connect|attach|insert|wipe|rinse|drain|let|put|place|set|start|stop|restart)\b/i
const WEAK_TITLE = /^(about|introduction|overview|the|a|an|my|our|notes?|thoughts)\b/i
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
    return ['text', 'important', 'warning', 'danger', 'error', 'tip', 'note', 'result', 'quote'].includes(e.kind) && VAGUE_MARKDOWN_LINK.test(e.text)
  }).length

  // Per step: the elements up to the next step or section
  const blocks = steps.map(({ i }) => {
    const rest = elements.slice(i + 1)
    const end = rest.findIndex((e) => e.kind === 'step' || e.kind === 'section')
    return end < 0 ? rest : rest.slice(0, end)
  })
  const withResult = blocks.filter((b) => b.some((e) => e.kind === 'result')).length
  const firstStep = elements.findIndex((e) => e.kind === 'step')
  const intro = (firstStep < 0 ? elements : elements.slice(0, firstStep)).some((e) => e.kind === 'text' && e.text.trim())
  const lastStep = elements.map((e) => e.kind).lastIndexOf('step')
  const endsWithResult = lastStep < 0 || elements.slice(lastStep + 1).some((e) => e.kind === 'result')
  const unlabelled = elements.filter((e) => e.kind === 'image' && e.image && !e.image.caption.trim()).length
  const twoActions = steps.filter(({ e }) => TWO_ACTIONS.test(e.text)).map(({ e }) => e.text.trim())
  const title = form.title.trim()

  return [
    {
      id: 'title',
      label: 'The title says what readers will do',
      ok: !title || !WEAK_TITLE.test(title),
      hint: 'Start with a verb, for example “How to bake bread” instead of “About bread”.',
    },
    {
      id: 'goal',
      label: 'An introduction says what readers will achieve',
      ok: steps.length === 0 || intro || Boolean(form.summary?.trim()),
      hint: 'Before the first step, add a short text (or a summary): the goal and who the guide is for.',
    },
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
      id: 'step-results',
      label: 'Most steps say what readers should see',
      ok: steps.length < 2 || withResult * 2 >= steps.length,
      hint: `${withResult} of ${steps.length} steps have an expected result. Add one after the steps that are easy to get wrong.`,
    },
    {
      id: 'one-action',
      label: 'Each step names one action',
      ok: twoActions.length === 0,
      hint: `“${twoActions[0] ?? ''}” may be two actions. Split it into two steps if it is.`,
    },
    {
      id: 'outcome',
      label: 'The guide ends with the final result',
      ok: endsWithResult,
      hint: 'After the last step, add an expected result that tells readers how to check that it worked.',
    },
    {
      id: 'captions',
      label: 'Images have a caption',
      ok: unlabelled === 0,
      hint: `${unlabelled} ${unlabelled === 1 ? 'image has' : 'images have'} no caption. Say what readers should look at.`,
    },
    {
      id: 'links',
      label: 'Links have meaningful text',
      ok: vagueLinks === 0,
      hint: 'Replace “here” or “click here” by words that say where the link goes.',
    },
  ]
}
