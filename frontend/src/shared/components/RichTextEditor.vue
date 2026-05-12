<script setup lang="ts">
import { onBeforeUnmount, ref, shallowRef, watch } from 'vue'
import { Editor, Toolbar } from '@wangeditor/editor-for-vue'
import type { IDomEditor, IEditorConfig, IToolbarConfig } from '@wangeditor/editor'
import '@wangeditor/editor/dist/css/style.css'
import api from '@/shared/http/client'

interface Props {
  modelValue: string
  placeholder?: string
  disabled?: boolean
}
const props = defineProps<Props>()
const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const editorRef = shallowRef<IDomEditor | null>(null)
const html = ref<string>(props.modelValue ?? '')

watch(
  () => props.modelValue,
  (v) => {
    if (v !== html.value) html.value = v ?? ''
  },
)

const toolbarConfig: Partial<IToolbarConfig> = {
  toolbarKeys: [
    'headerSelect',
    'bold', 'italic', 'underline',
    '|',
    'bulletedList', 'numberedList',
    'blockquote',
    '|',
    'insertLink', 'insertImage',
    '|',
    'clearStyle',
  ],
}

const editorConfig: Partial<IEditorConfig> = {
  placeholder: props.placeholder ?? 'Write something…',
  MENU_CONF: {
    uploadImage: {
      async customUpload(file: File, insertFn: (url: string) => void) {
        const data = new FormData()
        data.append('file', file)
        const res = await api.post<{ url: string }>('/api/media/upload/', data, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        insertFn(res.data.url)
      },
    },
  },
}

const handleCreated = (editor: IDomEditor) => {
  editorRef.value = editor
}

const handleChange = (editor: IDomEditor) => {
  const next = editor.getHtml()
  html.value = next
  emit('update:modelValue', next)
}

onBeforeUnmount(() => {
  editorRef.value?.destroy()
  editorRef.value = null
})
</script>

<template>
  <div class="rich-text-editor" :class="{ 'is-disabled': disabled }">
    <Toolbar :editor="editorRef" :default-config="toolbarConfig" mode="default" />
    <Editor
      v-model="html"
      :default-config="editorConfig"
      :mode="'default'"
      :default-html="modelValue"
      style="height: 480px; overflow-y: auto; width: 100%"
      @on-created="handleCreated"
      @on-change="handleChange"
    />
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 1px solid #d0d7e2;
  border-radius: 10px;
  overflow: hidden;
  width: 100%;
}
.rich-text-editor :deep(.w-e-text-container) {
  width: 100% !important;
}
.rich-text-editor :deep(.w-e-toolbar) {
  width: 100% !important;
}
.rich-text-editor.is-disabled {
  opacity: 0.6;
  pointer-events: none;
}
</style>
