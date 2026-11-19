import type { CommentKind, GuideStatus } from '~/types/guide'

/** Status shown next to a guide: always a word and an icon, never colour alone */
export const STATUS: Record<GuideStatus, { label: string; tone: 'ok' | 'caution' | 'muted' }> = {
  published: { label: 'Published', tone: 'ok' },
  outdated: { label: 'Outdated', tone: 'caution' },
  archived: { label: 'Archived', tone: 'muted' },
}

/** What a comment is about; `comment` is stored under its old name and shown as Feedback */
export const COMMENT_KINDS: { value: CommentKind; label: string; hint: string }[] = [
  { value: 'comment', label: 'Feedback', hint: 'Tell the author what worked or what did not.' },
  { value: 'question', label: 'Question', hint: 'Stuck on a step? Name the step and what you see.' },
  { value: 'error', label: 'Error', hint: 'A step does not work or is wrong. Say what happened.' },
  { value: 'addition', label: 'Addition', hint: 'A tip or detail the guide is missing.' },
]

/** Kinds that get a tag in the list; plain feedback needs none */
export const kindLabel = (kind: CommentKind) => (kind === 'comment' ? '' : COMMENT_KINDS.find((k) => k.value === kind)?.label ?? '')

export const COMMENT_REPORT_REASONS = [
  { value: 'spam', label: 'Spam or advertising' },
  { value: 'harassment', label: 'Harassment' },
  { value: 'vandalism', label: 'Vandalism or false content' },
  { value: 'privacy', label: 'Personal data' },
  { value: 'illegal', label: 'Illegal content' },
  { value: 'other', label: 'Other' },
]

export const GUIDE_REPORT_REASONS = [
  { value: 'spam', label: 'Spam or advertising' },
  { value: 'vandalism', label: 'False or dangerous advice' },
  { value: 'outdated', label: 'Outdated: steps no longer work' },
  { value: 'harassment', label: 'Harassment' },
  { value: 'privacy', label: 'Personal data' },
  { value: 'copyright', label: 'Copyright infringement' },
  { value: 'illegal', label: 'Illegal content' },
  { value: 'other', label: 'Other' },
]

/** "By anna", "By anna and 1 contributor", "By anna and 3 contributors" */
export function byLine(author: string | null, contributors: string[]) {
  const name = author ?? 'a deleted account'
  if (!contributors.length) return `By ${name}`
  return `By ${name} and ${contributors.length} ${contributors.length === 1 ? 'contributor' : 'contributors'}`
}

/** The note above a guide that may be out of date, or '' when there is nothing to say */
export function outdatedNote(status: GuideStatus, reports: number) {
  if (status === 'archived') return ''
  if (status === 'outdated' && !reports) return 'It is marked as outdated, so some steps may no longer work.'
  if (!reports) return ''
  return `${reports === 1 ? '1 reader says' : `${reports} readers say`} the steps no longer work.`
}
