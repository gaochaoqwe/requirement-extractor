<template>
  <div class="outline-rewriter-container">
    <div class="main-container">
      <div class="header">
        <h2>鉴定测评大纲二次编写工具</h2>
        <p>上传大纲 docx，填写各章节补充说明，AI 自动生成正文内容并输出新文档</p>
      </div>

      <!-- 步骤一：上传文件 -->
      <div class="step-section" v-if="currentStep === 'upload'">
        <div class="upload-area">
          <el-upload
            class="docx-uploader"
            drag
            :auto-upload="false"
            :multiple="false"
            accept=".docx"
            :on-change="onFileChange"
            :show-file-list="true"
            :limit="1"
            :on-exceed="onExceed"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将 .docx 文件拖到此处，或 <em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">仅支持 .docx 格式，文件大小不超过 50MB</div>
            </template>
          </el-upload>
        </div>

        <div class="upload-actions">
          <el-button
            type="primary"
            size="large"
            :loading="parsing"
            :disabled="!selectedFile"
            @click="parseOutline"
          >
            {{ parsing ? '正在解析...' : '解析大纲结构' }}
          </el-button>
        </div>
      </div>

      <!-- 步骤二：勾选章节并填写补充说明 -->
      <div class="step-section" v-if="currentStep === 'fill'">
        <div class="doc-info">
          <el-tag type="info" size="large">
            文档标题：{{ documentTitle || '（未识别到标题）' }}
          </el-tag>
          <el-tag type="success" size="large" style="margin-left: 12px">
            共 {{ sections.length }} 个章节
          </el-tag>
          <el-tag type="warning" size="large" style="margin-left: 12px">
            已选 {{ selectedCount }} 个
          </el-tag>
        </div>

        <!-- 工具栏：全选 / 取消全选 -->
        <div class="toolbar">
          <el-checkbox
            :model-value="isAllSelected"
            :indeterminate="isIndeterminate"
            @change="toggleSelectAll"
          >
            {{ isAllSelected ? '取消全选' : '全选' }}
          </el-checkbox>
          <span class="toolbar-tip">勾选需要 AI 编写内容的章节，未勾选章节将保持原样</span>
        </div>

        <div class="sections-list">
          <div
            v-for="sec in sections"
            :key="sec.paragraphIndex"
            class="section-item"
            :class="['level-' + sec.level, { 'is-selected': selectedSet[sec.paragraphIndex] }]"
            @click="toggleSection(sec.paragraphIndex)"
          >
            <div class="section-header">
              <el-checkbox
                :model-value="!!selectedSet[sec.paragraphIndex]"
                @click.stop
                @change="toggleSection(sec.paragraphIndex)"
                class="section-checkbox"
              />
              <el-tag :type="levelTagType(sec.level)" size="small" class="level-tag">
                {{ sec.level }} 级
              </el-tag>
              <span class="section-title">
                <span v-if="sec.numberText" class="number-text">{{ sec.numberText }}</span>
                {{ sec.titleText }}
              </span>
            </div>
            <!-- 只有选中的章节才展开补充说明输入框 -->
            <div v-if="selectedSet[sec.paragraphIndex]" class="extra-area" @click.stop>
              <el-input
                v-model="sectionExtras[sec.paragraphIndex]"
                type="textarea"
                :rows="2"
                :placeholder="`为「${sec.titleText}」填写补充说明（可选）`"
                class="section-extra-input"
              />
            </div>
          </div>
        </div>

        <div class="fill-actions">
          <el-button @click="resetToUpload" :disabled="generating">重新上传</el-button>
          <el-button
            type="primary"
            size="large"
            :loading="generating"
            :disabled="selectedCount === 0"
            @click="generateOutline"
          >
            <span v-if="generating">正在生成（{{ generatedCount }}/{{ selectedCount }}）...</span>
            <span v-else>AI 生成选中章节（{{ selectedCount }} 个）并下载</span>
          </el-button>
        </div>

        <div class="progress-area" v-if="generating">
          <el-progress
            :percentage="selectedCount > 0 ? Math.round((generatedCount / selectedCount) * 100) : 0"
            :stroke-width="10"
            status="striped"
            striped-flow
          />
          <p class="progress-tip">正在逐章节调用 AI 生成内容，请耐心等待...</p>
        </div>
      </div>

      <!-- 步骤三：完成 -->
      <div class="step-section result-section" v-if="currentStep === 'done'">
        <el-result icon="success" title="生成完成" sub-title="新大纲文档已自动下载到您的浏览器">
          <template #extra>
            <el-button type="primary" @click="resetToUpload">处理新文档</el-button>
          </template>
        </el-result>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, reactive, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = '/api/test-tools/outline-rewriter'

