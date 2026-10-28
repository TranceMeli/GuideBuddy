<script setup lang="ts">
useSeoMeta({ title: 'Sign in', robots: 'noindex' })

const route = useRoute()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const errors = ref<string[]>([])
const needsVerification = ref(false)
const busy = ref(false)

async function submit() {
  errors.value = []
  needsVerification.value = false
  busy.value = true
  try {
    await login(username.value, password.value)
    await navigateTo(safeNext(route.query.next))
  } catch (e) {
    needsVerification.value = apiErrorCode(e) === 'email_not_verified'
    errors.value = apiErrorMessages(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <h1>Sign in</h1>
    <form class="stack narrow" @submit.prevent="submit">
      <div v-if="errors.length" class="error-box" role="alert">
        <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
        <p v-if="needsVerification">
          <NuxtLink to="/confirm">Request the confirmation link again</NuxtLink>
        </p>
      </div>
      <div>
        <label for="username">User name</label>
        <input id="username" v-model="username" type="text" autocomplete="username" required>
      </div>
      <div>
        <label for="password">Password</label>
        <input id="password" v-model="password" type="password" autocomplete="current-password" required>
      </div>
      <p><button type="submit" class="button" :disabled="busy">Sign in</button></p>
    </form>
    <p><NuxtLink to="/forgot-password">Forgot your password?</NuxtLink></p>
    <p>No account yet? <NuxtLink to="/register">Register now</NuxtLink>.</p>
  </div>
</template>
