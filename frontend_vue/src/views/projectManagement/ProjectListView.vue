<template>
  <div class="project-list-view">
    <div class="header-row">
      <h1>项目管理</h1>
      <div class="actions">
        <button @click="goToCreateProject" class="btn btn-primary">新建项目</button>
        <button @click="fetchProjects" class="btn btn-refresh">刷新</button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <p>正在加载项目列表...</p>
    </div>
    <div v-else-if="error" class="error-message">
      <p>加载失败: {{ error.message || error }}</p>
    </div>
    <div v-else class="project-list-table-wrapper">
      <table class="project-table">
        <thead>
          <tr>
            <th>项目名称</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody v-if="hasValidProjects">
          <tr v-for="project in validProjects" :key="project.id" class="project-item" @click="goToProjectDetails(project.id)">
            <td>{{ project.name }}</td>
            <td>{{ formatDate(project.created_at) }}</td>
            <td>
              <button @click.stop="goToProjectDetails(project.id)" class="btn btn-sm btn-info">查看</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
// 项目管理 API 路径已统一为 /api/projects

export default {
  name: 'ProjectListView',
  data() {
    return {
      projects: [],
      loading: false,
      error: null,
    };
  },
  computed: {
    validProjects() {
      // 过滤掉无效的项目（例如名称为空等）
      return this.projects.filter(project => 
        project && project.id && project.name && project.name.trim() !== ''
      );
    },
    hasValidProjects() {
      return this.validProjects.length > 0;
    }
  },
  methods: {
    async fetchProjects() {
      this.loading = true;
      this.error = null;
      try {
        // 强制每次都从后端请求最新数据
        const response = await axios.get(`/api/projects/`, { params: { t: Date.now() } });
        this.projects = response.data;
      } catch (err) {
        this.error = err.response ? err.response.data : err;
      }
      this.loading = false;
    },
    goToCreateProject() {
      this.$router.push({ name: 'ProjectCreate' });
    },
    goToProjectDetails(projectId) {
      this.$router.push({ name: 'ProjectDetail', params: { id: projectId } });
    },
    formatDate(dateString) {
      if (!dateString) return '-';
      const options = { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' };
      return new Date(dateString).toLocaleString(undefined, options);
    },
    getStatusClass(status) {
      if (status === 'active') return 'badge-success';
      if (status === 'inactive') return 'badge-secondary';
      if (status === 'completed') return 'badge-primary';
      return 'badge-light';
    },
    statusText(status) {
      if (status === 'active') return '进行中';
      if (status === 'inactive') return '未启动';
      if (status === 'completed') return '已完成';
      return status || '-';
    }
  },
  mounted() {
    this.fetchProjects();
  }
};
</script>

<style scoped>
.project-list-view {
  padding: 32px 36px 0 36px;
  background: #f6f8fa;
  min-height: 100vh;
}

.header-row {
  display: flex;
  align-items: center;
  margin-bottom: 18px;
}
.header-row h1 {
  font-size: 2rem;
  font-weight: bold;
  margin: 0 24px 0 0;
  flex-shrink: 0;
}
.actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-block;
  font-weight: 500;
  color: #fff;
  background-color: #409eff;
  border: none;
  padding: 8px 22px;
  font-size: 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.2s;
  outline: none;
}
.btn-primary {
  background-color: #409eff;
}
.btn-primary:hover {
  background-color: #337ecc;
}
.btn-refresh {
  background-color: #67c23a;
}
.btn-refresh:hover {
  background-color: #529b2e;
}
.btn-info {
  background-color: #36cfc9;
}
.btn-info:hover {
  background-color: #13a39f;
}
.btn-sm {
  padding: 5px 14px;
  font-size: 0.95rem;
}

.loading,
.error-message,
.no-projects {
  margin-top: 24px;
  text-align: center;
  color: #888;
}
.error-message {
  color: #e74c3c;
}

.project-list-table-wrapper {
  margin-top: 12px;
  width: 100%;
  overflow-x: auto;
}
.project-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  font-size: 1rem;
}
.project-table thead th {
  font-weight: bold;
  background: #f0f4f8;
  border-bottom: 2px solid #e0e6ed;
  padding: 14px 10px;
  text-align: left;
}
.project-table tbody tr {
  transition: background 0.2s;
}
.project-table tbody tr:nth-child(even) {
  background: #f7fafc;
}
.project-table tbody tr:hover {
  background: #e6f7ff;
}
.project-table td {
  padding: 12px 10px;
  border-bottom: 1px solid #f0f4f8;
  vertical-align: middle;
}
.project-table .desc-cell {
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.badge {
  display: inline-block;
  font-size: 0.95em;
  padding: 0.3em 0.8em;
  border-radius: 12px;
  font-weight: 500;
}
.badge-success {
  background-color: #67c23a;
  color: #fff;
}
.badge-secondary {
  background-color: #909399;
  color: #fff;
}
.badge-primary {
  background-color: #409eff;
  color: #fff;
}
.badge-light {
  background-color: #f4f4f5;
  color: #606266;
}
</style>
