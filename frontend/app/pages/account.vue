<script setup lang="ts">
definePageMeta({ middleware: 'auth' })
useSeoMeta({ title: 'My account', robots: 'noindex' })

const { user, clearSession } = useAuth()
const password = ref('')
const errors = ref<string[]>([])
const busy = ref(false)

async function deleteAccount() {
  if (!confirm('Really delete your account for good?')) return
  errors.value = []
  busy.value = true
  try {
    await $fetch<unknown>('/api/auth/account', { method: 'DELETE', body: { password: password.value } })
    user.value = null
    clearNuxtData()
    await navigateTo('/')
  } catch (e) {
    if ((e as { statusCode?: number }).statusCode === 401) {
      await clearSession()
      await navigateTo('/login')
      return
    }
    errors.value = apiErrorMessages(e)
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div v-if="user">
    <h1>My account</h1>
    <dl>
      <dt>User name</dt><dd>{{ user.username }}</dd>
      <dt>E-mail</dt><dd>{{ user.email }}</dd>
      <dt>Role</dt><dd>{{ user.is_moderator ? 'Moderator' : 'Author' }}</dd>
    </dl>
    <p v-if="!user.can_write" class="hint-box" role="status">{{ user.write_hint }}</p>

    <section class="danger-zone">
      <h2>Delete account</h2>
      <p>
        Your account and your e-mail address are deleted. Your contributions stay as part of the
        community content (CC BY-SA 4.0), but are no longer linked to you.
      </p>
      <form class="stack narrow" @submit.prevent="deleteAccount">
        <div v-if="errors.length" class="error-box" role="alert">
          <ul><li v-for="m in errors" :key="m">{{ m }}</li></ul>
        </div>
        <div>
          <label for="password">Password to confirm</label>
          <input id="password" v-model="password" type="password" autocomplete="current-password" required>
        </div>
        <p><button type="submit" class="danger-btn" :disabled="busy">Delete account for good</button></p>
      </form>
    </section>
  </div>
</template>
