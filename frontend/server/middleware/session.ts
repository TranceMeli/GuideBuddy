/**
 * Keeps the login fresh. Runs on every request (pages and /api/...):
 * if the short-lived access cookie is missing but the refresh cookie is still there, a new
 * token pair is fetched silently and set as new HttpOnly cookies.
 * The user does not notice any of this.
 */
export default defineEventHandler(async (event) => {
  const path = event.path.split('?')[0] ?? ''
  // Static files need no login
  if (path.startsWith('/_nuxt/') || path.startsWith('/__nuxt') || /\.[a-z0-9]{2,5}$/i.test(path)) return

  const access = getCookie(event, ACCESS_COOKIE)
  const refresh = getCookie(event, REFRESH_COOKIE)
  if (access || !refresh) return
  // Login and logout handle their cookies themselves
  if (path === '/api/auth/login' || path === '/api/auth/logout') return

  const tokens = await refreshTokens(event, refresh)
  if (tokens) setAuthCookies(event, tokens)
  else if (tokens === null) clearAuthCookies(event) // refresh token invalid: sign out
})
