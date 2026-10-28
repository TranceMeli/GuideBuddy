export type ThemeMode = 'auto' | 'light' | 'dark'

const ORDER: ThemeMode[] = ['auto', 'light', 'dark']
const LABEL: Record<ThemeMode, string> = { auto: 'Auto', light: 'Light', dark: 'Dark' }
const cookieOptions = { maxAge: 60 * 60 * 24 * 365, sameSite: 'lax' as const, path: '/' }

/**
 * Light/dark mode of the standard look. The choice is kept in a cookie ("gb_theme"), so the
 * server already renders the right mode (no flash). "auto" follows the operating system.
 * Rendered as data-mode on <html>.
 */
export function useTheme() {
  const mode = useCookie<ThemeMode>('gb_theme', { default: () => 'auto', ...cookieOptions })
  if (!ORDER.includes(mode.value)) mode.value = 'auto'

  useHead({
    htmlAttrs: { 'data-mode': computed(() => (mode.value === 'auto' ? undefined : mode.value)) },
  })

  function next() {
    mode.value = ORDER[(ORDER.indexOf(mode.value) + 1) % ORDER.length]!
  }

  /** Print in the light mode ("Print version"): switch for the print dialog, then switch back. */
  async function printVersion() {
    const before = mode.value
    mode.value = 'light'
    await nextTick()
    const restore = () => {
      mode.value = before
      window.removeEventListener('afterprint', restore)
    }
    window.addEventListener('afterprint', restore)
    window.print()
  }

  return { mode, label: computed(() => LABEL[mode.value]), next, printVersion }
}
