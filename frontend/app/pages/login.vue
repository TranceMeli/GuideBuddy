<script setup lang="ts">
useSeoMeta({ title: 'Sign in', robots: 'noindex' })

const route = useRoute()
const { login } = useAuth()

const username = ref('')
const password = ref('')
const errors = ref<string[]>([])
const fieldErrors = ref<Record<string, string[]>>({})
const errorBox = ref<HTMLElement | null>(null)
const needsVerification = ref(false)
const busy = ref(false)

async function submit() {
  errors.value = []
  needsVerification.value = false
  fieldErrors.value = {}
  if (!username.value.trim()) fieldErrors.value.username = ['Enter your user name.']
  if (!password.value) fieldErrors.value.password = ['Enter your password.']
  if (Object.keys(fieldErrors.value).length) {
    await nextTick()
    errorBox.value?.focus()
    return
  }
  busy.value = true
  try {
    await login(username.value, password.value)
    await navigateTo(safeNext(route.query.next))
  } catch (e) {
    needsVerification.value = apiErrorCode(e) === 'email_not_verified'
    errors.value = apiErrorMessages(e)
    await nextTick()
    errorBox.value?.focus()
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div>
    <h1>Sign in</h1>
    <form class="stack narrow" novalidate @submit.prevent="submit">
      <div v-if="errors.length || Object.keys(fieldErrors).length" ref="errorBox" class="error-box" role="alert" tabindex="-1">
        <ul>
          <li v-for="(messages, id) in fieldErrors" :key="id"><a :href="`#${id}`">{{ messages.join(' ') }}</a></li>
          <li v-for="m in errors" :key="m">{{ m }}</li>
        </ul>
        <p v-if="needsVerification">
          <NuxtLink to="/confirm">Request the confirmation link again</NuxtLink>
        </p>
      </div>
      <FormField id="username" label="User name" required :errors="fieldErrors.username">
        <template #default="{ field }">
          <input v-bind="field" v-model="username" type="text" autocomplete="username" required>
        </template>
      </FormField>
      <FormField id="password" label="Password" required :errors="fieldErrors.password">
        <template #default="{ field }">
          <input v-bind="field" v-model="password" type="password" autocomplete="current-password" required>
        </template>
      </FormField>
      <p><button type="submit" class="button" :disabled="busy">{{ busy ? 'Signing in …' : 'Sign in' }}</button></p>
    </form>
    <p><NuxtLink to="/forgot-password">Forgot your password?</NuxtLink></p>
    <p>No account yet? <NuxtLink to="/register">Register now</NuxtLink>.</p>
  </div>
</template>
