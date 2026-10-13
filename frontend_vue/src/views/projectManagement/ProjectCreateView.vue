<template>
  <div class="project-create-view">
    <div class="header-row">
      <h1>新建项目</h1>
    </div>
    <form @submit.prevent="submitCreateProject" class="project-form">
      <div class="form-group">
        <label for="projectName">项目名称</label>
        <input type="text" id="projectName" v-model="project.name" class="form-control" required maxlength="100" placeholder="请输入项目名称">
      </div>

      <div v-if="error" class="error-message">
        <p>创建失败: {{ error.message || error }}</p>
      </div>
      
      <div v-if="successMessage" class="success-message">
        <p>{{ successMessage }}</p>
      </div>

      <div class="form-actions">
        <button type="submit" class="btn btn-primary" :disabled="submitting">
          {{ submitting ? '创建中...' : '创建项目' }}
        </button>
        <button type="button" @click="goBack" class="btn btn-secondary" :disabled="submitting">
          取消
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import axios from 'axios';

// 项目管理 API 路径已统一为 /api/projects

export default {
  name: 'ProjectCreateView',
  data() {
    return {
      project: {
        name: '',
      },
      submitting: false,
      error: null,
      successMessage: ''
    };
  },
  methods: {
    async submitCreateProject() {
      this.submitting = true;
      this.error = null;
      this.successMessage = '';
      try {
        const response = await axios.post(`/api/projects/`, this.project);
        this.successMessage = `Project '${response.data.name}' created successfully! ID: ${response.data.id}`;
        // Optionally, reset form or redirect
        // this.resetForm();
        // this.$router.push({ name: 'ProjectDetail', params: { id: response.data.id } });
        setTimeout(() => {
            this.$router.push({ name: 'ProjectList' }); // Or to the detail page
        }, 1500); // Delay for user to see success message
      } catch (err) {
        console.error('Failed to create project:', err);
        this.error = err.response ? err.response.data : err;
        if (err.response && err.response.data && err.response.data.detail) {
            this.error = { message: err.response.data.detail };
        }
      }
      this.submitting = false;
    },
    resetForm() {
      this.project = {
        name: '',
      };
    },
    goBack() {
      this.$router.push({ name: 'ProjectList' }); // Or use this.$router.go(-1)
    }
  }
};
</script>

<style scoped>
.project-create-view {
  padding: 32px 36px 0 36px;
  background: #f6f8fa;
  min-height: 100vh;
}

.header-row {
  display: flex;
  align-items: center;
  margin-bottom: 22px;
}

.header-row h1 {
  font-size: 2rem;
  font-weight: bold;
  margin: 0;
}

.project-form {
  max-width: 680px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 24px 28px;
}

.project-form .form-group {
  margin-bottom: 20px;
}

.project-form label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  font-size: 0.95rem;
  color: #333;
}

.project-form .form-control {
  width: 100%;
  padding: 10px 12px;
  font-size: 1rem;
  line-height: 1.5;
  border: 1px solid #e0e6ed;
  border-radius: 4px;
  box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.project-form .form-control:focus {
  border-color: #409eff;
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.1);
  outline: none;
}

.project-form textarea.form-control {
  resize: vertical;
  min-height: 100px;
}

.project-form select.form-control {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='%23333'%3E%3Cpath d='M7 10l5 5 5-5z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  background-size: 20px;
  padding-right: 30px;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 28px;
}

.form-actions button {
  min-width: 100px;
}

.error-message {
  color: #e74c3c;
  background-color: #fdecea;
  border-left: 4px solid #e74c3c;
  padding: 12px 16px;
  margin: 16px 0;
  border-radius: 4px;
}

.success-message {
  color: #27ae60;
  background-color: #eafaf1;
  border-left: 4px solid #2ecc71;
  padding: 12px 16px;
  margin: 16px 0;
  border-radius: 4px;
}

.btn {
  display: inline-block;
  font-weight: 500;
  color: #fff;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  user-select: none;
  border: none;
  padding: 8px 22px;
  font-size: 1rem;
  border-radius: 4px;
  transition: background 0.2s;
  outline: none;
}

.btn-primary {
  background-color: #409eff;
}

.btn-primary:hover {
  background-color: #337ecc;
}

.btn-primary:disabled {
  background-color: #a0cfff;
  cursor: not-allowed;
}

.btn-secondary {
  background-color: #909399;
}

.btn-secondary:hover {
  background-color: #666;
}

.btn-secondary:disabled {
  background-color: #c8c9cc;
  cursor: not-allowed;
}
</style>
