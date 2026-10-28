import type { AuthUser } from '~/types/guide'

/**
 * Login state. The token itself lives in an HttpOnly cookie and is invisible to
 * JavaScript; this only holds who is signed in (fetched from the server).
 */
export function useAuth() {
  const user = useState<AuthUser | null>('auth-user', () => null)
  const loggedIn = computed(() => !!user.value)
  const username = computed(() => user.value?.username ?? null)
  const isModerator = computed(() => !!user.value?.is_moderator)

  async function login(name: string, password: string) {
    user.value = await $fetch<AuthUser>('/api/auth/login', {
      method: 'POST',
      body: { username: name, password },
    })
  }

  async function logout() {
    try {
      await $fetch<unknown>('/api/auth/logout', { method: 'POST' })
    } catch {
      // already signed out - cleaning up locally is enough
    }
    user.value = null
    clearNuxtData()
  }

  /** Drop the session locally (e.g. after a 401). */
  async function clearSession() {
    await logout()
  }

  async function refresh() {
    try {
      user.value = await $fetch<AuthUser>('/api/auth/me/')
    } catch {
      user.value = null
    }
  }

  return { user, loggedIn, username, isModerator, login, logout, clearSession, refresh }
}

/** Only allow internal paths as redirect targets (no open redirect). */
export function safeNext(value: unknown): string {
  const next = typeof value === 'string' ? value : ''
  return next.startsWith('/') && !next.startsWith('//') ? next : '/'
}
