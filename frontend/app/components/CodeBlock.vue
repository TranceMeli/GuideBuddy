<script setup lang="ts">
/**
 * Code in JetBrains Mono with the language above it. variant "wrong"/"right" adds the
 * text label FALSCH:/RICHTIG: (coral/teal frame; the wrong
 * code is struck through).
 */
const props = defineProps<{ code: string; language?: string; variant?: 'wrong' | 'right'; copyable?: boolean }>()
const t = useGuideLabels()
const copied = ref(false)

async function copy() {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => (copied.value = false), 1500)
  } catch {
    // clipboard not available (insecure context): nothing to do
  }
}
</script>

<template>
  <figure class="code-block" :class="variant ? `code-block--${variant}` : undefined">
    <figcaption class="code-head" :lang="t.lang">
      <span v-if="variant" class="code-verdict">
        <GuideIcon :name="variant === 'wrong' ? 'close' : 'check'" :size="16" />
        {{ variant === 'wrong' ? t.wrong : t.right }}:
      </span>
      <span v-if="language" class="code-lang">{{ language }}</span>
      <button v-if="copyable" type="button" class="code-copy" @click="copy">
        <GuideIcon name="copy" :size="16" /> {{ copied ? `${t.copied} ✓` : t.copy }}
      </button>
    </figcaption>
    <pre><code>{{ code }}</code></pre>
  </figure>
</template>
