import type { H3Event } from 'h3'

/**
 * Login with JWTs in two HttpOnly cookies: JavaScript in the browser cannot read them.
 * - gb_access:  short-lived, sent to Django with every request
 * - gb_refresh: longer-lived, only used to get a new access token
 */
export const ACCESS_COOKIE = 'gb_access'
export const REFRESH_COOKIE = 'gb_refresh'

/** Address of the Django API (only the Nuxt server calls it). */
export function apiBase(event: H3Event): string {
  return String(useRuntimeConfig(event).apiBase).replace(/\/$/, '')
}

export interface TokenPair {
  access: string
  refresh: string
}

/** Remaining lifetime of a JWT in seconds (only for the cookie max-age; Django does the checking). */
function secondsLeft(token: string, fallback: number): number {
  try {
    const payload = JSON.parse(atob((token.split('.')[1] ?? '').replace(/-/g, '+').replace(/_/g, '/')))
    const left = Math.floor(Number(payload.exp) - Date.now() / 1000)
    return left > 0 ? left : fallback
  } catch {
    return fallback
  }
}

function baseCookieOptions(event: H3Event) {
  const secure = String(useRuntimeConfig(event).public.siteUrl).startsWith('https://')
  return { httpOnly: true, sameSite: 'lax' as const, secure, path: '/' }
}

/** Sets both cookies and makes them visible for the rest of this request, too. */
export function setAuthCookies(event: H3Event, tokens: TokenPair) {
  const base = baseCookieOptions(event)
  setCookie(event, ACCESS_COOKIE, tokens.access, { ...base, maxAge: secondsLeft(tokens.access, 600) })
  setCookie(event, REFRESH_COOKIE, tokens.refresh, {
    ...base,
    maxAge: secondsLeft(tokens.refresh, 60 * 60 * 24 * 14),
  })
  rewriteRequestCookies(event, { [ACCESS_COOKIE]: tokens.access, [REFRESH_COOKIE]: tokens.refresh })
}

export function clearAuthCookies(event: H3Event) {
  deleteCookie(event, ACCESS_COOKIE, { path: '/' })
  deleteCookie(event, REFRESH_COOKIE, { path: '/' })
  rewriteRequestCookies(event, { [ACCESS_COOKIE]: null, [REFRESH_COOKIE]: null })
}

/** Rewrites the cookie header of the incoming request, so the new state applies later in the same request. */
function rewriteRequestCookies(event: H3Event, changes: Record<string, string | null>) {
  const current = String(event.node.req.headers.cookie ?? '')
    .split(';')
    .map((part) => part.trim())
    .filter((part) => part && !(part.split('=')[0]! in changes))
  for (const [name, value] of Object.entries(changes)) {
    if (value) current.push(`${name}=${value}`)
  }
  event.node.req.headers.cookie = current.join('; ')
}

/**
 * Protection against requests triggered by foreign websites (CSRF).
 * Write requests must come from this site itself.
 */
export function assertSameOrigin(event: H3Event) {
  if (['GET', 'HEAD', 'OPTIONS'].includes(event.method)) return
  const origin = getRequestHeader(event, 'origin')
  const host = getRequestHeader(event, 'x-forwarded-host') || getRequestHeader(event, 'host')
  let ok = true
  if (origin) {
    try {
      ok = new URL(origin).host === host
    } catch {
      ok = false
    }
  } else {
    const site = getRequestHeader(event, 'sec-fetch-site')
    ok = !site || site === 'same-origin' || site === 'none'
  }
  if (!ok) {
    throw createError({ statusCode: 403, statusMessage: 'Request from a foreign origin rejected' })
  }
}

/**
 * Headers for Django: the access token from the cookie and the visitor's address
 * (so the rate limits apply per visitor, not per Nuxt server).
 */
export function upstreamHeaders(event: H3Event): Record<string, string> {
  const config = useRuntimeConfig(event)
  const headers: Record<string, string> = {}
  const ip = getRequestIP(event, { xForwardedFor: Boolean(config.trustProxy) })
  if (ip) headers['x-forwarded-for'] = ip
  const access = getCookie(event, ACCESS_COOKIE)
  if (access) headers.authorization = `Bearer ${access}`
  return headers
}

/** Calls Django; errors are passed to the browser unchanged (status and JSON). */
export async function callBackend<T>(
  event: H3Event,
  path: string,
  options: { method?: 'GET' | 'POST' | 'DELETE'; body?: unknown } = {},
): Promise<{ ok: true; data: T } | { ok: false; status: number; data: unknown }> {
  try {
    const data = await $fetch<T>(`${apiBase(event)}${path}`, {
      method: options.method ?? 'GET',
      body: options.body as Record<string, unknown> | undefined,
      headers: upstreamHeaders(event),
    })
    return { ok: true, data }
  } catch (error) {
    const err = error as { statusCode?: number; data?: unknown }
    return {
      ok: false,
      status: err.statusCode ?? 502,
      data: err.data ?? { detail: 'The server cannot be reached.' },
    }
  }
}

// --- Automatic renewal -------------------------------------------------------

// Concurrent requests with the same refresh token share one renewal. Django replaces the
// refresh token on every renewal; without this, the second parallel request would fail
// with the old token and sign the user out.
const inflight = new Map<string, Promise<TokenPair | null | undefined>>()
const GRACE_MS = 10_000

/**
 * Gets a new token pair with the refresh token.
 * Returns the pair on success, null if the token is invalid (sign out), undefined on
 * technical errors (keep the cookies and try again later).
 */
export function refreshTokens(event: H3Event, refresh: string): Promise<TokenPair | null | undefined> {
  const known = inflight.get(refresh)
  if (known) return known
  const job = (async () => {
    try {
      const data = await $fetch<TokenPair>(`${apiBase(event)}/auth/refresh/`, {
        method: 'POST',
        body: { refresh },
        headers: upstreamHeaders(event),
      })
      return { access: data.access, refresh: data.refresh }
    } catch (error) {
      const status = (error as { statusCode?: number }).statusCode
      return status === 401 || status === 400 ? null : undefined
    }
  })()
  inflight.set(refresh, job)
  setTimeout(() => inflight.delete(refresh), GRACE_MS)
  return job
}

/**
 * For signing out: if this refresh token was just renewed, there is a successor.
 * It must be revoked on sign-out as well, otherwise it would stay valid.
 */
export async function takeSuccessor(refresh: string): Promise<string | null> {
  const job = inflight.get(refresh)
  inflight.delete(refresh)
  const pair = job ? await job : null
  return pair ? pair.refresh : null
}
