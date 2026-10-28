// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: false },
  css: ['~/assets/css/tokens.css', '~/assets/css/main.css', '~/assets/css/templates.css', '~/assets/css/guides.css'],

  runtimeConfig: {
    // Server only: address of the Django API. The browser never talks to Django directly,
    // only through /api on this server. Override with NUXT_API_BASE
    apiBase: 'http://127.0.0.1:8000/api',
    // Set to true behind a reverse proxy (Nginx, Caddy ...), so the real visitor address
    // from X-Forwarded-For is used for the rate limits. Override with NUXT_TRUST_PROXY
    trustProxy: false,
    public: {
      // Public address of this frontend (sitemap, canonical links, secure cookie with https).
      // Override with NUXT_PUBLIC_SITE_URL
      siteUrl: 'http://localhost:3000',
      // Optional: Cloudflare Turnstile (captcha). Empty = off. NUXT_PUBLIC_TURNSTILE_SITE_KEY
      turnstileSiteKey: '',
      // Operator shown in the footer, imprint and privacy policy. The defaults are a fictional
      // placeholder company – replace them via NUXT_PUBLIC_OPERATOR_* before going live.
      operatorName: 'GuideBuddy GmbH',
      operatorAddress: 'Musterstraße 12, 70173 Stuttgart',
      operatorCountry: 'Germany',
      operatorEmail: 'hello@guidebuddy.example',
      hostingProvider: '',
      mailProvider: '',
    },
  },

  // Basic security headers for all pages
  routeRules: {
    '/**': {
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
      },
    },
  },

  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content:
            'Step-by-step guides on any topic – free to read and to download as PDF.',
        },
      ],
    },
  },
})
