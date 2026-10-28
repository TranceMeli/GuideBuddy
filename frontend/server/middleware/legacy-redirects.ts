/**
 * Permanent redirects from the former German page addresses to the English ones, so links
 * in old e-mails (confirmation, password reset), bookmarks and search results keep working.
 * The query string is kept. Guides whose German slug was replaced when GuideBuddy became
 * English only redirect to their new address too.
 */
const EXACT: Record<string, string> = {
  '/anmelden': '/login',
  '/registrieren': '/register',
  '/bestaetigen': '/confirm',
  '/passwort-vergessen': '/forgot-password',
  '/passwort-neu': '/reset-password',
  '/konto': '/account',
  '/impressum': '/imprint',
  '/datenschutz': '/privacy',
  '/nutzungsbedingungen': '/terms',
  '/lizenz': '/license',
  '/guides/neu': '/guides/new',
}

const RENAMED_GUIDES: Record<string, string> = {
  'die-erste-programmiersprache-wahlen': 'choose-your-first-programming-language',
  'vue-react-oder-nuxt': 'vue-react-or-nuxt',
  'jura': 'law',
}

const PATTERNS: [RegExp, string][] = [
  [/^\/kategorie\/([^/]+)\/?$/, '/category/$1'],
  [/^\/guides\/([^/]+)\/bearbeiten\/?$/, '/guides/$1/edit'],
  [/^\/guides\/([^/]+)\/verlauf\/?$/, '/guides/$1/history'],
]

export default defineEventHandler((event) => {
  if (event.method !== 'GET' && event.method !== 'HEAD') return
  const url = getRequestURL(event)
  const path = url.pathname.replace(/\/+$/, '') || '/'
  let target = EXACT[path]
  if (!target) {
    const match = PATTERNS.find(([pattern]) => pattern.test(path))
    if (match) target = path.replace(match[0], match[1])
  }
  const guide = path.match(/^\/guides\/([^/]+)(\/.*)?$/)
  const renamed = guide ? RENAMED_GUIDES[guide[1]!] : undefined
  if (!target && renamed) target = `/guides/${renamed}${guide![2] ?? ''}`
  if (target) return sendRedirect(event, `${target}${url.search}`, 301)
})
