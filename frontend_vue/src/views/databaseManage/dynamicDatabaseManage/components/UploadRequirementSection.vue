<template>
  <div class="upload-section">
    <h3>需求文档</h3>
    <el-upload
      ref="requirementUpload"
      class="upload-demo compact"
      drag
      :before-upload="beforeUpload"
      :file-list="fileList"
      :on-remove="onRemove"
      :disabled="disabled"
      accept=".docx"
      :multiple="false">
      <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
      <div class="el-upload__text">
        <span v-if="!requirementUploaded">拖拽需求文档到此处，或<em>点击上传</em></span>
        <span v-else>需求文档已上传</span>
      </div>
      <template #tip>
        <div class="el-upload__tip">
          仅支持 .docx 格式，文件大小不超过 50MB
        </div>
      </template>
    </el-upload>

    <!-- 需求文档上传状态显示 -->
    <div v-if="requirementUploaded" class="upload-status success">
      <el-icon class="status-icon"><CircleCheck /></el-icon>
      <span class="status-text">需求文档上传成功：{{ fileInfo?.name }}</span>
      <span class="file-size">({{ formatFileSize(fileInfo?.size || 0) }})</span>
    </div>
  </div>
</template>

<script setup>
import { UploadFilled, CircleCheck } from '@element-plus/icons-vue'

const props = defineProps({
  fileList: { type: Array, required: true },
  disabled: { type: Boolean, default: false },
  requirementUploaded: { type: Boolean, default: false },
  fileInfo: { type: Object, default: null },
  formatFileSize: { type: Function, required: true },
  beforeUpload: { type: Function, required: true },
  onRemove: { type: Function, required: true },
})
</script>

<style scoped>
.upload-section {
  margin-bottom: 16px;
}
.upload-status {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #16a34a;
  margin-top: 8px;
}
.status-icon { color: #22c55e; }
.file-size { color: #64748b; }
</style>
