import TurndownService from 'turndown'
import { tables } from 'turndown-plugin-gfm'
import type { Step } from '~/types/guide'
import { styleClassesOf } from '~/utils/textStyles'

/**
 * The editor only knows one continuous text. The guide is still stored as steps
 * (for PDF, history and search engines): every large heading (H2) starts a new step.
 */

export interface DraftStep {
  title: string
  body: string // Markdown
}

// Title of the text before the first heading; follows the guide's language.
// Every title is recognised when an existing guide is loaded back into the editor.
const INTRO_TITLES: Record<string, string> = { en: 'Overview' }
const introTitle = (language = 'en') => INTRO_TITLES[language] ?? INTRO_TITLES.en!
const isIntroTitle = (title: string) => Object.values(INTRO_TITLES).includes(title)

let turndown: TurndownService | null = null
function toMarkdown(html: string): string {
  if (!turndown) {
    turndown = new TurndownService({
      headingStyle: 'atx',
      codeBlockStyle: 'fenced',
      bulletListMarker: '-',
      emDelimiter: '*',
    })
    turndown.use(tables)
    // Text styles (colour, highlight, font) stay as <span class="c-teal">: Markdown has no
    // syntax for them, the server keeps exactly these class names and drops everything else.
    turndown.addRule('textStyle', {
      filter: (node) => node.nodeName === 'SPAN' && styleClassesOf(node.getAttribute('class')).length > 0,
      replacement: (content, node) => {
        const classes = styleClassesOf((node as HTMLElement).getAttribute('class')).join(' ')
        return content.trim() ? `<span class="${classes}">${content}</span>` : content
      },
    })
  }
  return turndown.turndown(html).trim()
}

const escapeHtml = (value: string) =>
  value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')

/** Rich text (HTML from the editor) -> steps with Markdown content. Browser only. */
export function htmlToSteps(html: string, guideTitle: string, language?: string): { steps: DraftStep[]; errors: string[] } {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  const sections: { title: string | null; html: string }[] = [{ title: null, html: '' }]
  for (const node of Array.from(doc.body.childNodes)) {
    if (node instanceof HTMLElement && (node.tagName === 'H1' || node.tagName === 'H2')) {
      sections.push({ title: (node.textContent ?? '').trim(), html: '' })
    } else {
      sections[sections.length - 1]!.html += node instanceof HTMLElement ? node.outerHTML : (node.textContent ?? '')
    }
  }

  const hasHeadings = sections.length > 1
  const steps: DraftStep[] = []
  const errors: string[] = []
  sections.forEach((section, index) => {
    const body = toMarkdown(section.html)
    if (section.title === null) {
      // text before the first heading
      if (body) steps.push({ title: hasHeadings ? introTitle(language) : guideTitle.trim() || introTitle(language), body })
      return
    }
    const title = section.title || `Step ${index}`
    if (!body) {
      errors.push(`The heading “${title}” has no text below it yet.`)
      return
    }
    steps.push({ title: title.slice(0, 160), body })
  })
  if (!steps.length && !errors.length) errors.push('Please write the content of the guide.')
  return { steps, errors }
}

/** Stored steps -> one HTML document for the editor. */
export function stepsToHtml(steps: Step[], guideTitle: string): string {
  return steps
    .map((step, index) => {
      // A single step without its own heading (title = guide title), or the introduction
      const implicit =
        (steps.length === 1 && step.title === guideTitle) || (index === 0 && isIntroTitle(step.title))
      return `${implicit ? '' : `<h2>${escapeHtml(step.title)}</h2>`}${step.body_html}`
    })
    .join('')
}
