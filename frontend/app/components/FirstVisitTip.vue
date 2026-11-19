<script setup lang="ts">
/**
 * Short hint for a first visit: how to search, read, comment and write. Dismissed for good
 * (per browser). It is shown only after mounting, so the server-rendered page stays the same
 * for everybody.
 */
const KEY = 'guidebuddy:tip-dismissed'
const show = ref(false)

onMounted(() => {
  try {
    show.value = localStorage.getItem(KEY) !== '1'
  } catch {
    show.value = true
  }
})

function dismiss() {
  show.value = false
  try {
    localStorage.setItem(KEY, '1')
  } catch {
    /* private mode: the hint comes back next time */
  }
}
</script>

<template>
  <section v-if="show" class="first-visit" aria-labelledby="first-visit-title">
    <GuideIcon name="compass" :size="26" />
    <div class="first-visit-text">
      <h2 id="first-visit-title">New here? Four things to know</h2>
      <ul>
        <li>Search to find a guide.</li>
        <li>Read without an account.</li>
        <li>Sign in to comment and to write.</li>
        <li>Start from a template for your first guide.</li>
      </ul>
    </div>
    <div class="first-visit-actions">
      <NuxtLink to="/guides/new" class="btn btn-primary btn-small">Write your first guide</NuxtLink>
      <button type="button" class="btn btn-secondary btn-small" @click="dismiss">Dismiss</button>
    </div>
  </section>
</template>
