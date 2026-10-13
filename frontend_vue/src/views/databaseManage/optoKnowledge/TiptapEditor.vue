<template>
  <div class="tt-wrap">
    <div class="tt-toolbar">
      <el-button size="small" @click="toggleBold" :disabled="!editor">加粗</el-button>
      <el-button size="small" @click="toggleItalic" :disabled="!editor">斜体</el-button>
      <el-button size="small" @click="setParagraph" :disabled="!editor">正文</el-button>
      <el-button size="small" @click="setH2" :disabled="!editor">标题</el-button>
      <el-button size="small" @click="undo" :disabled="!editor">撤销</el-button>
      <el-button size="small" @click="redo" :disabled="!editor">重做</el-button>

      <el-upload
        class="tt-upload"
        :show-file-list="false"
        accept="image/*"
        :auto-upload="false"
        :on-change="handleImageChange"
      >
        <el-button size="small" type="primary" :disabled="!editor || uploading">插入图片</el-button>
      </el-upload>

      <div class="spacer"></div>
      <el-button size="small" type="success" @click="emitSave" :loading="saving" :disabled="!editor">保存</el-button>
    </div>

    <EditorContent class="tt-content" :editor="editor" />
  </div>
</template>

<script setup>
import { onBeforeUnmount, watch } from 'vue'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps({
  modelValue: { type: Object, default: null },
  saving: { type: Boolean, default: false },
  uploading: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'save', 'upload-image'])

const editor = useEditor({
  extensions: [
    StarterKit,
    Image.configure({ inline: false, allowBase64: true }),
    Placeholder.configure({ placeholder: '在这里编写知识内容…' })
  ],
  content: props.modelValue || { type: 'doc', content: [{ type: 'paragraph' }] },
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getJSON())
  }
})

watch(
  () => props.modelValue,
  (v) => {
    if (!editor.value) return
    // 避免循环更新
    const current = editor.value.getJSON()
    const same = JSON.stringify(current) === JSON.stringify(v || { type: 'doc', content: [{ type: 'paragraph' }] })
    if (!same) {
      editor.value.commands.setContent(v || { type: 'doc', content: [{ type: 'paragraph' }] })
    }
  }
)

onBeforeUnmount(() => {
  if (editor.value) editor.value.destroy()
})

function toggleBold() {
  editor.value?.chain().focus().toggleBold().run()
}
function toggleItalic() {
  editor.value?.chain().focus().toggleItalic().run()
}
function setParagraph() {
  editor.value?.chain().focus().setParagraph().run()
}
function setH2() {
  editor.value?.chain().focus().toggleHeading({ level: 2 }).run()
}
function undo() {
  editor.value?.chain().focus().undo().run()
}
function redo() {
  editor.value?.chain().focus().redo().run()
}

function emitSave() {
  emit('save')
}

function handleImageChange(uploadFile) {
  const file = uploadFile?.raw
  if (!file) return
  emit('upload-image', {
    file,
    insert: (src) => {
      editor.value?.chain().focus().setImage({ src }).run()
    }
  })
}
</script>

<style scoped>
.tt-wrap {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tt-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 10px;
  border: 1px solid rgba(130, 220, 255, 0.12);
  border-radius: 10px;
  background: rgba(8, 10, 18, 0.55);
}

.tt-upload {
  display: inline-flex;
}

.spacer {
  flex: 1;
}

.tt-content {
  margin-top: 12px;
  flex: 1;
  overflow: auto;
  padding: 12px 12px;
  border-radius: 10px;
  border: 1px solid rgba(130, 220, 255, 0.12);
  background: rgba(6, 8, 14, 0.35);
}

.tt-content :deep(.ProseMirror) {
  outline: none;
  color: rgba(235, 247, 255, 0.92);
}

.tt-content :deep(.ProseMirror h2) {
  margin: 16px 0 8px;
  font-size: 16px;
  color: rgba(200, 245, 255, 0.95);
}

.tt-content :deep(.ProseMirror p) {
  line-height: 1.8;
}

.tt-content :deep(img) {
  max-width: 100%;
  border-radius: 8px;
  border: 1px solid rgba(130, 220, 255, 0.16);
}
</style>