export default {
  name: 'OutlineRewriter',
  components: { UploadFilled },

  setup() {
    const currentStep = ref('upload')
    const parsing = ref(false)
    const generating = ref(false)
    const generatedCount = ref(0)

    const selectedFile = ref(null)
    const sessionId = ref('')
    const localDocxPath = ref('')
    const documentTitle = ref('')
    const sections = ref([])

    // 用普通 reactive 对象模拟 Set，key 为 paragraphIndex，value 为 true/false
    // 默认全部不选中
    const selectedSet = reactive({})
    const sectionExtras = reactive({})

    const selectedCount = computed(
      () => Object.values(selectedSet).filter(Boolean).length
    )
    const isAllSelected = computed(
      () => sections.value.length > 0 && selectedCount.value === sections.value.length
    )
    const isIndeterminate = computed(
      () => selectedCount.value > 0 && selectedCount.value < sections.value.length
    )

    const toggleSelectAll = () => {
      if (isAllSelected.value) {
        sections.value.forEach(sec => { selectedSet[sec.paragraphIndex] = false })
      } else {
        sections.value.forEach(sec => { selectedSet[sec.paragraphIndex] = true })
      }
    }

    const toggleSection = (idx) => {
      selectedSet[idx] = !selectedSet[idx]
    }

    const onFileChange = (file) => { selectedFile.value = file.raw }
    const onExceed = () => { ElMessage.warning('只能上传一个文件，请先移除已选文件') }

    const levelTagType = (level) => {
      const map = { 1: 'danger', 2: 'warning', 3: 'success', 4: 'info' }
      return map[level] || 'info'
    }

    const parseOutline = async () => {
      if (!selectedFile.value) { ElMessage.warning('请先选择 .docx 文件'); return }
      parsing.value = true
      try {
        const formData = new FormData()
        formData.append('file', selectedFile.value)
        const res = await axios.post(`${API_BASE}/parse`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        if (!res.data.success) throw new Error(res.data.detail || '解析失败')

        sessionId.value = res.data.session_id
        documentTitle.value = res.data.document_title
        sections.value = res.data.sections
        localDocxPath.value = res.data.local_docx_path || ''

        // 初始化：全部不选中，补充说明为空
        sections.value.forEach(sec => {
          selectedSet[sec.paragraphIndex] = false
          sectionExtras[sec.paragraphIndex] = ''
        })

        currentStep.value = 'fill'
        ElMessage.success(`解析完成，共识别 ${sections.value.length} 个章节，请勾选需要编写的章节`)
      } catch (err) {
        ElMessage.error(`解析失败：${err.response?.data?.detail || err.message}`)
      } finally {
        parsing.value = false
      }
    }

    const generateOutline = async () => {
      if (selectedCount.value === 0) { ElMessage.warning('请至少勾选一个章节'); return }
      generating.value = true
      generatedCount.value = 0
      try {
        // 只传选中章节的补充说明
        const extrasPayload = {}
        Object.keys(selectedSet).forEach(k => {
          if (selectedSet[k]) extrasPayload[String(k)] = sectionExtras[k] || ''
        })

        const res = await axios.post(
          `${API_BASE}/generate`,
          { session_id: sessionId.value, local_docx_path: localDocxPath.value, section_extras: extrasPayload },
          {
            responseType: 'blob',
            timeout: 600000,
            onDownloadProgress: () => {
              generatedCount.value = Math.min(generatedCount.value + 1, selectedCount.value)
            },
          }
        )

        const blob = new Blob([res.data], {
          type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        })
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `outline_rewritten_${Date.now()}.docx`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        URL.revokeObjectURL(url)

        currentStep.value = 'done'
        ElMessage.success('生成完成，文档已下载')
      } catch (err) {
        ElMessage.error(`生成失败：${err.response?.data?.detail || err.message}`)
      } finally {
        generating.value = false
      }
    }

    const resetToUpload = () => {
      currentStep.value = 'upload'
      selectedFile.value = null
      sessionId.value = ''
      localDocxPath.value = ''
      documentTitle.value = ''
      sections.value = []
      generatedCount.value = 0
      Object.keys(selectedSet).forEach(k => delete selectedSet[k])
      Object.keys(sectionExtras).forEach(k => delete sectionExtras[k])
    }

    return {
      currentStep, parsing, generating, generatedCount,
      selectedFile, documentTitle, sections, sectionExtras,
      selectedSet, selectedCount, isAllSelected, isIndeterminate,
      toggleSelectAll, toggleSection,
      onFileChange, onExceed, levelTagType,
      parseOutline, generateOutline, resetToUpload,
    }
  },
}
</script>

<style scoped>
.outline-rewriter-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  padding: 20px;
  display: flex;
  justify-content: center;
  align-items: flex-start;
}

