/**
 * Forwards all calls to /api/... to the Django API and adds the access token (JWT) from the
 * HttpOnly cookie. Browser code never needs to see the token, and the browser does not
 * have to reach Django directly (or through CORS).
 */
export default defineEventHandler(async (event) => {
  assertSameOrigin(event)

  // These endpoints have their own handlers that set or delete the cookies. Passed through
  // here, the browser would see the tokens in the response body.
  // Django decodes %-escapes in the path. So decode here as well (and collapse "//"),
  // otherwise e.g. "/api/auth/%6Cogin/" would get past the block.
  let bare: string
  try {
    bare = decodeURIComponent(getRequestURL(event).pathname)
  } catch {
    throw createError({ statusCode: 400, statusMessage: 'Invalid address' })
  }
  bare = bare.replace(/\/{2,}/g, '/').replace(/\/+$/, '')
  if (['/api/auth/login', '/api/auth/refresh', '/api/auth/logout', '/api/auth/account'].includes(bare)) {
    throw createError({ statusCode: 404, statusMessage: 'Not found' })
  }

  // Keep the path including the trailing "/" (Django expects it)
  const url = getRequestURL(event)
  const path = url.pathname.replace(/^\/api/, '')
  const target = `${apiBase(event)}${path}${url.search}`

  const headers = getProxyRequestHeaders(event)
  delete headers.cookie
  delete headers.authorization
  delete headers['x-forwarded-for']
  Object.assign(headers, upstreamHeaders(event))

  const hasBody = !['GET', 'HEAD', 'OPTIONS'].includes(event.method)
  return sendProxy(event, target, {
    headers,
    fetchOptions: {
      method: event.method,
      body: hasBody ? await readRawBody(event, false) : undefined,
      redirect: 'manual',
    },
  })
})
