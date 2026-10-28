<script setup lang="ts">
useSeoMeta({ title: 'New password', robots: 'noindex' })

const route = useRoute()
const uid = String(route.query.uid ?? '')
const token = String(route.query.token ?? '')

const password = ref('')
const done = ref('')
const errors = ref<string[]>([])
const busy = ref(false)

async function submit() {
  errors.value = []
  busy.value = true
  try {
    const result = await $fetch<{ detail: string }>('/api/auth/password-reset/confirm/', {
      method: 'POST',
      body: { uid, token, password: password.value },
    })
    done.value = result.detail
  } catch (e) {
    errors.value = apiErrorMessages(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <h1>Set a new password</h1>
    <div v-if="done" class="ok-box" role="status">
      <p>{{ done }}</p>
      <p><NuxtLink class="button" to="/login">Go to sign in</NuxtLink></p>
    </div>
    <p v-else-if="!uid || !token" class="error-box" role="alert">
      The link is incomplete. <NuxtLink to="/forgot-password">Request a new link</NuxtLink>
    </p>
    <form v-else class="stack narrow" @submit.prevent="submit">
      <div v-if="errors.length" class="error-box" role="alert">
        <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
        <p><NuxtLink to="/forgot-password">Request a new link</NuxtLink></p>
      </div>
      <div>
        <label for="password">New password</label>
        <input id="password" v-model="password" type="password" autocomplete="new-password" required>
      </div>
      <p><button type="submit" class="button" :disabled="busy">Save password</button></p>
    </form>
  </div>
</template>