.main-container {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  padding: 32px;
  width: 100%;
  max-width: 900px;
}

.header { text-align: center; margin-bottom: 32px; }
.header h2 { color: #2c3e50; font-size: 26px; margin-bottom: 8px; }
.header p { color: #7f8c8d; font-size: 15px; }

.upload-area { margin-bottom: 24px; }
.docx-uploader { width: 100%; }
:deep(.el-upload-dragger) { width: 100%; border-radius: 10px; }
.upload-actions { text-align: center; }

.doc-info { margin-bottom: 14px; }

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 14px;
  background: #f4f6f8;
  border-radius: 8px;
  margin-bottom: 14px;
  font-weight: 600;
}

.toolbar-tip {
  color: #909399;
  font-size: 13px;
  font-weight: 400;
}

/* 章节列表 */
.sections-list {
  max-height: 540px;
  overflow-y: auto;
  padding-right: 4px;
  margin-bottom: 24px;
}

.section-item {
  padding: 12px 14px;
  margin-bottom: 8px;
  border-radius: 8px;
  border-left: 4px solid #e0e0e0;
  background: #fafafa;
  cursor: pointer;
  transition: box-shadow 0.15s, background 0.15s, border-left-color 0.15s;
  user-select: none;
}

.section-item:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }

.section-item.is-selected {
  background: #ecf5ff;
  border-left-color: #409eff !important;
  box-shadow: 0 2px 10px rgba(64,158,255,0.14);
}

.section-item.level-1:not(.is-selected) { border-left-color: #f56c6c; background: #fff5f5; }
.section-item.level-2:not(.is-selected) { border-left-color: #e6a23c; background: #fffbf0; }
.section-item.level-3:not(.is-selected) { border-left-color: #67c23a; background: #f5fff0; }
.section-item.level-4:not(.is-selected) { border-left-color: #909399; background: #f8f8f8; }

.section-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-checkbox { flex-shrink: 0; }
.level-tag { flex-shrink: 0; }

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #2c3e50;
  line-height: 1.4;
}

.number-text { color: #909399; margin-right: 4px; }

/* 补充说明区域（仅选中时出现） */
.extra-area {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed #c6e2ff;
}

.section-extra-input { width: 100%; }

/* 底部操作 */
.fill-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-bottom: 16px;
}

.progress-area { margin-top: 16px; }
.progress-tip {
  text-align: center;
  color: #909399;
  font-size: 13px;
  margin-top: 8px;
}

.result-section { padding: 40px 0; }

.sections-list::-webkit-scrollbar { width: 6px; }
.sections-list::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 3px; }

:deep(.el-button) { border-radius: 8px; }
:deep(.el-textarea__inner) { border-radius: 6px; font-size: 13px; }
</style>
