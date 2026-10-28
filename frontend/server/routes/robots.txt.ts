export default defineEventHandler((event) => {
  const site = String(useRuntimeConfig(event).public.siteUrl).replace(/\/$/, '')
  setHeader(event, 'content-type', 'text/plain; charset=utf-8')
  return [
    'User-agent: *',
    'Allow: /',
    'Disallow: /api/',
    'Disallow: /login',
    'Disallow: /register',
    'Disallow: /confirm',
    'Disallow: /forgot-password',
    'Disallow: /reset-password',
    'Disallow: /account',
    'Disallow: /moderation',
    'Disallow: /guides/new',
    '',
    `Sitemap: ${site}/sitemap.xml`,
    '',
  ].join('\n')
})
