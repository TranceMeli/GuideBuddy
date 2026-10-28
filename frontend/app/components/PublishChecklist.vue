<script setup lang="ts">
import type { Check } from '~/utils/publishChecks'

/** "Before you publish": the checks of publishChecks.ts as a folded list. Advice only. */
const props = defineProps<{ checks: Check[] }>()
const passed = computed(() => props.checks.filter((c) => c.ok).length)
</script>

<template>
  <details class="publish-checks">
    <summary>
      <span>Before you publish</span>
      <span class="publish-checks-count" :class="{ 'is-complete': passed === checks.length }">{{ passed }} of {{ checks.length }} checks passed</span>
    </summary>
    <ul class="publish-checks-list">
      <li v-for="check in checks" :key="check.id" :class="check.ok ? 'is-ok' : 'is-open'">
        <span class="publish-checks-mark" aria-hidden="true">{{ check.ok ? '✓' : '!' }}</span>
        <span>
          {{ check.label }}<span class="visually-hidden">: {{ check.ok ? 'done' : 'to do' }}</span>
          <small v-if="!check.ok">{{ check.hint }}</small>
        </span>
      </li>
    </ul>
    <p class="muted small">These checks only advise; you can always publish.</p>
  </details>
</template>
