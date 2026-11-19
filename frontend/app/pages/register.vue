<script setup lang="ts">
useSeoMeta({ title: 'Register', robots: 'noindex' })

const username = ref('')
const email = ref('')
const password = ref('')
const acceptTerms = ref(false)
const website = ref('') // Honeypot: people do not see this field
const captcha = ref('')
const errors = ref<string[]>([])
const fieldErrors = ref<Record<string, string[]>>({})
const errorBox = ref<HTMLElement | null>(null)
const done = ref('')
const busy = ref(false)
const dev = import.meta.dev

const MIN_PASSWORD = 8

/** What can be checked before asking the server, with the same words the server would use */
function checkInputs(): Record<string, string[]> {
  const found: Record<string, string[]> = {}
  if (!username.value.trim()) found.username = ['Enter a user name.']
  if (!/^\S+@\S+\.\S+$/.test(email.value.trim())) found.email = ['Enter an address like name@example.com.']
  if (password.value.length < MIN_PASSWORD) {
    found.password = [`Your password has ${password.value.length} of ${MIN_PASSWORD} characters. Add ${MIN_PASSWORD - password.value.length} more.`]
  }
  if (!acceptTerms.value) found.accept_terms = ['Accept the terms of use to register.']
  return found
}

// Short list on top (with links to the fields) so nothing is missed, the details under each field
const summary = computed(() => Object.entries(fieldErrors.value).map(([id, messages]) => ({ id, text: messages.join(' ') })))
async function showProblems() {
  await nextTick()
  errorBox.value?.focus()
}

async function submit() {
  errors.value = []
  fieldErrors.value = checkInputs()
  if (Object.keys(fieldErrors.value).length) return showProblems()
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
    const split = apiFieldErrors(e, ['username', 'email', 'password', 'accept_terms'])
    fieldErrors.value = split.fields
    errors.value = split.other
    await showProblems()
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

    <form v-else class="stack narrow" novalidate @submit.prevent="submit">
      <div v-if="errors.length || summary.length" ref="errorBox" class="error-box" role="alert" tabindex="-1">
        <p v-if="summary.length" class="error-title">{{ summary.length === 1 ? 'One field needs your attention' : `${summary.length} fields need your attention` }}</p>
        <ul>
          <li v-for="item in summary" :key="item.id"><a :href="`#${item.id === 'accept_terms' ? 'terms' : item.id}`">{{ item.text }}</a></li>
          <li v-for="m in errors" :key="m">{{ m }}</li>
        </ul>
      </div>
      <FormField id="username" label="User name" required help="It is shown publicly in the history of your changes." :errors="fieldErrors.username">
        <template #default="{ field }">
          <input v-bind="field" v-model="username" type="text" autocomplete="username" required>
        </template>
      </FormField>
      <FormField id="email" label="E-mail" required help="Never published. You will receive a confirmation link." :errors="fieldErrors.email">
        <template #default="{ field }">
          <input v-bind="field" v-model="email" type="email" autocomplete="email" required>
        </template>
      </FormField>
      <FormField id="password" label="Password" required help="At least 8 characters, not only digits, not a common password." :errors="fieldErrors.password">
        <template #default="{ field }">
          <input v-bind="field" v-model="password" type="password" autocomplete="new-password" required>
        </template>
      </FormField>
      <div class="hp" aria-hidden="true">
        <label for="website">Website (please leave empty)</label>
        <input id="website" v-model="website" type="text" tabindex="-1" autocomplete="off">
      </div>
      <div class="check" :class="{ 'has-error': fieldErrors.accept_terms }">
        <input id="terms" v-model="acceptTerms" type="checkbox" required :aria-invalid="fieldErrors.accept_terms ? 'true' : undefined" :aria-describedby="fieldErrors.accept_terms ? 'terms-error' : undefined">
        <label for="terms">
          I accept the <NuxtLink to="/terms" target="_blank">terms of use</NuxtLink>
          and have read the <NuxtLink to="/privacy" target="_blank">privacy policy</NuxtLink>.
          My contributions are licensed under <NuxtLink to="/license" target="_blank">CC BY-SA 4.0</NuxtLink>.
        </label>
      </div>
      <p v-if="fieldErrors.accept_terms" id="terms-error" class="field-error"><GuideIcon name="alert" :size="16" /> <span>{{ fieldErrors.accept_terms.join(' ') }}</span></p>
      <TurnstileWidget @token="captcha = $event" />
      <p><button type="submit" class="button" :disabled="busy">{{ busy ? 'Creating account …' : 'Create account' }}</button></p>
    </form>
  </div>
</template>
