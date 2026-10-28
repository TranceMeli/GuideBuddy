/** Signs out: revokes the refresh token at Django and removes both cookies. */
export default defineEventHandler(async (event) => {
  assertSameOrigin(event)
  const refresh = getCookie(event, REFRESH_COOKIE)
  if (refresh) {
    const successor = await takeSuccessor(refresh)
    for (const token of [refresh, successor]) {
      if (token) await callBackend(event, '/auth/logout/', { method: 'POST', body: { refresh: token } })
    }
  }
  clearAuthCookies(event)
  setResponseStatus(event, 204)
  return null
})
