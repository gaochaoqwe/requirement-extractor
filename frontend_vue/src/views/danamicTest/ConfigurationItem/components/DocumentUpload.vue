<template>
  <div class="document-upload">
    <el-form :model="uploadInfo" :rules="uploadRules" ref="uploadForm" label-width="120px">
      <el-form-item label="需求文档" prop="requirementFile">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handleRequirementFileChange"
          :file-list="requirementFileList"
          accept=".docx,.doc,.pdf"
          :limit="1">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将需求文档拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .docx/.doc/.pdf 格式，文件大小不超过 50MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item label="是否有策划表">
        <el-switch v-model="uploadInfo.hasPlanning" active-text="是" inactive-text="否"></el-switch>
      </el-form-item>

      <el-form-item v-if="uploadInfo.hasPlanning" label="策划表文档" prop="planningFile">
        <el-upload
          class="upload-demo"
          drag
          :auto-upload="false"
          :on-change="handlePlanningFileChange"
          :file-list="planningFileList"
          accept=".xlsx,.xls"
          :limit="1">
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            将策划表拖拽到此处，或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .xlsx/.xls 格式，文件大小不超过 20MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <div class="upload-summary" v-if="requirementFileList.length > 0">
        <h4>已上传文件</h4>
        <el-table :data="uploadedFiles" style="width: 100%">
          <el-table-column prop="name" label="文件名" width="300"></el-table-column>
          <el-table-column prop="size" label="文件大小" width="120"></el-table-column>
          <el-table-column prop="type" label="文件类型" width="120"></el-table-column>
          <el-table-column label="操作">
            <template #default="scope">
              <el-button size="small" type="danger" @click="removeFile(scope.row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-form>
  </div>
</template>

<script>
import { UploadFilled } from '@element-plus/icons-vue'

export default {
  name: 'DocumentUpload',
  components: {
    UploadFilled
  },
  props: {
    modelValue: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['update:modelValue', 'validate'],
  data() {
    return {
      uploadInfo: {
        requirementFile: null,
        planningFile: null,
        hasPlanning: false
      },
      requirementFileList: [],
      planningFileList: [],
      uploadRules: {
        requirementFile: [
          { required: true, message: '请上传需求文档', trigger: 'change' }
        ]
      }
    }
  },
  computed: {
    uploadedFiles() {
      const files = [];
      if (this.requirementFileList.length > 0) {
        files.push({
          name: this.requirementFileList[0].name,
          size: this.formatFileSize(this.requirementFileList[0].size),
          type: '需求文档'
        });
      }
      if (this.planningFileList.length > 0) {
        files.push({
          name: this.planningFileList[0].name,
          size: this.formatFileSize(this.planningFileList[0].size),
          type: '策划表'
        });
      }
      return files;
    }
  },
  watch: {
    modelValue: {
      handler(newVal) {
        this.uploadInfo = { ...this.uploadInfo, ...newVal };
      },
      deep: true,
      immediate: true
    },
    uploadInfo: {
      handler(newVal) {
        this.$emit('update:modelValue', newVal);
      },
      deep: true
    }
  },
  methods: {
    handleRequirementFileChange(file, fileList) {
      if (file.size > 50 * 1024 * 1024) {
        this.$message.error('文件大小不能超过50MB');
        return;
      }
      
      this.requirementFileList = fileList;
      this.uploadInfo.requirementFile = file.raw;
      this.validateField('requirementFile');
    },
    
    handlePlanningFileChange(file, fileList) {
      if (file.size > 20 * 1024 * 1024) {
        this.$message.error('文件大小不能超过20MB');
        return;
      }
      
      this.planningFileList = fileList;
      this.uploadInfo.planningFile = file.raw;
    },
    
    removeFile(file) {
      if (file.type === '需求文档') {
        this.requirementFileList = [];
        this.uploadInfo.requirementFile = null;
      } else if (file.type === '策划表') {
        this.planningFileList = [];
        this.uploadInfo.planningFile = null;
      }
    },
    
    formatFileSize(bytes) {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    validateField(field) {
      this.$refs.uploadForm.validateField(field);
    },
    
    validate() {
      return this.$refs.uploadForm.validate();
    },
    
    resetForm() {
      this.$refs.uploadForm.resetFields();
      this.requirementFileList = [];
      this.planningFileList = [];
    }
  }
}
</script>

<style scoped>
.document-upload {
  padding: 20px;
}

.upload-demo {
  width: 100%;
}

.upload-summary {
  margin-top: 30px;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.upload-summary h4 {
  margin-top: 0;
  color: #409eff;
}

.el-upload__text {
  color: #606266;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
}
</style> 