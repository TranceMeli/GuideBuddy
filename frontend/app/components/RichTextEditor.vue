<script setup lang="ts">
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import { TableKit } from '@tiptap/extension-table'
import { Placeholder } from '@tiptap/extensions'
import { MARK_NAME, textStyleMarks } from '~/utils/textStyleMarks'
import type { StyleKind } from '~/utils/textStyles'

/** Simple rich-text editor (TipTap). v-model is HTML. Text colour, highlight and font are
 *  picked from the fixed palette (utils/textStyles.ts). */
const props = defineProps<{ modelValue: string; labelledby?: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      underline: false, // Markdown has no underline
      link: { openOnClick: false, autolink: true, protocols: ['http', 'https', 'mailto'] },
    }),
    TableKit, // keep existing tables when editing
    ...textStyleMarks,
    Placeholder.configure({ placeholder: 'Write your guide here …' }),
  ],
  editorProps: {
    attributes: {
      class: 'prose rte-content',
      role: 'textbox',
      'aria-multiline': 'true',
      ...(props.labelledby ? { 'aria-labelledby': props.labelledby } : {}),
    },
  },
  onUpdate: ({ editor }) => emit('update:modelValue', editor.isEmpty ? '' : editor.getHTML()),
})

onBeforeUnmount(() => editor.value?.destroy())

function setLink() {
  const current = editor.value?.getAttributes('link').href as string | undefined
  const url = window.prompt('Link address (leave empty to remove):', current ?? 'https://')
  if (url === null) return
  const chain = editor.value?.chain().focus().extendMarkRange('link')
  if (!url.trim() || url.trim() === 'https://') chain?.unsetLink().run()
  else chain?.setLink({ href: url.trim() }).run()
}

// The styles at the cursor, for the menu
const currentStyles = computed(() => {
  const e = editor.value
  const result: Partial<Record<StyleKind, string | null>> = {}
  for (const kind of Object.keys(MARK_NAME) as StyleKind[]) result[kind] = e?.getAttributes(MARK_NAME[kind]).value ?? null
  return result
})
function applyStyle(kind: StyleKind, value: string | null) {
  const chain = editor.value?.chain().focus()
  if (!chain) return
  if (value) chain.setMark(MARK_NAME[kind], { value }).run()
  else chain.extendMarkRange(MARK_NAME[kind]).unsetMark(MARK_NAME[kind]).run()
}

type Tool = { label: string; title: string; active?: () => boolean; run: () => void }
const tools = computed<Tool[][]>(() => {
  const e = editor.value
  if (!e) return []
  return [
    [
      { label: 'Step', title: 'New step (large heading)', active: () => e.isActive('heading', { level: 2 }), run: () => e.chain().focus().toggleHeading({ level: 2 }).run() },
      { label: 'Subheading', title: 'Small heading', active: () => e.isActive('heading', { level: 3 }), run: () => e.chain().focus().toggleHeading({ level: 3 }).run() },
    ],
    [
      { label: 'B', title: 'Bold', active: () => e.isActive('bold'), run: () => e.chain().focus().toggleBold().run() },
      { label: 'I', title: 'Italic', active: () => e.isActive('italic'), run: () => e.chain().focus().toggleItalic().run() },
      { label: 'Link', title: 'Insert link', active: () => e.isActive('link'), run: setLink },
    ],
    [
      { label: '• List', title: 'Bulleted list', active: () => e.isActive('bulletList'), run: () => e.chain().focus().toggleBulletList().run() },
      { label: '1. List', title: 'Numbered list', active: () => e.isActive('orderedList'), run: () => e.chain().focus().toggleOrderedList().run() },
      { label: '❝ Quote', title: 'Quote or note', active: () => e.isActive('blockquote'), run: () => e.chain().focus().toggleBlockquote().run() },
      { label: '</> Code', title: 'Code block', active: () => e.isActive('codeBlock'), run: () => e.chain().focus().toggleCodeBlock().run() },
    ],
    [
      { label: '↶', title: 'Undo', run: () => e.chain().focus().undo().run() },
      { label: '↷', title: 'Redo', run: () => e.chain().focus().redo().run() },
    ],
  ]
})
</script>

<template>
  <div class="rte">
    <div class="rte-toolbar" role="toolbar" aria-label="Text format">
      <span v-for="(group, g) in tools" :key="g" class="rte-group">
        <button
          v-for="tool in group"
          :key="tool.title"
          type="button"
          :title="tool.title"
          :aria-label="tool.title"
          :aria-pressed="tool.active ? tool.active() : undefined"
          :class="{ 'is-active': tool.active?.() }"
          @mousedown.prevent
          @click="tool.run"
        >
          {{ tool.label }}
        </button>
      </span>
      <TextStyleMenu :current="currentStyles" @apply="applyStyle" />
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>
