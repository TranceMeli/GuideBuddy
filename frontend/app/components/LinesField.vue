<script setup lang="ts">
/** A short list of texts, edited as one line per item. */
const model = defineModel<string[]>({ required: true })
const props = defineProps<{ id: string; label: string; maxItems: number; maxLength: number; placeholder?: string }>()

const text = ref(model.value.join('\n'))
const tooMany = computed(() => linesToList(text.value).length > props.maxItems)
const tooLong = computed(() => linesToList(text.value).some((line) => line.length > props.maxLength))
watch(text, (value) => {
  model.value = linesToList(value)
})
</script>

<template>
  <div>
    <label :for="id">{{ label }} <span class="muted">(optional, one line per item)</span></label>
    <textarea :id="id" v-model="text" rows="3" :placeholder="placeholder" :aria-describedby="`${id}-hint`" />
    <p :id="`${id}-hint`" class="field-meta" :class="{ 'is-error': tooMany || tooLong }">
      <span v-if="tooMany">At most {{ maxItems }} items.</span>
      <span v-else-if="tooLong">At most {{ maxLength }} characters per line.</span>
      <span v-else>Up to {{ maxItems }} items.</span>
    </p>
  </div>
</template>
