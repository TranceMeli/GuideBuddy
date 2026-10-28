<script setup lang="ts">
import type { GuideImage, ImageKind } from '~/types/guide'

/** Uploads one image (POST /api/images/, alt text required) and keeps its reference. */
const model = defineModel<GuideImage | null>({ required: true })
const props = defineProps<{ id: string }>()

const MAX_BYTES = 5 * 1024 * 1024
const file = ref<File | null>(null)
const alt = ref('')
const caption = ref('')
const currentCaption = computed(() => {
  const image = model.value
  if (!image) return ''
  const label = image.kind ? IMAGE_KINDS.find((k) => k.value === image.kind)?.label : ''
  return [label, image.caption].filter(Boolean).join(': ')
})
const kind = ref<ImageKind>('')
const error = ref('')
const uploading = ref(false)
const fileInput = ref<HTMLInputElement | null>(null)

function choose(event: Event) {
  error.value = ''
  const chosen = (event.target as HTMLInputElement).files?.[0] ?? null
  if (chosen && !/\.(png|jpe?g|gif|webp)$/i.test(chosen.name)) {
    error.value = 'Allowed formats are PNG, JPEG, GIF and WebP.'
    file.value = null
  } else if (chosen && chosen.size > MAX_BYTES) {
    error.value = 'The image must be 5 MB or smaller.'
    file.value = null
  } else {
    file.value = chosen
  }
}

async function upload() {
  if (!file.value) return
  if (!alt.value.trim()) {
    error.value = 'Please briefly describe what the image shows.'
    return
  }
  error.value = ''
  uploading.value = true
  const body = new FormData()
  body.append('file', file.value)
  body.append('alt', alt.value.trim())
  body.append('caption', caption.value.trim())
  body.append('kind', kind.value)
  try {
    model.value = await $fetch<GuideImage>('/api/images/', { method: 'POST', body })
    file.value = null
    alt.value = ''
    caption.value = ''
    kind.value = ''
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    error.value = apiErrorMessages(e).join(' ')
  } finally {
    uploading.value = false
  }
}
</script>

<template>
  <div class="image-picker">
    <figure v-if="model" class="image-picker-current">
      <img :src="model.url" :alt="model.alt" :width="model.width" :height="model.height" loading="lazy">
      <figcaption>
        <span class="muted small">Alt text: {{ model.alt }}</span>
        <span v-if="currentCaption" class="muted small">
          {{ currentCaption }}
        </span>
        <button type="button" class="link-button danger" @click="model = null">Remove image</button>
      </figcaption>
    </figure>
    <div v-else class="image-picker-upload">
      <div>
        <label :for="`${props.id}-file`">Image <span class="muted">(optional, PNG/JPEG/GIF/WebP, max. 5 MB)</span></label>
        <input :id="`${props.id}-file`" ref="fileInput" type="file" accept="image/png,image/jpeg,image/gif,image/webp" @change="choose">
      </div>
      <div v-if="file">
        <label :for="`${props.id}-alt`">What does the image show? <span class="muted">(alt text, required)</span></label>
        <input :id="`${props.id}-alt`" v-model="alt" type="text" maxlength="200" placeholder="e.g. Open quick release on the front wheel">
      </div>
      <div v-if="file" class="field-row">
        <div>
          <label :for="`${props.id}-kind`">What kind of image is it? <span class="muted">(optional)</span></label>
          <select :id="`${props.id}-kind`" v-model="kind">
            <option value="">not specified</option>
            <option v-for="k in IMAGE_KINDS" :key="k.value" :value="k.value">{{ k.label }}</option>
          </select>
        </div>
        <div>
          <label :for="`${props.id}-caption`">Caption <span class="muted">(optional)</span></label>
          <input :id="`${props.id}-caption`" v-model="caption" type="text" maxlength="200" placeholder="e.g. The result in the browser">
        </div>
      </div>
      <p v-if="file && kind === 'mockup'" class="muted small">A mockup is a drawn, schematic screen. Only call an image a screenshot if it really is one.</p>
      <p v-if="file">
        <button type="button" class="secondary" :disabled="uploading" @click="upload">
          {{ uploading ? 'Uploading …' : 'Upload image' }}
        </button>
      </p>
    </div>
    <p v-if="error" class="error-box" role="alert">{{ error }}</p>
  </div>
</template>
