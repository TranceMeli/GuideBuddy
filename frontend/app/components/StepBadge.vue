<script setup lang="ts">
/**
 * Number badge of a step: 40px square, radius 10px.
 * active = filled (royal blue / black), done = check icon, open = frame only.
 */
withDefaults(defineProps<{ number: number; state?: 'active' | 'done' | 'open'; small?: boolean }>(), {
  state: 'active',
})
</script>

<template>
  <span class="step-badge" :class="[`is-${state}`, { 'is-small': small }]" aria-hidden="true">
    <GuideIcon v-if="state === 'done'" name="check" :size="small ? 16 : 22" />
    <template v-else>{{ number }}</template>
  </span>
</template>
