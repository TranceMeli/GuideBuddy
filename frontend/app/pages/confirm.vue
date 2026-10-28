<script setup lang="ts">
useSeoMeta({ title: 'Confirm e-mail', robots: 'noindex' })

const route = useRoute()
const uid = String(route.query.uid ?? '')
const token = String(route.query.token ?? '')

const state = ref<'idle' | 'working' | 'ok' | 'failed'>(uid && token ? 'working' : 'idle')
const message = ref('')
const email = ref('')
const resent = ref('')
const errors = ref<string[]>([])

onMounted(async () => {
  if (state.value !== 'working') return
  try {
    const result = await $fetch<{ detail: string }>('/api/auth/verify/', {
      method: 'POST',
      body: { uid, token },
    })
    message.value = result.detail
    state.value = 'ok'
  } catch (e) {
    message.value = apiErrorMessages(e).join(' ')
    state.value = 'failed'
  }
})

async function resend() {
  errors.value = []
  try {
    const result = await $fetch<{ detail: string }>('/api/auth/resend/', {
      method: 'POST',
      body: { email: email.value },
    })
    resent.value = result.detail
  } catch (e) {
    errors.value = apiErrorMessages(e)
  }
}
</script>

<template>
  <div>
    <h1>Confirm your e-mail address</h1>
    <p v-if="state === 'working'" role="status">One moment, checking your link …</p>
    <div v-else-if="state === 'ok'" class="ok-box" role="status">
      <p>{{ message }}</p>
      <p><NuxtLink class="button" to="/login">Go to sign in</NuxtLink></p>
    </div>
    <template v-else>
      <div v-if="state === 'failed'" class="error-box" role="alert">{{ message }}</div>
      <p>Request a new confirmation link:</p>
      <div v-if="resent" class="ok-box" role="status">
        <p>{{ resent }}</p>
        <p v-if="$config.public.siteUrl.startsWith('http://localhost')" class="muted">
          Development: the link is shown in the terminal of the Django server.
        </p>
      </div>
      <form v-else class="stack narrow" @submit.prevent="resend">
        <div v-if="errors.length" class="error-box" role="alert">
          <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
        </div>
        <div>
          <label for="email">E-mail</label>
          <input id="email" v-model="email" type="email" autocomplete="email" required>
        </div>
        <p><button type="submit" class="button">Send link</button></p>
      </form>
    </template>
  </div>
</template>
