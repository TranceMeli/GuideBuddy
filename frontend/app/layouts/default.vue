<script setup lang="ts">
import type { Category } from '~/types/guide'

const { loggedIn, username, isModerator, logout } = useAuth()
const operator = useRuntimeConfig().public
const route = useRoute()
const year = new Date().getFullYear()

const { data: categories } = await useFetch<Category[]>(`${useApiBase()}/categories/`, { key: 'categories' })

// Mobile menu and categories menu close whenever the page changes
const menuOpen = ref(false)
const categoriesMenu = ref<HTMLDetailsElement | null>(null)
watch(
  () => route.fullPath,
  () => {
    menuOpen.value = false
    if (categoriesMenu.value) categoriesMenu.value.open = false
  },
)

async function onLogout() {
  await logout()
  await navigateTo('/')
}
</script>

<template>
  <div class="site">
    <a class="skip" href="#main">Skip to content</a>
    <header class="site-header">
      <div class="site-bar">
        <NuxtLink class="brand" to="/">GuideBuddy</NuxtLink>
        <button
          type="button"
          class="menu-toggle"
          :aria-expanded="menuOpen"
          aria-controls="site-menu"
          @click="menuOpen = !menuOpen"
        >
          <span aria-hidden="true">{{ menuOpen ? '✕' : '☰' }}</span> Menu
        </button>

        <div id="site-menu" class="site-menu" :class="{ 'is-open': menuOpen }">
          <nav class="main-nav" aria-label="Main navigation">
            <NuxtLink to="/" class="nav-link" exact-active-class="is-current">Guides</NuxtLink>
            <details ref="categoriesMenu" class="nav-menu">
              <summary class="nav-link" :class="{ 'is-current': route.path.startsWith('/category/') }">Categories</summary>
              <ul class="nav-dropdown">
                <li v-for="c in categories ?? []" :key="c.id">
                  <NuxtLink :to="`/category/${c.slug}`" active-class="is-current">{{ c.name }}</NuxtLink>
                </li>
              </ul>
            </details>
            <NuxtLink to="/guides/new" class="nav-link nav-cta" active-class="is-current">+ New guide</NuxtLink>
            <NuxtLink v-if="isModerator" to="/moderation" class="nav-link" active-class="is-current">Moderation</NuxtLink>
          </nav>

          <nav class="user-nav" aria-label="Account">
            <template v-if="loggedIn">
              <NuxtLink to="/account" class="nav-link" active-class="is-current">
                <span aria-hidden="true">●</span> {{ username }}
              </NuxtLink>
              <button type="button" class="nav-link nav-button" @click="onLogout">Sign out</button>
            </template>
            <template v-else>
              <NuxtLink to="/login" class="nav-link" active-class="is-current">Sign in</NuxtLink>
              <NuxtLink to="/register" class="nav-link" active-class="is-current">Register</NuxtLink>
            </template>
            <ThemeToggle />
          </nav>
        </div>
      </div>
    </header>

    <main id="main">
      <slot />
    </main>

    <ReaderEnhancer />
    <AppToast />
    <ConfirmDialog />

    <footer class="site-footer">
      <div class="footer-grid">
        <section aria-labelledby="footer-about">
          <h2 id="footer-about" class="footer-brand">GuideBuddy</h2>
          <p>Step-by-step guides by the community – free to read, edit and download.</p>
        </section>
        <section aria-labelledby="footer-company">
          <h2 id="footer-company" class="footer-title">Company</h2>
          <address>
            {{ operator.operatorName }}<br>
            <template v-for="(line, i) in String(operator.operatorAddress).split(', ')" :key="i">{{ line }}<br></template>
            {{ operator.operatorCountry }}<br>
            <a v-if="operator.operatorEmail" :href="`mailto:${operator.operatorEmail}`">{{ operator.operatorEmail }}</a>
          </address>
        </section>
        <nav aria-labelledby="footer-legal">
          <h2 id="footer-legal" class="footer-title">Legal</h2>
          <ul>
            <li><NuxtLink to="/imprint">Imprint</NuxtLink></li>
            <li><NuxtLink to="/privacy">Privacy policy</NuxtLink></li>
            <li><NuxtLink to="/terms">Terms of use</NuxtLink></li>
            <li><NuxtLink to="/license">Content license</NuxtLink></li>
            <li><a href="/sitemap.xml">Sitemap</a></li>
          </ul>
        </nav>
      </div>
      <p class="footer-bottom">
        © {{ year }} {{ operator.operatorName }} · Content under <NuxtLink to="/license">CC BY-SA 4.0</NuxtLink>
      </p>
    </footer>
  </div>
</template>
