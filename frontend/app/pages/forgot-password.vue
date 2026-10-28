<script setup lang="ts">
useSeoMeta({ title: 'Forgot password', robots: 'noindex' })

const email = ref('')
const done = ref('')
const errors = ref<string[]>([])
const busy = ref(false)

async function submit() {
  errors.value = []
  busy.value = true
  try {
    const result = await $fetch<{ detail: string }>('/api/auth/password-reset/', {
      method: 'POST',
      body: { email: email.value },
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
    <h1>Forgot your password?</h1>
    <div v-if="done" class="ok-box" role="status">
      <p>{{ done }}</p>
      <p v-if="$config.public.siteUrl.startsWith('http://localhost')" class="muted">
        Development: the link is shown in the terminal of the Django server.
      </p>
    </div>
    <form v-else class="stack narrow" @submit.prevent="submit">
      <div v-if="errors.length" class="error-box" role="alert">
        <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
      </div>
      <div>
        <label for="email">E-mail</label>
        <input id="email" v-model="email" type="email" autocomplete="email" required>
      </div>
      <p><button type="submit" class="button" :disabled="busy">Send reset link</button></p>
    </form>
  </div>
</template>
