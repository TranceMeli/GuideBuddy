<script setup lang="ts">
/**
 * The dialog of useConfirm(). It is a native <dialog> opened with showModal(), so focus stays
 * inside, Esc cancels and the page behind cannot be used. The safe button has the focus first.
 */
const { state, answer } = useConfirm()
const dialog = ref<HTMLDialogElement | null>(null)

watch(state, (options) => {
  const el = dialog.value
  if (!el) return
  if (options && !el.open) el.showModal()
  else if (!options && el.open) el.close()
}, { flush: 'post' }) // after the buttons are drawn, so the safe one can take the focus
</script>

<template>
  <dialog ref="dialog" class="confirm" aria-labelledby="confirm-title" aria-describedby="confirm-body" @cancel.prevent="answer(false)">
    <form v-if="state" method="dialog" class="confirm-box" @submit.prevent>
      <h2 id="confirm-title" class="confirm-title">{{ state.title }}</h2>
      <p v-if="state.body" id="confirm-body" class="confirm-body">{{ state.body }}</p>
      <div class="confirm-actions">
        <button type="button" class="btn btn-secondary" autofocus @click="answer(false)">{{ state.cancelLabel ?? 'Cancel' }}</button>
        <button type="button" class="btn" :class="state.danger ? 'btn-danger' : 'btn-primary'" @click="answer(true)">{{ state.confirmLabel ?? 'Continue' }}</button>
      </div>
    </form>
  </dialog>
</template>
