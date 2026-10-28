import type { ComputedRef, InjectionKey } from 'vue'

/**
 * Visible labels of the guide reading templates. GuideBuddy is English only for now, so
 * there is one set; the lookup by language stays so further sets can be added later.
 * `lang` is the language the labels are in, for the lang attribute of elements that
 * carry them.
 */
export interface GuideLabels {
  lang: string
  // notice boxes
  tip: string; note: string; warning: string; error: string; result: string; focusResult: string
  // header
  level: string; duration: string; prerequisites: string; materials: string; goals: string
  levels: Record<string, string>
  count: Record<string, [string, string]>
  startGuide: string; downloadPdf: string; printVersion: string; attachment: string; download: string
  // step by step
  contents: string; progress: (done: number, total: number) => string; stepDone: string
  step: string; stepOf: (current: number, total: number) => string
  previousStep: string; nextStep: string; showStep: string; upcoming: string
  focusMode: string; resetProgress: string; resetConfirm: string
  commonMistakes: string; rightWay: string; conclusion: string
  close: string; menu: string; back: string; next: string; finish: string; section: string
  // code
  wrong: string; right: string; copy: string; copied: string
  // images: caption label, kinds and the enlarge button
  noContent: string
  figure: string; imageKinds: Record<string, string>
  types: Record<string, string>
}

const en: GuideLabels = {
  lang: 'en',
  tip: 'Tip', note: 'Note', warning: 'Important', error: 'Error', result: 'Expected result', focusResult: 'This is what it should look like',
  level: 'Level', duration: 'Duration', prerequisites: 'Prerequisites', materials: 'What you need', goals: 'What you can do afterwards',
  levels: { beginner: 'Beginner', intermediate: 'Intermediate', advanced: 'Advanced' },
  count: {
    page: ['step', 'steps'], free: ['step', 'steps'],
  },
  startGuide: 'Start guide', downloadPdf: 'Download PDF', printVersion: 'Print version',
  attachment: 'Attachment', download: 'Download',
  contents: 'Contents', progress: (done, total) => `${done} of ${total}`, stepDone: 'Step done',
  step: 'Step', stepOf: (current, total) => `Step ${current} of ${total}`,
  previousStep: 'Previous step', nextStep: 'Next step', showStep: 'Show step', upcoming: 'coming up',
  focusMode: 'Focus mode', resetProgress: 'Reset progress', resetConfirm: 'Reset your progress in this guide?',
  commonMistakes: 'Common mistakes', rightWay: 'How to do it right', conclusion: 'Well done!',
  close: 'Close', menu: 'All steps', back: 'Back', next: 'Next', finish: 'Finish guide', section: 'Section',
  wrong: 'Wrong', right: 'Right', copy: 'Copy', copied: 'Copied',
  noContent: 'This guide has no content yet.',
  figure: 'Figure',
  imageKinds: { photo: 'Photo', screenshot: 'Screenshot', mockup: 'Mockup (schematic)', diagram: 'Diagram' },
  types: { page: 'Guide', free: 'Guide' },
}

const SETS: Record<string, GuideLabels> = { en }

export const labelsFor = (language?: string | null): GuideLabels => SETS[(language ?? '').slice(0, 2)] ?? en

/** Labels of a guide, reactive. Provided once by GuideReader, read by the parts inside it. */
export const GUIDE_LABELS_KEY: InjectionKey<ComputedRef<GuideLabels>> = Symbol('guide-labels')
export function useGuideLabels(): ComputedRef<GuideLabels> {
  return inject(GUIDE_LABELS_KEY, computed(() => en))
}
