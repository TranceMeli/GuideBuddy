import type { AuthUser } from '~/types/guide'

/**
 * While rendering on the server: who is signed in? The access token comes from the
 * HttpOnly cookie (the server middleware has already renewed it if needed).
 */
export default defineNuxtPlugin(async () => {
  const access = useCookie('gb_access')
  if (!access.value) return
  const user = useState<AuthUser | null>('auth-user', () => null)
  try {
    user.value = await $fetch<AuthUser>(`${useApiBase()}/auth/me/`, {
      headers: { Authorization: `Bearer ${access.value}` },
    })
  } catch {
    user.value = null
  }
})
