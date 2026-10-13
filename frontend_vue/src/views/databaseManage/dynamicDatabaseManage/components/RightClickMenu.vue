<template>
  <div
    v-if="visible"
    class="context-menu"
    :style="{ left: x + 'px', top: y + 'px' }"
    @contextmenu.prevent
  >
    <div class="menu-item" @click="$emit('edit')">编辑单元格</div>
    <div class="menu-item" @click="$emit('copy')">复制</div>
    <div class="menu-item" @click="$emit('cut')">剪切</div>
    <div class="menu-item" :class="{ disabled: !canPaste }" @click="onPaste">粘贴</div>
    <div class="menu-item" @click="$emit('clear')">清除内容</div>
    <div class="menu-separator"></div>
    <div class="menu-item" @click="$emit('insert-above')">在上方插入行</div>
    <div class="menu-item" @click="$emit('insert-below')">在下方插入行</div>
    <div class="menu-separator"></div>
    <div class="menu-item danger" @click="$emit('delete-rows')">删除行</div>
  </div>
</template>

<script setup>
const props = defineProps({
  visible: { type: Boolean, default: false },
  x: { type: Number, default: 0 },
  y: { type: Number, default: 0 },
  canPaste: { type: Boolean, default: false }
})

const emit = defineEmits(['edit', 'copy', 'cut', 'paste', 'clear', 'insert-above', 'insert-below', 'delete-rows'])

function onPaste() {
  if (props.canPaste) emit('paste')
}
</script>

<style scoped>
.context-menu {
  position: fixed;
  background: white;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  z-index: 1000;
  min-width: 150px;
  padding: 4px 0;
}

.menu-item {
  padding: 8px 16px;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.menu-item:hover {
  background: #f0f0f0;
}

.menu-item.disabled {
  opacity: 0.5;
  pointer-events: none;
}

.menu-item.danger {
  color: #e53e3e;
}

.menu-item.danger:hover {
  background: #fed7d7;
}

.menu-separator {
  height: 1px;
  background: #e0e0e0;
  margin: 4px 0;
}
</style>
