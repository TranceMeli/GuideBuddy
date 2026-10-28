<script setup lang="ts">
import type { Guide } from '~/types/guide'

/**
 * Reading view of a guide: picks the template for its type and provides the labels in the
 * guide's language to everything inside. Used on the guide page and for the editor
 * preview (preview: no PDF, no saved progress, no feedback).

 */
const props = defineProps<{
  guide: Guide
  preview?: boolean
  locked?: boolean
  /** Template gallery: sample data, shown like a real page (collapsed steps, some done) */
  sample?: boolean
}>()

const labels = computed(() => labelsFor(props.guide.language))
provide(GUIDE_LABELS_KEY, labels)
const { printVersion } = useTheme()

const count = computed(() => {
  const g = props.guide
  return g.guide_type === 'page' ? g.elements.filter((e) => e.kind === 'step').length : g.steps.length
})
const pdfUrl = computed(() => `${usePublicApiBase()}/guides/${props.guide.slug}/pdf/`)
// The PDF is built from the flat step list (see the API)
const hasPdf = computed(() => (!props.preview || props.sample) && (props.guide.steps.length > 0 || props.guide.elements.length > 0))
</script>

<template>
  <article class="reader" :class="`reader-${guide.guide_type}`" :lang="guide.language || 'en'">
      <GuideBar />
      <GuideHeader :guide="guide" :count="count" :locked="locked">
        <template #actions>
          <a v-if="hasPdf" class="btn btn-secondary" :href="sample ? undefined : pdfUrl">
            <GuideIcon name="download" :size="18" /> {{ labels.downloadPdf }}
          </a>
          <a v-if="guide.attachment_info && !preview" class="btn btn-secondary" :href="guide.attachment_info.download_url" download>
            <GuideIcon name="download" :size="18" />
            {{ guide.steps.length ? labels.attachment : labels.download }}: {{ guide.attachment_info.name }}
          </a>
          <button v-if="!preview || sample" type="button" class="btn btn-ghost" @click="printVersion">
            <GuideIcon name="printer" :size="18" /> {{ labels.printVersion }}
          </button>
        </template>
        <template v-if="$slots.tools" #tools><slot name="tools" /></template>
      </GuideHeader>

      <ElementsReader v-if="guide.guide_type === 'page'" :guide="guide" :preview="preview" />
      <FreeReader v-else :guide="guide" :preview="preview" />
  </article>
</template>
