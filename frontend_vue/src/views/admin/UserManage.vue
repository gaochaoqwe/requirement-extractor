<template>
  <div class="admin-user-manage">
    <div class="main-content">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-left">
          <h1>
            <el-icon><UserFilled /></el-icon>
            人员管理
          </h1>
          <el-tag type="danger" size="large">管理员模式</el-tag>
        </div>
        <div class="header-right">
          <el-button @click="goBack" icon="Back">返回任务中心</el-button>
          <el-button @click="goHome" icon="HomeFilled">返回首页</el-button>
          <el-button type="primary" icon="Plus" @click="openCreateDialog">新建账号</el-button>
          <el-button @click="refreshUsers" icon="Refresh" :loading="loading">刷新</el-button>
        </div>
      </div>

      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card total">
          <div class="stat-icon">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ users.length }}</div>
            <div class="stat-label">总账号数</div>
          </div>
        </el-card>
        <el-card class="stat-card active">
          <div class="stat-icon">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ activeCount }}</div>
            <div class="stat-label">启用中</div>
          </div>
        </el-card>
        <el-card class="stat-card disabled">
          <div class="stat-icon">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ users.length - activeCount }}</div>
            <div class="stat-label">已停用</div>
          </div>
        </el-card>
      </div>

      <!-- 筛选栏 -->
      <el-card class="filter-card">
        <div class="filter-row">
          <div class="filter-left">
            <el-icon><InfoFilled /></el-icon>
            <span>共 {{ filteredUsers.length }} 个账号</span>
          </div>
          <div class="filter-right">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索用户名或显示名"
              clearable
              style="width: 300px;"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </div>
        </div>
      </el-card>

      <!-- 用户列表 -->
      <el-card class="user-list-card">
        <div v-if="loading" class="loading-container">
          <el-icon class="is-loading" :size="50"><Loading /></el-icon>
          <p>加载账号列表中...</p>
        </div>

        <el-empty v-else-if="filteredUsers.length === 0" description="暂无账号" />

        <el-table v-else :data="filteredUsers" stripe style="width: 100%;">
          <el-table-column prop="id" label="ID" width="80" align="center" />
          <el-table-column prop="username" label="用户名" min-width="150">
            <template #default="{ row }">
              <span class="username-cell">{{ row.username }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="display_name" label="显示名" min-width="150" />
          <el-table-column label="状态" width="110" align="center">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
                {{ row.is_active ? '启用' : '停用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="180">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="最后登录" min-width="180">
            <template #default="{ row }">
              {{ row.last_login ? formatTime(row.last_login) : '从未登录' }}
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 新建账号对话框 -->
    <el-dialog
      v-model="createDialogVisible"
      title="新建账号"
      width="480px"
      :close-on-click-modal="false"
      @closed="resetForm"
    >
      <el-form
        ref="createFormRef"
        :model="createForm"
        :rules="createRules"
        label-width="90px"
        class="create-form"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="createForm.username"
            placeholder="建议使用姓名全拼，如 zhangsan"
            clearable
          />
        </el-form-item>
        <el-form-item label="显示名" prop="display_name">
          <el-input
            v-model="createForm.display_name"
            placeholder="例如：张三"
            clearable
          />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="不少于6位，默认 123456"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirm_password">
          <el-input
            v-model="createForm.confirm_password"
            type="password"
            placeholder="请再次输入密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">
          确定创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import {
  User, UserFilled, Search, Loading, Back, Refresh, Plus, HomeFilled,
  InfoFilled, CircleCheck, CircleClose
} from '@element-plus/icons-vue';
import request from '@/api/request';

const router = useRouter();

// 用户列表相关
const users = ref([]);
const loading = ref(false);
const searchKeyword = ref('');

// 新建对话框相关
const createDialogVisible = ref(false);
const creating = ref(false);
const createFormRef = ref(null);

const createForm = reactive({
  username: '',
  display_name: '',
  password: '123456',
  confirm_password: '123456'
});

const validateConfirm = (rule, value, callback) => {
  if (value !== createForm.password) {
    callback(new Error('两次输入的密码不一致'));
  } else {
    callback();
  }
};

const createRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 2, max: 50, message: '用户名长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  display_name: [
    { required: true, message: '请输入显示名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
};

const activeCount = computed(() => users.value.filter(u => u.is_active).length);

const filteredUsers = computed(() => {
  const keyword = searchKeyword.value.trim().toLowerCase();
  if (!keyword) return users.value;
  return users.value.filter(u =>
    String(u.username || '').toLowerCase().includes(keyword) ||
    String(u.display_name || '').toLowerCase().includes(keyword)
  );
});

// 加载用户列表
async function refreshUsers() {
  loading.value = true;
  try {
    const res = await request.get('/auth/users');
    if (res && res.success) {
      users.value = res.data || [];
      console.log(`加载了 ${users.value.length} 个账号`);
    } else {
      ElMessage.error(res?.message || '获取账号列表失败');
    }
  } catch (error) {
    console.error('获取账号列表失败:', error);
    ElMessage.error(error.message || '获取账号列表失败');
  } finally {
    loading.value = false;
  }
}

// 打开新建对话框
function openCreateDialog() {
  createDialogVisible.value = true;
}

// 重置表单
function resetForm() {
  if (createFormRef.value) {
    createFormRef.value.clearValidate();
  }
  createForm.username = '';
  createForm.display_name = '';
  createForm.password = '123456';
  createForm.confirm_password = '123456';
}

// 创建账号
async function handleCreate() {
  if (!createFormRef.value) return;

  await createFormRef.value.validate(async (valid) => {
    if (!valid) return;

    creating.value = true;
    try {
      const res = await request.post('/auth/register', {
        username: createForm.username.trim(),
        password: createForm.password,
        display_name: createForm.display_name.trim()
      });

      if (res && res.success) {
        ElMessage.success('账号创建成功');
        createDialogVisible.value = false;
        await refreshUsers();
      } else {
        ElMessage.error(res?.message || '账号创建失败');
      }
    } catch (error) {
      console.error('创建账号失败:', error);
      ElMessage.error(error.message || '账号创建失败');
    } finally {
      creating.value = false;
    }
  });
}

// 格式化时间
function formatTime(timeStr) {
  if (!timeStr) return '-';
  const date = new Date(timeStr);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 返回任务中心
function goBack() {
  router.push('/admin-task-manager');
}

// 返回首页
function goHome() {
  router.push('/');
}

onMounted(() => {
  console.log('管理员人员管理页面加载');
  refreshUsers();
});
</script>

<style scoped>
.admin-user-manage {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
}

/* 页面标题 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-left h1 {
  font-size: 28px;
  color: #303133;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.stat-card {
  border-radius: 12px;
  overflow: hidden;
}

.stat-card :deep(.el-card__body) {
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.stat-card.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.stat-card.active {
  background: linear-gradient(135deg, #42e695 0%, #3bb2b8 100%);
  color: white;
}

.stat-card.disabled {
  background: linear-gradient(135deg, #bdc3c7 0%, #8e9eab 100%);
  color: white;
}

.stat-icon {
  font-size: 48px;
  opacity: 0.9;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

/* 筛选卡片 */
.filter-card {
  margin-bottom: 24px;
  border-radius: 12px;
}

.filter-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.filter-left {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #606266;
  font-size: 14px;
}

/* 列表卡片 */
.user-list-card {
  border-radius: 12px;
  min-height: 400px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  color: #909399;
}

.username-cell {
  font-weight: 600;
  color: #303133;
}

/* 响应式 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
