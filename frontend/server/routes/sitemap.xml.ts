interface Page<T> {
  next: string | null
  results: T[]
}

const escapeXml = (value: string) =>
  value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event)
  const api = apiBase(event)
  const site = String(config.public.siteUrl).replace(/\/$/, '')

  const urls: { loc: string; lastmod?: string }[] = [{ loc: `${site}/` }]

  let next: string | null = `${api}/guides/`
  while (next) {
    const page: Page<{ slug: string; updated_at: string }> = await $fetch<Page<{ slug: string; updated_at: string }>>(next)
    for (const guide of page.results) {
      urls.push({ loc: `${site}/guides/${guide.slug}`, lastmod: guide.updated_at })
    }
    next = page.next
  }

  const categories = await $fetch<{ slug: string }[]>(`${api}/categories/`)
  for (const category of categories) {
    urls.push({ loc: `${site}/category/${category.slug}` })
  }

  const body = urls
    .map(
      (u) =>
        `  <url><loc>${escapeXml(u.loc)}</loc>${u.lastmod ? `<lastmod>${escapeXml(u.lastmod)}</lastmod>` : ''}</url>`,
    )
    .join('\n')

  setHeader(event, 'content-type', 'application/xml; charset=utf-8')
  return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${body}\n</urlset>\n`
})
