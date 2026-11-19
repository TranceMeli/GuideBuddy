<script setup lang="ts">
/**
 * One labelled form field: the label says whether the field is required, the help text says what
 * to enter, and an error sits right under the field with an icon and words (never colour alone).
 * The input gets its aria attributes through the slot: `<input v-bind="field" ...>`.
 */
const props = defineProps<{ id: string; label: string; required?: boolean; help?: string; errors?: string[] }>()

const invalid = computed(() => Boolean(props.errors?.length))
const field = computed(() => ({
  id: props.id,
  'aria-invalid': invalid.value ? (true as const) : undefined,
  'aria-describedby': [props.help ? `${props.id}-help` : '', invalid.value ? `${props.id}-error` : ''].filter(Boolean).join(' ') || undefined,
}))
</script>

<template>
  <div class="field" :class="{ 'has-error': invalid }">
    <label :for="id">{{ label }} <span v-if="required" class="field-req">(required)</span></label>
    <slot :field="field" />
    <p v-if="help" :id="`${id}-help`" class="field-help">{{ help }}</p>
    <p v-if="invalid" :id="`${id}-error`" class="field-error"><GuideIcon name="alert" :size="16" /> <span>{{ errors!.join(' ') }}</span></p>
  </div>
</template>
