/** Deletes your own account (Django checks the password) and then removes the cookies. */
export default defineEventHandler(async (event) => {
  assertSameOrigin(event)
  const body = await readBody(event)
  const result = await callBackend(event, '/auth/account/', { method: 'DELETE', body })
  if (!result.ok) {
    setResponseStatus(event, result.status)
    return result.data
  }
  clearAuthCookies(event)
  setResponseStatus(event, 204)
  return null
})
