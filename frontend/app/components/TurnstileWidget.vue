<script setup lang="ts">
/**
 * Optional captcha (Cloudflare Turnstile). Without a site key (NUXT_PUBLIC_TURNSTILE_SITE_KEY)
 * nothing is shown and nothing is loaded from Cloudflare.
 */
const emit = defineEmits<{ token: [value: string] }>()
const siteKey = String(useRuntimeConfig().public.turnstileSiteKey || '')
const box = ref<HTMLElement | null>(null)

declare global {
  interface Window {
    turnstile?: {
      render: (el: HTMLElement, options: Record<string, unknown>) => string
    }
  }
}

onMounted(() => {
  if (!siteKey || !box.value) return
  const el = box.value
  const render = () =>
    window.turnstile?.render(el, {
      sitekey: siteKey,
      callback: (token: string) => emit('token', token),
      'expired-callback': () => emit('token', ''),
    })
  if (window.turnstile) return render()
  const script = document.createElement('script')
  script.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit'
  script.async = true
  script.onload = render
  document.head.appendChild(script)
})
</script>

<template>
  <div v-if="siteKey" ref="box" />
</template>
