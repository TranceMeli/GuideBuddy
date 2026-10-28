<script setup lang="ts">
useSeoMeta({ title: 'Register', robots: 'noindex' })

const username = ref('')
const email = ref('')
const password = ref('')
const acceptTerms = ref(false)
const website = ref('') // Honeypot: people do not see this field
const captcha = ref('')
const errors = ref<string[]>([])
const done = ref('')
const busy = ref(false)
const dev = import.meta.dev

async function submit() {
  errors.value = []
  busy.value = true
  try {
    const result = await $fetch<{ detail: string }>('/api/auth/register/', {
      method: 'POST',
      body: {
        username: username.value,
        email: email.value,
        password: password.value,
        accept_terms: acceptTerms.value,
        website: website.value,
        captcha_token: captcha.value,
      },
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
    <h1>Create an account</h1>

    <div v-if="done" class="ok-box" role="status">
      <p>{{ done }}</p>
      <p v-if="dev" class="muted">
        Development: no real e-mail is sent. You will find the confirmation link in the
        terminal where the Django server is running.
      </p>
    </div>

    <form v-else class="stack narrow" @submit.prevent="submit">
      <div v-if="errors.length" class="error-box" role="alert">
        <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
      </div>
      <div>
        <label for="username">User name</label>
        <input id="username" v-model="username" type="text" autocomplete="username" required>
        <p class="muted">It is shown publicly in the history of your changes.</p>
      </div>
      <div>
        <label for="email">E-mail</label>
        <input id="email" v-model="email" type="email" autocomplete="email" required>
        <p class="muted">Never published. You will receive a confirmation link.</p>
      </div>
      <div>
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" autocomplete="new-password" required>
        <p class="muted">At least 8 characters, not only digits, not a common password.</p>
      </div>
      <div class="hp" aria-hidden="true">
        <label for="website">Website (please leave empty)</label>
        <input id="website" v-model="website" type="text" tabindex="-1" autocomplete="off">
      </div>
      <div class="check">
        <input id="terms" v-model="acceptTerms" type="checkbox" required>
        <label for="terms">
          I accept the <NuxtLink to="/terms" target="_blank">terms of use</NuxtLink>
          and have read the <NuxtLink to="/privacy" target="_blank">privacy policy</NuxtLink>.
          My contributions are licensed under <NuxtLink to="/license" target="_blank">CC BY-SA 4.0</NuxtLink>.
        </label>
      </div>
      <TurnstileWidget @token="captcha = $event" />
      <p><button type="submit" class="button" :disabled="busy">Register</button></p>
    </form>
  </div>
</template>
