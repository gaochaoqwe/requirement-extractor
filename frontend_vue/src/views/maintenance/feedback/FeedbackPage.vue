<template>
  <div class="feedback-page">
    <div class="page-shell">
      <div class="page-title">用户反馈</div>
      <div class="page-subtitle">提交问题 / 建议，管理员会在这里统一回复</div>

      <el-row :gutter="16">
        <el-col :xs="24" :lg="16">
          <el-card class="card glass" shadow="never">
            <template #header>
              <div class="card-header">
                <div class="title">提交反馈</div>
              </div>
            </template>

            <el-form :model="form" label-width="80px" class="form">
              <el-row :gutter="16">
                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="类型">
                    <el-select v-model="form.type" placeholder="请选择" style="width: 100%;">
                      <el-option label="Bug" value="bug" />
                      <el-option label="功能建议" value="feature" />
                      <el-option label="使用咨询" value="question" />
                      <el-option label="其他" value="other" />
                    </el-select>
                  </el-form-item>
                </el-col>

                <el-col :xs="24" :sm="12" :md="8">
                  <el-form-item label="模块">
                    <el-select v-model="form.module" placeholder="请选择" filterable style="width: 100%;">
                      <el-option
                        v-for="opt in moduleOptions"
                        :key="opt"
                        :label="opt"
                        :value="opt"
                      />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-form-item label="内容">
                <el-input v-model="form.content" type="textarea" :rows="6" placeholder="一句话说清问题/建议即可（可选：带上复现步骤或截图）" />
              </el-form-item>

              <el-form-item>
                <el-button type="primary" :loading="submitting" @click="submitFeedback">提交反馈</el-button>
                <el-button :disabled="submitting" @click="resetForm">清空</el-button>
              </el-form-item>
            </el-form>
          </el-card>

          <el-card class="card glass" shadow="never" style="margin-top: 16px;">
            <template #header>
              <div class="card-header">
                <div class="title">反馈列表</div>
                <div class="actions">
                  <el-button size="small" :loading="loadingList" @click="refresh">刷新列表</el-button>
                </div>
              </div>
            </template>

            <el-tabs v-model="activeTab" @tab-change="refresh">
              <el-tab-pane label="我提交过的反馈" name="mine" />
              <el-tab-pane v-if="isAdmin" label="全部反馈" name="all" />
            </el-tabs>

            <el-table :data="items" style="width: 100%;" v-loading="loadingList" class="table">
              <el-table-column prop="id" label="#" width="80" />
              <el-table-column label="提出人" width="140">
                <template #default="scope">
                  <span>{{ scope.row.submitter_display_name || scope.row.submitter_username || '-' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="module" label="模块" width="200" />
              <el-table-column prop="type" label="类型" width="120" />
              <el-table-column prop="status" label="状态" width="120" />
              <el-table-column prop="content" label="内容" min-width="260" />
              <el-table-column prop="admin_reply" label="管理员回复" min-width="220" />
              <el-table-column prop="created_at" label="时间" width="180" />
              <el-table-column v-if="isAdmin" label="操作" width="120" fixed="right">
                <template #default="scope">
                  <el-button size="small" @click="openReply(scope.row)">回复</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-card>
        </el-col>

        <el-col :xs="24" :lg="8">
          <el-card class="card glass side" shadow="never">
            <template #header>
              <div class="card-header">
                <div class="title">看板</div>
              </div>
            </template>

            <div class="stats">
              <div class="stat">
                <div class="stat-num">{{ stats.total }}</div>
                <div class="stat-label">当前列表数量</div>
              </div>
              <div class="stat">
                <div class="stat-num">{{ stats.replied }}</div>
                <div class="stat-label">已回复</div>
              </div>
              <div class="stat">
                <div class="stat-num">{{ stats.open }}</div>
                <div class="stat-label">未回复</div>
              </div>
            </div>

            <div class="tips">
              <div class="tip-title">小提示</div>
              <div class="tip-brief">简单描述就行，能复现最好；不想写太多也没关系。</div>
              <el-collapse class="tip-collapse" accordion>
                <el-collapse-item name="1" title="可选：如何让我们更快定位？">
                  <div class="tip-item">页面/功能点 + 复现步骤（可选）</div>
                  <div class="tip-item">期望结果 vs 实际结果（可选）</div>
                  <div class="tip-item">截图/报错信息（可选）</div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-dialog v-model="replyDialogVisible" title="回复反馈" width="560px">
        <el-input v-model="replyText" type="textarea" :rows="6" placeholder="请输入回复内容" />
        <template #footer>
          <el-button @click="replyDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="replying" @click="submitReply">提交回复</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { createFeedback, listAllFeedback, listMyFeedback, replyFeedback } from '@/api/maintenance'
import { useAuthStore } from '@/stores/auth'

const form = reactive({
  type: 'bug',
  module: '',
  content: ''
})

const submitting = ref(false)
const loadingList = ref(false)
const items = ref([])

const authStore = useAuthStore()
const isAdmin = ref(false)
const activeTab = ref('mine')

const moduleOptions = [
  '文档审查-配置项测试',
  '文档审查-回归测试',
  '代码审查-配置项测试',
  '代码审查-新回归测试',
  '代码审查-回归测试',
  '动态测试-配置项测试',
  '动态测试-回归测试',
  '静态分析',
  '测试工具',
  '资产管理-动态资产',
  '资产管理-静态资产',
  '资产管理-光电知识系统'
]

const replyDialogVisible = ref(false)
const replying = ref(false)
const replyText = ref('')
const replyingFeedbackId = ref(null)

const stats = computed(() => {
  const list = Array.isArray(items.value) ? items.value : []
  const total = list.length
  const replied = list.filter((x) => String(x?.status || '').toLowerCase() === 'replied' || !!x?.admin_reply).length
  const open = total - replied
  return { total, replied, open }
})

function resetForm() {
  form.type = 'bug'
  form.module = ''
  form.content = ''
}

async function submitFeedback() {
  if (!form.content || !String(form.content).trim()) {
    ElMessage.warning('请输入反馈内容')
    return
  }

  if (!form.module || !String(form.module).trim()) {
    ElMessage.warning('请选择模块')
    return
  }

  submitting.value = true
  try {
    const page_url = window.location?.href || ''
    await createFeedback({
      type: form.type,
      module: form.module,
      content: form.content,
      page_url
    })
    ElMessage.success('提交成功')
    resetForm()
    await refresh()
  } catch (e) {
    ElMessage.error(e?.message || '提交失败')
  } finally {
    submitting.value = false
  }
}

function formatRow(it) {
  return {
    ...it,
    created_at: it.created_at ? new Date(it.created_at).toLocaleString() : '',
    replied_at: it.replied_at ? new Date(it.replied_at).toLocaleString() : ''
  }
}

async function loadMyFeedback() {
  loadingList.value = true
  try {
    const res = await listMyFeedback({ limit: 50, offset: 0 })
    items.value = (res?.data || []).map(formatRow)
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loadingList.value = false
  }
}

async function loadAllFeedback() {
  loadingList.value = true
  try {
    const res = await listAllFeedback({ limit: 200, offset: 0 })
    items.value = (res?.data || []).map(formatRow)
  } catch (e) {
    ElMessage.error(e?.message || '加载失败')
  } finally {
    loadingList.value = false
  }
}

async function refresh() {
  if (activeTab.value === 'all' && isAdmin.value) {
    await loadAllFeedback()
  } else {
    await loadMyFeedback()
  }
}

function openReply(row) {
  replyingFeedbackId.value = row?.id
  replyText.value = row?.admin_reply || ''
  replyDialogVisible.value = true
}

async function submitReply() {
  if (!replyingFeedbackId.value) return
  if (!replyText.value || !String(replyText.value).trim()) {
    ElMessage.warning('请输入回复内容')
    return
  }

  replying.value = true
  try {
    await replyFeedback(replyingFeedbackId.value, replyText.value)
    ElMessage.success('回复成功')
    replyDialogVisible.value = false
    await refresh()
  } catch (e) {
    ElMessage.error(e?.message || '回复失败')
  } finally {
    replying.value = false
  }
}

onMounted(() => {
  isAdmin.value = String(authStore.user?.username || '') === 'gaochao'
  refresh()
})
</script>

<style scoped>
.feedback-page {
  width: 100%;
  min-height: calc(100vh - 56px);
  padding: 18px 18px 26px;
  background:
    radial-gradient(1100px 460px at 16% 0%, rgba(99, 102, 241, 0.22), rgba(0, 0, 0, 0)),
    radial-gradient(900px 420px at 90% 20%, rgba(34, 211, 238, 0.18), rgba(0, 0, 0, 0)),
    linear-gradient(180deg, rgba(15, 23, 42, 0.02), rgba(15, 23, 42, 0.01));
}

.page-shell {
  width: 100%;
  max-width: 1440px;
  margin: 0 auto;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 13px;
  opacity: 0.75;
  margin-bottom: 14px;
}

.card {
  border-radius: 8px;
  border: 1px solid rgba(15, 23, 42, 0.08);
}

.glass {
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.title {
  font-size: 16px;
  font-weight: 600;
}

.form {
  width: 100%;
}

.side {
  position: sticky;
  top: 16px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}

.stat {
  border-radius: 10px;
  padding: 12px 10px;
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.10), rgba(34, 211, 238, 0.06));
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.stat-num {
  font-size: 18px;
  font-weight: 700;
  line-height: 20px;
}

.stat-label {
  margin-top: 4px;
  font-size: 12px;
  opacity: 0.8;
}

.tips {
  border-top: 1px dashed rgba(15, 23, 42, 0.12);
  padding-top: 12px;
}

.tip-title {
  font-weight: 600;
  margin-bottom: 8px;
}

.tip-brief {
  font-size: 12px;
  opacity: 0.85;
  line-height: 18px;
  margin-bottom: 8px;
}

.tip-collapse {
  --el-collapse-border-color: rgba(15, 23, 42, 0.10);
}

.tip-item {
  font-size: 12px;
  opacity: 0.85;
  line-height: 20px;
}
</style>
