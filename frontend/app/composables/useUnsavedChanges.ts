import type { Ref } from 'vue'

/**
 * Warns before unsaved editor changes get lost: leaving the page inside the app asks first,
 * closing or reloading the tab shows the browser's own warning. `source` returns everything
 * the author can change; any change after the editor has settled marks the page as dirty.
 * Call markSaved() right before navigating away after a successful save.
 */
export function useUnsavedChanges(source: () => unknown): { dirty: Ref<boolean>; markSaved: () => void } {
  const dirty = ref(false)
  let armed = false

  // Rich text and list fields normalise their content once after mounting; only changes
  // after that count as the author's
  onMounted(() => setTimeout(() => (armed = true), 500))
  watch(source, () => {
    if (armed) dirty.value = true
  }, { deep: true })

  function onBeforeUnload(event: BeforeUnloadEvent) {
    if (!dirty.value) return
    event.preventDefault()
    event.returnValue = ''
  }
  onMounted(() => window.addEventListener('beforeunload', onBeforeUnload))
  onBeforeUnmount(() => window.removeEventListener('beforeunload', onBeforeUnload))

  onBeforeRouteLeave(() => {
    if (dirty.value && !confirm('You have unsaved changes. Leave this page anyway?')) return false
  })

  return { dirty, markSaved: () => (dirty.value = false) }
}
