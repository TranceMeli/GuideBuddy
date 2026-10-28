interface LoginResponse {
  access: string
  refresh: string
  user: Record<string, unknown>
}

/** Signs in and stores the JWTs in HttpOnly cookies (never in the response body). */
export default defineEventHandler(async (event) => {
  assertSameOrigin(event)
  const body = await readBody(event)
  const result = await callBackend<LoginResponse>(event, '/auth/login/', { method: 'POST', body })
  if (!result.ok) {
    setResponseStatus(event, result.status)
    return result.data
  }
  setAuthCookies(event, { access: result.data.access, refresh: result.data.refresh })
  return result.data.user
})
