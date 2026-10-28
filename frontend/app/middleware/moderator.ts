export default defineNuxtRouteMiddleware((to) => {
  const { loggedIn, isModerator } = useAuth()
  if (!loggedIn.value) {
    return navigateTo({ path: '/login', query: { next: to.fullPath } })
  }
  if (!isModerator.value) {
    throw createError({ statusCode: 403, statusMessage: 'Moderators only', fatal: true })
  }
})
